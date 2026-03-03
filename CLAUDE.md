# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SAGE (Strategic Analyst & Guided Equity-researcher)** is an AI-powered financial research analyst that uses multi-model orchestration to analyze companies, markets, and financial data. The system operates in two modes:

- **Mock mode**: Works out-of-the-box without API keys (for testing/development)
- **Production mode**: Uses real APIs for web search, LLM calls, code execution, and vector storage

## Development Commands

### Running Tests
```bash
# Run full test suite (works without API keys)
python tests/test_sage.py

# Run with specific query
python main.py "Your research question here"
```

### Installation
```bash
# Install all dependencies
pip install -r requirements.txt

# Install minimal dependencies (for mock mode only)
pip install -r requirements-minimal.txt
```

### Configuration
```bash
# Copy environment template
cp config/.env.example config/.env

# Edit with your API keys
# Then set SAGE_MODE=production in config/.env
```

## Architecture Overview

### Core Execution Flow

The orchestrator (`core/orchestrator.py`) coordinates a 5-step pipeline:

1. **Memory Check** (`skills/memory.py`): Checks if we already have relevant cached research
2. **Research** (`skills/research.py`): If needed, performs web search + data extraction
3. **Quant Analysis** (`skills/quant_analysis.py`): Runs calculations and generates charts
4. **Memory Store**: Caches new findings for future queries
5. **Report** (`skills/report.py`): Synthesizes everything into a final briefing

### Multi-Model Routing

The `ModelClient` (`core/models.py`) routes tasks to different LLMs based on capability:

- **orchestrator** → Claude Sonnet 4: Planning, reasoning, writing
- **extractor** → GPT-4o: Structured data extraction from web content
- **longform** → Gemini 2.5 Pro: Long-context document analysis

In mock mode, all models return realistic simulated responses without API calls.

### Streaming System

Real-time progress updates use Server-Sent Events (SSE) via `StreamManager` (`core/streaming.py`). Event types:

- `status`: Progress updates (e.g., "🔍 Starting research")
- `chunk`: Streaming text for final report
- `chart`: Generated visualizations with base64 images
- `sources`: Citation list with URLs
- `done`: Completion metadata (time, models used)
- `error`: Error messages with details

### Skills Architecture

Each skill is a self-contained module with:
- Model client reference for LLM calls
- Stream manager for progress updates
- Mock mode support for testing
- Async execution with structured outputs

## Key Implementation Details

### Mock Mode vs Production

- Check mode with `config.is_mock_mode()`
- Mock mode returns realistic data without external API calls
- All skills have complete mock implementations
- Production mode requires 6 API keys (see `config/.env.example`)

### Adding New Skills

1. Create new file in `skills/` directory
2. Accept `ModelClient` and `StreamManager` in `__init__`
3. Implement mock responses for testing
4. Add to orchestrator workflow in `core/orchestrator.py`

### Configuration System

The config loader (`config/config.py`) auto-detects mock mode if API keys are missing. It validates production requirements and returns missing keys, allowing graceful degradation.

### Path Management

The CLI entry point (`main.py`) adds the project root to `sys.path`, so all imports work from any directory. Run commands from the project root.

## External APIs

Production mode integrates 7 external services:

1. **OpenAI** - GPT-4o for structured extraction
2. **Anthropic** - Claude Sonnet for orchestration
3. **Google AI** - Gemini 2.5 Pro for long-context analysis
4. **Hyperbrowser** - Web search + page fetching
5. **E2B** - Sandboxed code execution
6. **Turbopuffer** - Vector storage for memory
7. **Braintrust** - Observability (optional)

Real API implementations are stubs in `core/models.py` (lines 178-191). Mock mode is fully functional.

## Testing Strategy

- All tests work in mock mode by default
- Test individual skills: Import and instantiate with mock client
- Test full pipeline: Run `orchestrator.execute(query)`
- Verify streaming: Check `stream.events` list after execution
- Production tests: Set `SAGE_MODE=production` in environment

## Important Constraints

- The MCP server (`mcp/server.py`) is defined but not yet implemented
- Real API implementations need to be built (currently raise `NotImplementedError`)
- Memory skill uses in-memory storage in mock mode; Turbopuffer in production
- Charts in mock mode return placeholder base64 strings
