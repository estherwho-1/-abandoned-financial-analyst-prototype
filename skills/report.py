"""ReportSkill - Synthesize findings into final briefing."""
from typing import Any
from pydantic import BaseModel
from core.models import ModelClient, Message
from core.streaming import StreamManager


class ReportSection(BaseModel):
    """A section of the report."""
    title: str
    content: str


class FinalReport(BaseModel):
    """The complete investment briefing."""
    executive_summary: str
    sections: list[ReportSection]
    sources: list[dict]


class ReportSkill:
    """
    Synthesizes all research into a final deliverable.
    
    Flow:
    1. Takes: research findings, analysis results, charts, memory context
    2. Streams structured briefing:
       - Executive Summary
       - Key Metrics
       - Competitive Analysis
       - Bull Case / Bear Case
       - Charts (embedded)
       - Sources
    3. Progressively streams each section
    """
    
    def __init__(self, model_client: ModelClient, stream: StreamManager):
        self.model = model_client
        self.stream = stream
    
    async def generate(
        self,
        query: str,
        research_results: Any,
        analysis_results: Any,
        memory_context: list[dict] | None = None,
    ) -> FinalReport:
        """
        Generate final investment briefing.
        
        Args:
            query: The original question
            research_results: Output from ResearchSkill
            analysis_results: Output from QuantAnalysisSkill
            memory_context: Retrieved memories (if any)
        
        Returns:
            FinalReport with all sections
        """
        await self.stream.status("Synthesizing final briefing", "📝")
        
        # Build context for report generation
        context = self._build_context(
            query,
            research_results,
            analysis_results,
            memory_context,
        )
        
        # Generate report using Claude
        report = await self._generate_report(query, context)
        
        # Stream the report sections
        await self._stream_report(report)
        
        # Emit sources
        sources = self._extract_sources(research_results)
        await self.stream.sources(sources)
        
        return report
    
    def _build_context(
        self,
        query: str,
        research_results: Any,
        analysis_results: Any,
        memory_context: list[dict] | None,
    ) -> str:
        """Build combined context for report generation."""
        parts = []
        
        # Research findings
        if research_results:
            parts.append("## Research Findings")
            if hasattr(research_results, 'findings'):
                for finding in research_results.findings[:5]:
                    parts.append(f"- {finding['fact']}")
            
            if hasattr(research_results, 'extracted_data'):
                parts.append("\n## Extracted Data")
                parts.append(str(research_results.extracted_data))
        
        # Analysis results
        if analysis_results:
            parts.append("\n## Quantitative Analysis")
            if hasattr(analysis_results, 'metrics'):
                for key, value in analysis_results.metrics.items():
                    parts.append(f"- {key}: {value}")
        
        # Memory context
        if memory_context:
            parts.append("\n## Past Research Context")
            for mem in memory_context[:2]:
                parts.append(f"- {mem.get('content', '')[:200]}...")
        
        return "\n".join(parts)
    
    async def _generate_report(self, query: str, context: str) -> FinalReport:
        """Generate the full report using Claude."""
        prompt = f"""You are an expert financial analyst. Generate a comprehensive investment briefing.

Question: {query}

Context and Data:
{context}

Generate a structured report with these sections:

1. **Executive Summary** (2-3 sentences)
2. **Key Metrics** (table format)
3. **Analysis** (key insights)
4. **Bull Case** (3-5 points with specific data)
5. **Bear Case** (3-5 points with specific data)

Use markdown formatting. Be specific and data-driven. Cite numbers from the context."""
        
        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="orchestrator",
        )
        
        # Parse sections from response
        sections = self._parse_sections(response.content)
        
        # Extract executive summary (first paragraph)
        exec_summary = response.content.split("\n\n")[0].replace("## Executive Summary", "").strip()
        
        return FinalReport(
            executive_summary=exec_summary,
            sections=sections,
            sources=[],  # Will be added separately
        )
    
    def _parse_sections(self, content: str) -> list[ReportSection]:
        """Parse markdown sections from report content."""
        sections = []
        current_title = ""
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("##"):
                # Save previous section
                if current_title:
                    sections.append(ReportSection(
                        title=current_title,
                        content="\n".join(current_content).strip(),
                    ))
                
                # Start new section
                current_title = line.replace("##", "").strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_title:
            sections.append(ReportSection(
                title=current_title,
                content="\n".join(current_content).strip(),
            ))
        
        return sections
    
    async def _stream_report(self, report: FinalReport):
        """Stream report sections progressively."""
        # Stream executive summary
        await self.stream.chunk(f"\n## Executive Summary\n\n{report.executive_summary}\n")
        
        # Stream each section
        for section in report.sections:
            await self.stream.chunk(f"\n## {section.title}\n\n{section.content}\n")
    
    def _extract_sources(self, research_results: Any) -> list[dict]:
        """Extract source citations from research results."""
        sources = []
        
        if hasattr(research_results, 'raw_sources'):
            for source in research_results.raw_sources[:10]:
                sources.append({
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                    "date": source.get("date", ""),
                })
        
        return sources
