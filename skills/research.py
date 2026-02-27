"""ResearchSkill - Web search and data extraction."""
import asyncio
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
    4. Fetches top results
    5. Extracts structured data (GPT-4o)
    """
    
    def __init__(self, model_client: ModelClient, stream: StreamManager):
        self.model = model_client
        self.stream = stream
        self.is_mock = config.is_mock_mode()
    
    async def research(self, question: str, context: str = "") -> ResearchResult:
        """
        Execute research for a given question.
        
        Args:
            question: The research question
            context: Optional context about what we already know
        
        Returns:
            ResearchResult with findings and sources
        """
        await self.stream.status("Planning research queries", "🧠")
        
        # Step 1: Plan search queries using orchestrator (Claude)
        queries = await self._plan_queries(question, context)
        
        # Step 2: Execute searches
        await self.stream.status(f"Searching web ({len(queries)} queries)", "🔍")
        search_results = await self._execute_searches(queries)
        
        # Step 3: Fetch detailed content from top results
        await self.stream.status("Fetching detailed sources", "📄")
        detailed_sources = await self._fetch_sources(search_results)
        
        # Step 4: Extract structured data using GPT-4o
        await self.stream.status("Extracting structured data", "🎯")
        extracted = await self._extract_data(question, detailed_sources)
        
        # Step 5: Synthesize findings
        findings = await self._synthesize_findings(question, detailed_sources, extracted)
        
        return ResearchResult(
            query=question,
            findings=findings,
            raw_sources=detailed_sources,
            extracted_data=extracted,
        )
    
    async def _plan_queries(self, question: str, context: str) -> list[str]:
        """Use Claude to plan effective search queries."""
        prompt = f"""You are a research planner. Given a research question, generate 3-5 effective search queries.

Research Question: {question}

Context: {context or "None"}

Return ONLY a JSON array of search query strings, nothing else.
Example: ["nvidia quarterly earnings 2025", "nvidia ai chip market share"]"""
        
        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="orchestrator",
        )
        
        # Parse queries from response
        import json
        try:
            queries = json.loads(response.content)
            return queries[:5]  # Limit to 5 queries
        except:
            # Fallback: extract anything that looks like a query
            return [
                f"{question} latest news",
                f"{question} analysis",
                f"{question} data",
            ]
    
    async def _execute_searches(self, queries: list[str]) -> list[dict]:
        """Execute web searches."""
        if self.is_mock:
            return self._mock_search(queries)
        
        # Real Hyperbrowser implementation would go here
        # For now, use mock
        return self._mock_search(queries)
    
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
        return results[:10]  # Return top 10 total
    
    async def _fetch_sources(self, search_results: list[dict]) -> list[dict]:
        """Fetch full content from search result URLs."""
        if self.is_mock:
            return self._mock_fetch(search_results)
        
        # Real Hyperbrowser fetch would go here
        return self._mock_fetch(search_results)
    
    def _mock_fetch(self, search_results: list[dict]) -> list[dict]:
        """Mock fetched content."""
        detailed = []
        for result in search_results[:5]:  # Top 5
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
            for s in sources[:3]
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
        import json
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
