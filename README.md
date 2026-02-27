# 🏦 SAGE - Strategic Analyst & Guided Equity-researcher

## Quick Start

```bash
# Install dependencies
cd sage
pip install -r requirements.txt

# Run mock test (no API keys needed)
python tests/test_sage.py

# Run with real APIs (after adding keys to config/.env)
python main.py "Research NVIDIA's competitive position"
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
