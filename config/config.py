"""Configuration management for SAGE."""
import os
import warnings
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def _parse_mock_flag(env_var: str, default: bool = True) -> bool:
    """Parse a MOCK_* env var. Returns True (mocked) unless explicitly 'false'."""
    val = os.getenv(env_var, "")
    if val.lower() == "false":
        return False
    if val.lower() == "true":
        return True
    return default


class Config(BaseModel):
    """SAGE configuration."""

    # Mode (legacy — kept for backward compat)
    mode: Literal["mock", "production"] = os.getenv("SAGE_MODE", "mock")

    # API Keys
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    hyperbrowser_api_key: str | None = os.getenv("HYPERBROWSER_API_KEY")
    e2b_api_key: str | None = os.getenv("E2B_API_KEY")
    turbopuffer_api_key: str | None = os.getenv("TURBOPUFFER_API_KEY")
    braintrust_api_key: str | None = os.getenv("BRAINTRUST_API_KEY")

    # Per-service mock flags (default True = mocked)
    mock_llm: bool = _parse_mock_flag("MOCK_LLM")
    mock_search: bool = _parse_mock_flag("MOCK_SEARCH")
    mock_e2b: bool = _parse_mock_flag("MOCK_E2B")
    mock_memory: bool = _parse_mock_flag("MOCK_MEMORY")

    # Per-role provider routing ("anthropic", "openai", "google", or "openrouter")
    orchestrator_provider: str = os.getenv("ORCHESTRATOR_PROVIDER", "anthropic")
    extractor_provider: str = os.getenv("EXTRACTOR_PROVIDER", "openai")
    longform_provider: str = os.getenv("LONGFORM_PROVIDER", "google")

    # Model IDs (OpenRouter format; native providers auto-strip prefix)
    orchestrator_model: str = os.getenv("ORCHESTRATOR_MODEL", "anthropic/claude-sonnet-4")
    extractor_model: str = os.getenv("EXTRACTOR_MODEL", "openai/gpt-4o")
    longform_model: str = os.getenv("LONGFORM_MODEL", "google/gemini-2.5-pro")

    # Streaming
    enable_streaming: bool = True

    @staticmethod
    def native_model_id(model_id: str) -> str:
        """Strip provider prefix: 'anthropic/claude-sonnet-4' -> 'claude-sonnet-4'."""
        return model_id.split("/", 1)[-1]

    def model_post_init(self, __context):
        """Validate per-service flags against available API keys.

        LLM provider logic:
        - If OPENROUTER_API_KEY is set, all roles route through OpenRouter
          (provider overrides and native keys are ignored).
        - Otherwise, each role uses its native provider and needs the
          corresponding API key (ANTHROPIC, OPENAI, GOOGLE).
        """
        if not self.mock_llm:
            if self.openrouter_api_key:
                # OpenRouter handles everything — override providers
                self.orchestrator_provider = "openrouter"
                self.extractor_provider = "openrouter"
                self.longform_provider = "openrouter"
            else:
                # Native providers — check each role has its key
                provider_keys = {
                    "anthropic": ("ANTHROPIC_API_KEY", self.anthropic_api_key),
                    "openai": ("OPENAI_API_KEY", self.openai_api_key),
                    "google": ("GOOGLE_API_KEY", self.google_api_key),
                }
                needed = {self.orchestrator_provider, self.extractor_provider, self.longform_provider}
                missing = []
                for provider in needed:
                    if provider in provider_keys:
                        key_name, key_val = provider_keys[provider]
                        if not key_val:
                            missing.append(key_name)
                    elif provider == "openrouter":
                        missing.append("OPENROUTER_API_KEY")
                if missing:
                    warnings.warn(
                        f"MOCK_LLM=false but missing keys: {', '.join(missing)}. "
                        "Forcing mock_llm=True."
                    )
                    self.mock_llm = True

        if not self.mock_search and not self.hyperbrowser_api_key:
            warnings.warn("MOCK_SEARCH=false but HYPERBROWSER_API_KEY missing. Forcing mock_search=True.")
            self.mock_search = True

        if not self.mock_e2b and not self.e2b_api_key:
            warnings.warn("MOCK_E2B=false but E2B_API_KEY missing. Forcing mock_e2b=True.")
            self.mock_e2b = True

        if not self.mock_memory and not self.turbopuffer_api_key:
            warnings.warn("MOCK_MEMORY=false but TURBOPUFFER_API_KEY missing. Forcing mock_memory=True.")
            self.mock_memory = True

    def is_mock_mode(self) -> bool:
        """Check if ALL services are mocked (backward compat convenience)."""
        return self.mock_llm and self.mock_search and self.mock_e2b and self.mock_memory

    def validate_production(self) -> list[str]:
        """Validate production configuration. Returns list of missing keys."""
        if self.is_mock_mode():
            return []

        missing = []

        # LLM keys: OpenRouter OR native provider keys
        if not self.mock_llm:
            if self.openrouter_api_key:
                pass  # OpenRouter covers all LLM roles
            else:
                native_keys = {
                    "anthropic": ("ANTHROPIC_API_KEY", self.anthropic_api_key),
                    "openai": ("OPENAI_API_KEY", self.openai_api_key),
                    "google": ("GOOGLE_API_KEY", self.google_api_key),
                }
                for provider in {self.orchestrator_provider, self.extractor_provider, self.longform_provider}:
                    if provider in native_keys:
                        key_name, key_val = native_keys[provider]
                        if not key_val:
                            missing.append(key_name)

        # Service keys
        if not self.mock_search and not self.hyperbrowser_api_key:
            missing.append("HYPERBROWSER_API_KEY")
        if not self.mock_e2b and not self.e2b_api_key:
            missing.append("E2B_API_KEY")
        if not self.mock_memory and not self.turbopuffer_api_key:
            missing.append("TURBOPUFFER_API_KEY")

        return missing


# Global config instance
config = Config()
