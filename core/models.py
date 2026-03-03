"""Multi-model LLM client with intelligent routing."""
import asyncio
from typing import Literal, AsyncIterator
from pydantic import BaseModel
from config.config import config, Config


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
    """Multi-model LLM client with provider registry routing."""

    def __init__(self):
        self.is_mock = config.mock_llm

        # Map each role to (provider_name, model_id)
        self._role_config: dict[str, tuple[str, str]] = {
            "orchestrator": (config.orchestrator_provider, config.orchestrator_model),
            "extractor": (config.extractor_provider, config.extractor_model),
            "longform": (config.longform_provider, config.longform_model),
        }

        # Provider dispatch table (populated by _init_real_clients)
        self._providers: dict[str, callable] = {}

        if not self.is_mock:
            self._init_real_clients()

    def _init_real_clients(self):
        """Initialize only the API clients needed by configured providers."""
        needed = {provider for provider, _ in self._role_config.values()}

        if "anthropic" in needed:
            try:
                from anthropic import AsyncAnthropic
                self._anthropic = AsyncAnthropic(api_key=config.anthropic_api_key)
                self._providers["anthropic"] = self._call_anthropic
            except ImportError:
                print("⚠️  Anthropic SDK not installed")

        if "openai" in needed:
            try:
                from openai import AsyncOpenAI
                self._openai = AsyncOpenAI(api_key=config.openai_api_key)
                self._providers["openai"] = self._call_openai
            except ImportError:
                print("⚠️  OpenAI SDK not installed")

        if "google" in needed:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.google_api_key)
                self._gemini = genai
                self._providers["google"] = self._call_google
            except ImportError:
                print("⚠️  Google Generative AI SDK not installed")

        if "openrouter" in needed:
            try:
                from openai import AsyncOpenAI
                self._openrouter = AsyncOpenAI(
                    api_key=config.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                )
                self._providers["openrouter"] = self._call_openrouter
            except ImportError:
                print("⚠️  OpenAI SDK not installed (needed for OpenRouter)")

    async def complete(
        self,
        messages: list[Message],
        model: Literal["orchestrator", "extractor", "longform"] = "orchestrator",
        stream: bool = False,
    ) -> LLMResponse | AsyncIterator[str]:
        """
        Complete a chat conversation.

        Routes to the appropriate provider based on per-role configuration:
        - orchestrator: defaults to Anthropic Claude
        - extractor: defaults to OpenAI GPT-4o
        - longform: defaults to Google Gemini

        Any role can be routed through OpenRouter or swapped to another provider.
        """
        if self.is_mock:
            return await self._mock_complete(messages, model, stream)

        provider_name, model_id = self._role_config[model]
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not available for role '{model}'")
        return await self._providers[provider_name](messages, model_id, stream)

    async def _mock_complete(
        self,
        messages: list[Message],
        model: str,
        stream: bool,
    ) -> LLMResponse | AsyncIterator[str]:
        """Mock completion for testing without API keys."""
        _, model_id = self._role_config[model]
        model_name = f"{model_id} (mock)"

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
            model=model_name,
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

    async def _call_anthropic(self, messages: list[Message], model_id: str, stream: bool) -> LLMResponse:
        """Call Anthropic Claude API."""
        native_id = Config.native_model_id(model_id)
        response = await self._anthropic.messages.create(
            model=native_id,
            max_tokens=4096,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        )

    async def _call_openai(self, messages: list[Message], model_id: str, stream: bool) -> LLMResponse:
        """Call OpenAI API."""
        native_id = Config.native_model_id(model_id)
        response = await self._openai.chat.completions.create(
            model=native_id,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens},
        )

    async def _call_google(self, messages: list[Message], model_id: str, stream: bool) -> LLMResponse:
        """Call Google Gemini API."""
        native_id = Config.native_model_id(model_id)
        model = self._gemini.GenerativeModel(native_id)
        contents = [{"role": "user" if m.role == "user" else "model", "parts": [m.content]} for m in messages]
        response = await model.generate_content_async(contents)
        return LLMResponse(
            content=response.text,
            model=native_id,
            usage={"input": 0, "output": 0},
        )

    async def _call_openrouter(self, messages: list[Message], model_id: str, stream: bool) -> LLMResponse:
        """Call OpenRouter API (OpenAI-compatible)."""
        response = await self._openrouter.chat.completions.create(
            model=model_id,  # OpenRouter needs provider/model format as-is
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            usage={"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens},
        )
