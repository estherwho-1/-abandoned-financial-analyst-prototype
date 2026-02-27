"""SAGE Orchestrator - Coordinates all skills to execute research tasks."""
import asyncio
import time
from typing import Any
from pydantic import BaseModel
from core.models import ModelClient
from core.streaming import StreamManager
from skills.research import ResearchSkill
from skills.quant_analysis import QuantAnalysisSkill
from skills.memory import MemorySkill
from skills.report import ReportSkill


class SAGEResult(BaseModel):
    """Final result from SAGE."""
    query: str
    report: Any
    metadata: dict


class Orchestrator:
    """
    Main orchestrator for SAGE.
    
    Routes tasks across skills:
    1. Memory: Check what we already know
    2. Research: Gather new information
    3. QuantAnalysis: Run calculations and charts
    4. Memory: Store new findings
    5. Report: Synthesize everything
    """
    
    def __init__(self):
        self.stream = StreamManager()
        self.model_client = ModelClient()
        
        # Initialize skills
        self.research = ResearchSkill(self.model_client, self.stream)
        self.quant = QuantAnalysisSkill(self.model_client, self.stream)
        self.memory = MemorySkill(self.model_client, self.stream)
        self.report = ReportSkill(self.model_client, self.stream)
        
        self.models_used = set()
    
    async def execute(self, query: str, namespace: str = "default") -> SAGEResult:
        """
        Execute a research task.
        
        Args:
            query: The research question
            namespace: Memory namespace (e.g., ticker symbol)
        
        Returns:
            SAGEResult with final report and metadata
        """
        start_time = time.time()
        
        await self.stream.status("SAGE starting analysis", "🚀")
        
        # Step 1: Check memory for existing knowledge
        await self.stream.status("Checking memory", "🧠")
        skip_research, reason = await self.memory.should_skip_research(query, namespace)
        
        memory_context = None
        if skip_research:
            await self.stream.status(f"Using cached research: {reason}", "💾")
            memory_result = await self.memory.recall(query, namespace)
            memory_context = memory_result.results
        
        # Step 2: Research (if needed)
        research_results = None
        if not skip_research:
            await self.stream.status("Starting research", "🔍")
            research_results = await self.research.research(query)
            self.models_used.update(["claude-sonnet-4", "gpt-4o"])
        else:
            # Use memory as research results
            research_results = memory_context
        
        # Step 3: Quantitative Analysis
        if research_results and hasattr(research_results, 'extracted_data'):
            await self.stream.status("Running quantitative analysis", "🧮")
            analysis_results = await self.quant.analyze(
                data=research_results.extracted_data or {},
                analysis_request=query,
            )
            self.models_used.add("claude-sonnet-4")
        else:
            analysis_results = None
        
        # Step 4: Store new findings in memory
        if research_results and not skip_research:
            await self.stream.status("Storing findings in memory", "💾")
            content = str(research_results)
            metadata = {
                "query": query,
                "timestamp": time.time(),
                "namespace": namespace,
            }
            await self.memory.store(content, metadata, namespace)
        
        # Step 5: Generate final report
        await self.stream.status("Generating final briefing", "📝")
        final_report = await self.report.generate(
            query=query,
            research_results=research_results,
            analysis_results=analysis_results,
            memory_context=memory_context,
        )
        
        # Complete
        total_time = time.time() - start_time
        metadata = {
            "total_time": total_time,
            "models_used": list(self.models_used),
            "used_cache": skip_research,
        }
        
        await self.stream.done(metadata)
        
        return SAGEResult(
            query=query,
            report=final_report,
            metadata=metadata,
        )
    
    def get_stream(self) -> StreamManager:
        """Get the stream manager for this orchestration."""
        return self.stream
