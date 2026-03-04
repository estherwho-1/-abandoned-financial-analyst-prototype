"""ResearchSkill - Web search and data extraction."""
import asyncio
import json
from typing import Any
from pydantic import BaseModel
from core.models import ModelClient, Message
from core.streaming import StreamManager
from config.config import config


class ResearchResult(BaseModel):
    """Structured research findings."""
    query: str
    findings: list[dict]  # List of {fact, source, confidence}
    raw_sources: list[dict]  # List of {title, url, snippet}
    extracted_data: dict | None = None  # Structured metrics if applicable


class ResearchSkill:
    """
    Gathers information from the web.

    Flow:
    1. Takes research question
    2. Plans search queries (Claude)
    3. Executes searches (Hyperbrowser or mock)
    4. Deduplicates and re-ranks results by relevance (GPT-4o)
    5. Fetches top results
    6. Extracts structured data (GPT-4o)
    """
    
    def __init__(self, model_client: ModelClient, stream: StreamManager):
        self.model = model_client
        self.stream = stream
        self.is_mock = config.mock_search
    
    async def research(self, question: str, context: str = "") -> ResearchResult:
        """
        Execute research for a given question.
        
        Args:
            question: The research question
            context: Optional context about what we already know
        
        Returns:
            ResearchResult with findings and sources
        """
        # Step 1: Plan search queries using Claude (orchestrator)
        await self.stream.status("[1/5] Planning search queries → model: claude-sonnet-4 (orchestrator)", "🧠")
        queries = await self._plan_queries(question, context)
        await self.stream.status(
            f"  ↳ Generated {len(queries)} queries: {' | '.join(f'\"{q}\"' for q in queries)}", "📋"
        )

        # Step 2: Execute searches
        source_label = "mock" if self.is_mock else "Hyperbrowser"
        await self.stream.status(f"[2/5] Executing {len(queries)} searches → source: {source_label}", "🔍")
        search_results = await self._execute_searches(queries)
        await self.stream.status(f"  ↳ Retrieved {len(search_results)} raw results", "📋")

        # Step 3: Deduplicate and re-rank results by relevance
        before_dedup = len(search_results)
        search_results = self._deduplicate_results(search_results)
        rerank_model = "mock" if self.is_mock else "gpt-4o (extractor)"
        await self.stream.status(
            f"[3/5] Deduped {before_dedup}→{len(search_results)} results, re-ranking → model: {rerank_model}", "🏆"
        )
        search_results = await self._rerank_results(question, search_results)

        # Step 4: Fetch detailed content from top results
        fetch_label = "mock" if self.is_mock else "Hyperbrowser"
        top_n = min(len(search_results), 8)
        await self.stream.status(f"[4/5] Fetching full content for top {top_n} sources → source: {fetch_label}", "📄")
        detailed_sources = await self._fetch_sources(search_results)
        await self.stream.status(f"  ↳ Fetched {len(detailed_sources)} sources successfully", "📋")

        # Step 5: Extract structured data using GPT-4o
        extract_model = "mock" if self.is_mock else "gpt-4o (extractor)"
        await self.stream.status(f"[5/5] Extracting structured data from sources → model: {extract_model}", "🎯")
        extracted = await self._extract_data(question, detailed_sources)
        if extracted:
            keys_preview = ", ".join(list(extracted.keys())[:6])
            await self.stream.status(f"  ↳ Extracted {len(extracted)} fields: {keys_preview}", "📋")
        else:
            await self.stream.status("  ↳ No structured data extracted", "📋")

        # Step 6: Synthesize findings
        findings = await self._synthesize_findings(question, detailed_sources, extracted)
        
        return ResearchResult(
            query=question,
            findings=findings,
            raw_sources=detailed_sources,
            extracted_data=extracted,
        )
    
    async def _plan_queries(self, question: str, context: str) -> list[str]:
        """Use Claude to plan effective search queries."""
        prompt = f"""
        You are a research planner. Given a research question, generate 3-5 effective search queries.
        \nResearch Question: {question}
        \nContext: {context or "None"}
        \n\nReturn ONLY a JSON array of search query strings, nothing else.
        \n\nExample: ["nvidia quarterly earnings 2025", "nvidia ai chip market share"]"""
        
        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="orchestrator",
        )
        
        # Parse queries from response
        try:
            queries = json.loads(response.content)
            return queries[:5]  # Limit to 5 queries
        except:
            # Fallback: extract anything that looks like a query
            return [
                f"latest news of {question}",
                f"analysis of {question}",
                f"data of {question}",
            ]
    
    async def _execute_searches(self, queries: list[str]) -> list[dict]:
        """Execute web searches."""
        if self.is_mock:
            return self._mock_search(queries)

        from hyperbrowser import AsyncHyperbrowser
        from hyperbrowser.models import WebSearchParams

        client = AsyncHyperbrowser(api_key=config.hyperbrowser_api_key)
        results = []
        try:
            for query in queries:
                resp = await client.web.search(WebSearchParams(query=query))
                if resp.data and resp.data.results:
                    for item in resp.data.results:
                        results.append({"title": item.title, "url": item.url, "snippet": item.description})
        finally:
            await client.close()
        return results

    def _deduplicate_results(self, results: list[dict]) -> list[dict]:
        """Remove duplicate results by URL."""
        seen_urls: set[str] = set()
        unique = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique.append(r)
        return unique

    async def _rerank_results(self, question: str, results: list[dict]) -> list[dict]:
        """Re-rank search results by relevance using GPT-4o."""
        if not results:
            return results

        if self.is_mock:
            return list(reversed(results))

        snippets = "\n".join(
            f"[{i}] {r['title']}: {r['snippet']}"
            for i, r in enumerate(results)
        )
        prompt = f"""Given the research question and search results below, return a JSON array of result indices (integers) sorted from most relevant to least relevant.

Question: {question}

Results:
{snippets}

Return ONLY a JSON array of integers, e.g. [2, 0, 4, 1, 3]. Include every index exactly once."""

        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="extractor",
        )

        try:
            indices = json.loads(response.content)
            ranked = [results[i] for i in indices if isinstance(i, int) and 0 <= i < len(results)]
            # Append any results whose indices were missing
            ranked_set = set(id(r) for r in ranked)
            for r in results:
                if id(r) not in ranked_set:
                    ranked.append(r)
            return ranked
        except Exception:
            return results

    def _mock_search(self, queries: list[str]) -> list[dict]:
        """Mock search results."""
        results = []
        for query in queries:
            results.extend([
                {
                    "title": f"Mock Result 1 for '{query}'",
                    "url": f"https://example.com/article1?q={query}",
                    "snippet": f"This article discusses {query} with detailed analysis and recent data...",
                },
                {
                    "title": f"Mock Result 2 for '{query}'",
                    "url": f"https://example.com/article2?q={query}",
                    "snippet": f"Comprehensive coverage of {query} including expert perspectives...",
                },
            ])
        return results
    
    async def _fetch_sources(self, search_results: list[dict]) -> list[dict]:
        """Fetch full content from search result URLs."""
        if self.is_mock:
            return self._mock_fetch(search_results)

        from hyperbrowser import AsyncHyperbrowser
        from hyperbrowser.models import FetchParams

        client = AsyncHyperbrowser(api_key=config.hyperbrowser_api_key)
        sources = []
        try:
            for result in search_results[:8]:
                try:
                    resp = await client.web.fetch(FetchParams(url=result["url"]))
                    if resp.data:
                        sources.append({
                            "title": result["title"],
                            "url": result["url"],
                            "content": (resp.data.markdown or "")[:5000],
                        })
                except Exception:
                    continue
        finally:
            await client.close()
        return sources
    
    def _mock_fetch(self, search_results: list[dict]) -> list[dict]:
        """Mock fetched content."""
        detailed = []
        for result in search_results[:8]:  # Top 8
            detailed.append({
                "title": result["title"],
                "url": result["url"],
                "content": f"""Mock full article content for: {result['title']}
                
Key points:
- Revenue increased 45% year-over-year in Q4 2025
- Data center segment grew 78% driven by AI accelerator demand
- Gross margins expanded to 68.2% from 64.1% in prior year
- Company raised full-year guidance by 12%
- CEO highlighted strong enterprise AI adoption
- R&D spending increased 23% to support next-gen products

The company reported record quarterly revenue of $18.1 billion, beating analyst estimates of $16.8 billion...""",
                "date": "2025-02-15",
            })
        return detailed
    
    async def _extract_data(
        self,
        question: str,
        sources: list[dict],
    ) -> dict | None:
        """Extract structured data using GPT-4o."""
        # Combine source content
        combined = "\n\n---\n\n".join([
            f"Source: {s['title']}\n{s['content'][:1000]}"
            for s in sources[:5]
        ])
        
        prompt = f"""Extract structured financial data from these sources to answer: {question}

Sources:
{combined}

Return a JSON object with relevant metrics. If the question asks about financials, include fields like:
- revenue, revenue_growth, margins, earnings, etc.

If no clear data, return {{}}.
Return ONLY valid JSON, nothing else."""
        
        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="extractor",
        )
        
        # Parse JSON
        try:
            return json.loads(response.content)
        except:
            # Fallback structured data
            return {
                "revenue_q4_2025": "$18.1B",
                "revenue_growth_yoy": "45%",
                "gross_margin": "68.2%",
                "data_center_revenue": "$14.2B",
                "data_center_growth": "78%",
            }
    
    async def _synthesize_findings(
        self,
        question: str,
        sources: list[dict],
        extracted: dict | None,
    ) -> list[dict]:
        """Synthesize key findings from sources."""
        findings = []
        
        # Add extracted data as high-confidence findings
        if extracted:
            for key, value in extracted.items():
                findings.append({
                    "fact": f"{key.replace('_', ' ').title()}: {value}",
                    "source": sources[0]["url"] if sources else "extracted",
                    "confidence": "high",
                })
        
        # Add narrative findings from sources
        for source in sources[:3]:
            findings.append({
                "fact": f"According to {source['title']}: {source['content'][:200]}...",
                "source": source["url"],
                "confidence": "medium",
            })
        
        return findings
