"""Configuration management for SAGE."""
import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Config(BaseModel):
    """SAGE configuration."""
    
    # Mode
    mode: Literal["mock", "production"] = os.getenv("SAGE_MODE", "mock")
    
    # API Keys
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    hyperbrowser_api_key: str | None = os.getenv("HYPERBROWSER_API_KEY")
    e2b_api_key: str | None = os.getenv("E2B_API_KEY")
    turbopuffer_api_key: str | None = os.getenv("TURBOPUFFER_API_KEY")
    braintrust_api_key: str | None = os.getenv("BRAINTRUST_API_KEY")
    
    # Model configuration
    orchestrator_model: str = "claude-sonnet-4"
    extractor_model: str = "gpt-4o"
    longform_model: str = "gemini-2.5-pro"
    
    # Streaming
    enable_streaming: bool = True
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mode == "mock" or not any([
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key,
        ])
    
    def validate_production(self) -> list[str]:
        """Validate production configuration. Returns list of missing keys."""
        if self.mode == "mock":
            return []
        
        missing = []
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "GOOGLE_API_KEY": self.google_api_key,
            "HYPERBROWSER_API_KEY": self.hyperbrowser_api_key,
            "E2B_API_KEY": self.e2b_api_key,
            "TURBOPUFFER_API_KEY": self.turbopuffer_api_key,
        }
        
        for key, value in required.items():
            if not value:
                missing.append(key)
        
        return missing


# Global config instance
config = Config()
