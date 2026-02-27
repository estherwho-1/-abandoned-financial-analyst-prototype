# 🧪 SAGE Test Instructions

## Quick Test (No API Keys Required)

SAGE works in **MOCK mode** out of the box. You can test the entire architecture without any API keys.

### 1. Install Dependencies

```bash
cd /data/.openclaw/workspace/sage

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
python tests/test_sage.py
```

**Expected output:**
```
============================================================
🏦 SAGE Test Suite (Mock Mode)
============================================================

🧪 Testing Model Client...
  ✅ Orchestrator model: claude-sonnet-4 (mock)
  ✅ Extractor model: gpt-4o (mock)
  ✅ Model client working

🧪 Testing Research Skill...
  ✅ Found 5 findings
  ✅ Found 5 sources
  ✅ Extracted 5 metrics
  ✅ Research skill working

... (more tests)

============================================================
✅ ALL TESTS PASSED
============================================================
```

### 3. Run Full Example Query

```bash
python main.py "What is NVIDIA's competitive position in AI chips?"
```

**Expected output:**
- Status updates as SAGE works through each step
- Mock research findings
- Mock quantitative analysis with charts
- Bull/Bear case analysis
- Source citations
- Final metadata (time, models used)

---

## Production Mode (With Real API Keys)

Once you have API keys, switch to production mode:

### 1. Configure API Keys

```bash
# Copy example config
cp config/.env.example config/.env

# Edit with your keys
nano config/.env
```

Add your keys:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
HYPERBROWSER_API_KEY=...
E2B_API_KEY=...
TURBOPUFFER_API_KEY=...

# Set mode to production
SAGE_MODE=production
```

### 2. Test Production Mode

```bash
python main.py "Research Tesla's Q4 2025 earnings"
```

This will use real APIs for:
- Web search (Hyperbrowser)
- LLM calls (Claude, GPT-4o, Gemini)
- Code execution (E2B sandbox)
- Vector storage (Turbopuffer)

---

## Test Scenarios

### Scenario 1: Basic Company Research
```bash
python main.py "What is Apple's current valuation?"
```

### Scenario 2: Competitive Analysis
```bash
python main.py "Compare AMD vs Intel in server CPU market"
```

### Scenario 3: Financial Metrics
```bash
python main.py "Calculate Microsoft's Rule of 40 score"
```

### Scenario 4: Bull/Bear Case
```bash
python main.py "Give me bull and bear case for Palantir"
```

### Scenario 5: Memory Test (Run Twice)
```bash
# First run - should do research
python main.py "NVIDIA data center revenue growth"

# Second run - should use cached memory
python main.py "NVIDIA data center revenue growth"
```

---

## Verify Streaming

To test streaming output in real-time:

```bash
python main.py "Research Amazon AWS growth" 2>&1 | tee output.log
```

You should see:
- `🚀 SAGE starting analysis`
- `🧠 Checking memory`
- `🔍 Starting research`
- `📄 Fetching detailed sources`
- `🧮 Running quantitative analysis`
- `📊 Chart: ...`
- `📝 Generating final briefing`
- `✅ Completed in X.Xs`

---

## Troubleshooting

### Test fails with "ModuleNotFoundError"
```bash
# Make sure you're in the sage directory
cd /data/.openclaw/workspace/sage

# Install dependencies
pip install -r requirements.txt
```

### "Missing API keys" warning
This is expected if you haven't configured `.env` yet. The system will run in MOCK mode automatically.

### Import errors
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/data/.openclaw/workspace/sage:$PYTHONPATH
```

---

## What's Working in Mock Mode

✅ **Full architecture**
- Multi-model routing (Claude/GPT-4o/Gemini)
- All 4 skills (Research, Quant, Memory, Report)
- Streaming progress updates
- Structured output with citations

✅ **Mock implementations**
- Web search returns realistic mock data
- Code execution returns mock metrics + charts
- Vector memory stores in-memory
- All data flows work end-to-end

---

## Next Steps After Testing

Once you verify everything works in mock mode:

1. **Add API keys** to `config/.env`
2. **Test one API at a time** (start with just Anthropic)
3. **Build MCP server** (see `mcp/server.py` - not yet implemented)
4. **Add Braintrust observability** (optional)
5. **Deploy to production** (add error handling, rate limiting)

---

## API Key Priority (If Limited Budget)

If you can only get some API keys, prioritize:

1. **Anthropic** (Claude Sonnet) - Core orchestration brain
2. **OpenAI** (GPT-4o) - Structured extraction
3. **Hyperbrowser** - Web search/fetch
4. **E2B** - Code execution
5. **Turbopuffer** - Memory (can use in-memory fallback)
6. **Google AI** (Gemini) - Long-context (can route to Claude)
7. **Braintrust** - Observability (optional for MVP)

---

## Expected Performance

### Mock Mode
- Response time: ~2-5 seconds
- All features work, but data is simulated

### Production Mode (Estimated)
- Simple query: 15-30 seconds
- Complex analysis: 45-90 seconds
- With memory cache: 10-20 seconds

---

## Questions?

Check the main `README.md` for architecture details or inspect the code:

- `core/orchestrator.py` - Main coordination logic
- `skills/*.py` - Individual skill implementations
- `core/models.py` - Multi-model routing
- `core/streaming.py` - SSE streaming

Happy testing! 🚀
