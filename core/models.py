"""Multi-model LLM client with intelligent routing."""
import asyncio
from typing import Literal, AsyncIterator
from pydantic import BaseModel
from config.config import config


class Message(BaseModel):
    """Chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class LLMResponse(BaseModel):
    """LLM response."""
    content: str
    model: str
    usage: dict | None = None


class ModelClient:
    """Multi-model LLM client with routing logic."""
    
    def __init__(self):
        self.is_mock = config.is_mock_mode()
        
        if not self.is_mock:
            self._init_real_clients()
    
    def _init_real_clients(self):
        """Initialize real API clients."""
        try:
            if config.anthropic_api_key:
                from anthropic import AsyncAnthropic
                self.anthropic = AsyncAnthropic(api_key=config.anthropic_api_key)
        except ImportError:
            print("⚠️  Anthropic SDK not installed")
        
        try:
            if config.openai_api_key:
                from openai import AsyncOpenAI
                self.openai = AsyncOpenAI(api_key=config.openai_api_key)
        except ImportError:
            print("⚠️  OpenAI SDK not installed")
        
        try:
            if config.google_api_key:
                import google.generativeai as genai
                genai.configure(api_key=config.google_api_key)
                self.gemini = genai
        except ImportError:
            print("⚠️  Google Generative AI SDK not installed")
    
    async def complete(
        self,
        messages: list[Message],
        model: Literal["orchestrator", "extractor", "longform"] = "orchestrator",
        stream: bool = False,
    ) -> LLMResponse | AsyncIterator[str]:
        """
        Complete a chat conversation.
        
        Routes to the appropriate model based on task type:
        - orchestrator: Claude Sonnet (planning, reasoning, writing)
        - extractor: GPT-4o (structured data extraction)
        - longform: Gemini 2.5 Pro (long-context analysis)
        """
        if self.is_mock:
            return await self._mock_complete(messages, model, stream)
        
        if model == "orchestrator":
            return await self._call_claude(messages, stream)
        elif model == "extractor":
            return await self._call_gpt4o(messages, stream)
        elif model == "longform":
            return await self._call_gemini(messages, stream)
        else:
            raise ValueError(f"Unknown model type: {model}")
    
    async def _mock_complete(
        self,
        messages: list[Message],
        model: str,
        stream: bool,
    ) -> LLMResponse | AsyncIterator[str]:
        """Mock completion for testing without API keys."""
        model_names = {
            "orchestrator": "claude-sonnet-4 (mock)",
            "extractor": "gpt-4o (mock)",
            "longform": "gemini-2.5-pro (mock)",
        }
        
        # Generate mock response based on last user message
        last_msg = next((m for m in reversed(messages) if m.role == "user"), None)
        query = last_msg.content if last_msg else "query"
        
        mock_content = self._generate_mock_response(query, model)
        
        if stream:
            async def stream_mock():
                words = mock_content.split()
                for i, word in enumerate(words):
                    yield word + (" " if i < len(words) - 1 else "")
                    await asyncio.sleep(0.05)  # Simulate streaming delay
            return stream_mock()
        
        return LLMResponse(
            content=mock_content,
            model=model_names[model],
            usage={"mock": True, "tokens": len(mock_content.split())},
        )
    
    def _generate_mock_response(self, query: str, model: str) -> str:
        """Generate contextual mock responses."""
        query_lower = query.lower()
        
        if "research" in query_lower or "search" in query_lower:
            return """🔍 Mock Research Results:

**Key Findings:**
1. Revenue grew 45% YoY in Q4 2025
2. Data center segment up 78% driven by AI demand
3. Gaming segment stabilizing after crypto decline
4. Gross margins expanded to 68.2%

**Sources:**
- Company earnings release (Q4 2025)
- Investor presentation slides
- Analyst coverage from major banks

**Extracted Metrics:**
- Q4 Revenue: $18.1B (vs $12.5B YoY)
- EPS: $4.93 (vs $3.34 YoY)
- Data Center: $14.2B revenue
- Operating Margin: 54%"""
        
        elif "analysis" in query_lower or "calculate" in query_lower:
            return """🧮 Mock Quantitative Analysis:

**Financial Metrics Computed:**
- Revenue CAGR (3yr): 42.3%
- Gross Margin Trend: 64% → 66% → 68% (expanding)
- Rule of 40 Score: 96 (Revenue Growth 45% + Op Margin 51%)
- P/E Ratio: 48x (vs sector avg 28x)
- EV/Sales: 32x

**Charts Generated:**
📊 [Mock Chart: Revenue Growth by Segment]
📊 [Mock Chart: Margin Expansion Timeline]
📊 [Mock Chart: Valuation Multiples Comparison]

**Code Executed:**
```python
import pandas as pd
df = get_financial_data('NVDA', period='3y')
growth_rate = df['revenue'].pct_change().mean()
# Output: 42.3% CAGR
```"""
        
        elif "bull case" in query_lower or "bear case" in query_lower:
            return """📈 Bull Case:
1. **AI Infrastructure Dominance** - CUDA moat creates switching costs
2. **Pricing Power** - Demand far exceeds supply, gross margins expanding
3. **Long Runway** - AI infrastructure spend estimated $1T+ over 5 years
4. **Platform Effect** - Software (CUDA, AI Enterprise) locks in customers

📉 Bear Case:
1. **Valuation Risk** - Trading at 48x earnings requires sustained growth
2. **Competition** - AMD, Intel, custom chips (Google TPU, Amazon Trainium)
3. **Customer Concentration** - Top 4 customers = 40% of revenue
4. **Cyclical Exposure** - Data center spending can reverse quickly"""
        
        else:
            return f"""Mock response for: {query}

This is a simulated response. To get real analysis, add API keys to config/.env and set SAGE_MODE=production."""
    
    async def _call_claude(self, messages: list[Message], stream: bool) -> LLMResponse:
        """Call Anthropic Claude API."""
        # Real implementation would go here
        raise NotImplementedError("Add ANTHROPIC_API_KEY to use Claude")
    
    async def _call_gpt4o(self, messages: list[Message], stream: bool) -> LLMResponse:
        """Call OpenAI GPT-4o API."""
        # Real implementation would go here
        raise NotImplementedError("Add OPENAI_API_KEY to use GPT-4o")
    
    async def _call_gemini(self, messages: list[Message], stream: bool) -> LLMResponse:
        """Call Google Gemini API."""
        # Real implementation would go here
        raise NotImplementedError("Add GOOGLE_API_KEY to use Gemini")
