# 🏦 SAGE - Strategic Analyst & Guided Equity-researcher

AI financial research analyst with multi-model orchestration. Searches the web, runs quantitative analysis, builds persistent knowledge, and streams real-time briefings.

## Quick Start

### 1. Clone the Repository
```bash
git clone git@github.com:estherwho-1/sage-financial-analyst.git
cd sage-financial-analyst
```

**Note:** Always activate the virtual environment before running SAGE:
```bash
source venv/bin/activate
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies
```bash
# Minimal (for mock mode testing)
pip install pydantic python-dotenv rich

# Full (for production with all APIs)
pip install -r requirements.txt
```

### 4. Test in Mock Mode (No API Keys Needed)
```bash
# Run test suite
python tests/test_sage.py

# Run example query
python main.py "What is NVIDIA's competitive position in AI chips?"
```

### 5. Setup Environment for Production Mode

**Copy the environment template:**
```bash
cp config/.env.example config/.env
```

**Edit `config/.env` and add your API keys:**
```bash
# Required for core functionality
ANTHROPIC_API_KEY=sk-ant-...      # Get from: https://console.anthropic.com/
OPENAI_API_KEY=sk-...              # Get from: https://platform.openai.com/
GOOGLE_API_KEY=...                 # Get from: https://makersuite.google.com/

# Optional for full features
HYPERBROWSER_API_KEY=...           # Get from: https://hyperbrowser.ai/
E2B_API_KEY=...                    # Get from: https://e2b.dev/
TURBOPUFFER_API_KEY=...            # Get from: https://turbopuffer.com/
BRAINTRUST_API_KEY=...             # Get from: https://braintrust.dev/ (optional)

# Mode: "mock" or "production"
SAGE_MODE=production
```

**Note:** Mock mode works without any keys. Production mode requires at minimum: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`

### 6. Run with Real APIs
```bash
python main.py "Research Tesla Q4 2025 earnings"
```

## Project Structure

```
sage/
├── core/
│   ├── orchestrator.py    # Main agent loop + routing
│   ├── models.py          # Multi-model LLM client
│   └── streaming.py       # SSE streaming
├── skills/
│   ├── research.py        # Web search + extraction
│   ├── quant_analysis.py  # Code execution + charts
│   ├── memory.py          # Vector storage + retrieval
│   └── report.py          # Final briefing generation
├── mcp/
│   └── server.py          # MCP tool server
├── config/
│   ├── .env.example       # API key template
│   └── config.py          # Configuration loader
├── tests/
│   └── test_sage.py       # Integration tests
├── main.py                # CLI entry point
└── requirements.txt
```

## API Keys Needed

1. **OpenAI** - GPT-4o for structured extraction
2. **Anthropic** - Claude Sonnet for orchestration
3. **Google AI** - Gemini 2.5 Pro for long-context analysis
4. **Hyperbrowser** - Web search + fetch
5. **E2B** - Sandbox execution
6. **Turbopuffer** - Vector storage
7. **Braintrust** - Observability (optional)

## Configuration

Copy `config/.env.example` to `config/.env` and add your keys:

```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

## Features

- ✅ Mock mode (works without API keys)
- ✅ Multi-model routing (Claude/GPT-4o/Gemini)
- ✅ Streaming progress updates
- ✅ Skill-based architecture
- ✅ MCP server integration
- 🚧 Real API integrations (add keys)
- 🚧 Braintrust observability
