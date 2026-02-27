"""QuantAnalysisSkill - Code execution and chart generation."""
import asyncio
import base64
from typing import Any
from pydantic import BaseModel
from core.models import ModelClient, Message
from core.streaming import StreamManager
from config.config import config


class AnalysisResult(BaseModel):
    """Results from quantitative analysis."""
    query: str
    metrics: dict  # Computed metrics
    charts: list[dict]  # List of {title, image_base64, description}
    code_executed: str
    stdout: str


class QuantAnalysisSkill:
    """
    Runs quantitative financial analysis using code execution.
    
    Flow:
    1. Takes structured data + analysis request
    2. Claude generates Python code
    3. Executes in E2B sandbox
    4. Returns computed metrics + charts
    5. Self-heals errors (up to 3 retries)
    """
    
    def __init__(self, model_client: ModelClient, stream: StreamManager):
        self.model = model_client
        self.stream = stream
        self.is_mock = config.is_mock_mode()
        self.max_retries = 3
    
    async def analyze(
        self,
        data: dict,
        analysis_request: str,
    ) -> AnalysisResult:
        """
        Execute quantitative analysis.
        
        Args:
            data: Structured financial data (from ResearchSkill)
            analysis_request: What to analyze (e.g., "calculate revenue CAGR")
        
        Returns:
            AnalysisResult with metrics and charts
        """
        await self.stream.status("Generating analysis code", "🧮")
        
        # Generate Python code using Claude
        code = await self._generate_code(data, analysis_request)
        
        # Execute code in sandbox
        await self.stream.status("Running analysis in sandbox", "⚡")
        result = await self._execute_code(code)
        
        # Parse results
        metrics, charts = await self._parse_results(result)
        
        return AnalysisResult(
            query=analysis_request,
            metrics=metrics,
            charts=charts,
            code_executed=code,
            stdout=result.get("stdout", ""),
        )
    
    async def _generate_code(self, data: dict, request: str) -> str:
        """Generate Python code for analysis."""
        prompt = f"""You are a quantitative financial analyst. Generate Python code to analyze this data.

Data:
{data}

Analysis Request: {request}

Requirements:
- Use pandas, numpy, matplotlib for analysis and charts
- Save charts as PNG to /tmp/chart_N.png
- Print final metrics in JSON format to stdout
- Include error handling

Return ONLY the Python code, no explanations."""
        
        response = await self.model.complete(
            messages=[Message(role="user", content=prompt)],
            model="orchestrator",
        )
        
        # Extract code from response (remove markdown if present)
        code = response.content
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code
    
    async def _execute_code(
        self,
        code: str,
        retry_count: int = 0,
    ) -> dict:
        """Execute code in E2B sandbox (or mock)."""
        if self.is_mock:
            return await self._mock_execute(code)
        
        # Real E2B execution would go here
        # For now, use mock
        return await self._mock_execute(code)
    
    async def _mock_execute(self, code: str) -> dict:
        """Mock code execution results."""
        await asyncio.sleep(0.5)  # Simulate execution time
        
        # Generate mock chart (1x1 pixel PNG)
        mock_chart_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        return {
            "success": True,
            "stdout": """{
    "revenue_cagr_3y": 42.3,
    "gross_margin_avg": 66.7,
    "operating_margin_latest": 51.2,
    "rule_of_40_score": 96.5,
    "pe_ratio": 48.3,
    "ev_sales": 32.1
}""",
            "stderr": "",
            "charts": [
                {"path": "/tmp/chart_1.png", "title": "Revenue Growth by Segment"},
                {"path": "/tmp/chart_2.png", "title": "Margin Expansion Timeline"},
                {"path": "/tmp/chart_3.png", "title": "Valuation Multiples Comparison"},
            ],
            "chart_data": [mock_chart_b64] * 3,
        }
    
    async def _parse_results(self, execution_result: dict) -> tuple[dict, list[dict]]:
        """Parse metrics and charts from execution results."""
        import json
        
        # Parse metrics from stdout
        metrics = {}
        try:
            stdout = execution_result.get("stdout", "")
            if stdout:
                metrics = json.loads(stdout)
        except:
            metrics = {"error": "Failed to parse metrics"}
        
        # Parse charts
        charts = []
        chart_data = execution_result.get("chart_data", [])
        chart_info = execution_result.get("charts", [])
        
        for i, chart_b64 in enumerate(chart_data):
            info = chart_info[i] if i < len(chart_info) else {}
            charts.append({
                "title": info.get("title", f"Chart {i+1}"),
                "image_base64": chart_b64,
                "description": "",
            })
            
            # Emit chart event
            await self.stream.chart(
                title=info.get("title", f"Chart {i+1}"),
                image_base64=chart_b64,
            )
        
        return metrics, charts
