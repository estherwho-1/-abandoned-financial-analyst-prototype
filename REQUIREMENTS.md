# 🏦 Project: **SAGE** — Strategic Analyst & Guided Equity-researcher

### An AI financial research analyst that monitors markets, deeply researches companies, runs quantitative analysis in sandboxes, builds persistent knowledge over time, and streams real-time briefings — all orchestrated across multiple LLMs.

---

## The Pitch

Imagine having a junior analyst on your team who never sleeps. You tell SAGE:

> *"Research NVIDIA's competitive position in the AI chip market. Compare their margins, revenue growth, and R&D spend against AMD and Intel over the last 3 years. Then give me a bull and bear case."*

SAGE will:
1. **Search the web** for recent earnings reports, news, and analyst commentary (Hyperbrowser)
2. **Fetch and parse** full SEC filings, earnings transcripts, and articles (Hyperbrowser)
3. **Store everything** it learns in vector memory for future queries (Turbopuffer)
4. **Spin up a sandbox** to run Python code — pull financial data, build charts, calculate ratios (E2B)
5. **Route sub-tasks** to the best model — Claude for deep reasoning, Gemini for long-context doc analysis, GPT-4o for structured extraction (Multi-model)
6. **Stream a live briefing** back to you with charts, citations, and a final recommendation (Streaming)
7. **Log every step** so you can debug, eval, and improve the system (Braintrust)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    SAGE Orchestrator                 │
│              (Main Agent Loop + Router)              │
├─────────────┬──────────────┬───────────────┬────────┤
│  Research   │  Analysis    │   Memory      │ Report │
│  Skill      │  Skill       │   Skill       │ Skill  │
├─────────────┼──────────────┼───────────────┼────────┤
│ Hyperbrowser│ E2B Sandbox  │ Turbopuffer   │ Stream │
│ (search +   │ (run Python, │ (vector store │ (SSE   │
│  web fetch) │  charts)     │  + retrieval) │  out)  │
├─────────────┴──────────────┴───────────────┴────────┤
│               MCP Tool Server                       │
│  (Exposes SAGE's capabilities as MCP tools)         │
├─────────────────────────────────────────────────────┤
│              Braintrust Observability                │
│  (Traces, evals, scoring, prompt versioning)        │
└─────────────────────────────────────────────────────┘
```

---

## Technology Mapping

Every required technology has a clear, non-contrived role:

| Technology | Role in SAGE | Why It's Needed |
|---|---|---|
| **OpenAI (GPT-4o)** | Structured data extraction — parse earnings tables, extract financial metrics from messy HTML into clean JSON | Best at reliable JSON-mode structured output |
| **Gemini (2.5 Pro)** | Long-context document analysis — ingest full 10-K filings (100K+ tokens), summarize risk factors, compare sections across years | Largest context window, great for bulk doc reasoning |
| **Claude (Sonnet 4)** | Orchestrator brain + deep reasoning — route tasks, synthesize bull/bear cases, generate the final nuanced briefing | Best at nuanced reasoning, planning, and writing |
| **Hyperbrowser** | Web search (find recent news, filings, analyst reports) + web fetch (extract full page content from URLs) | The agent's eyes on the internet |
| **E2B Sandboxes** | Run Python code safely — pull data from `yfinance`, compute financial ratios, generate matplotlib/plotly charts | Agent needs to *execute* quantitative analysis, not just talk about it |
| **Turbopuffer** | Vector storage for persistent memory — store researched company profiles, past analyses, earnings summaries for RAG retrieval | Agent should get smarter over time; don't re-research what you already know |
| **Skills** | Modular capability packages — `ResearchSkill`, `QuantAnalysisSkill`, `MemorySkill`, `ReportSkill` — each with its own system prompt, tools, and model preference | Clean separation of concerns; easy to add new capabilities |
| **MCP Tools** | Expose SAGE as an MCP server so it can be used from Claude Desktop, Cursor, or any MCP client. Also consume external MCP tools (e.g., a Postgres MCP for storing structured data) | Industry-standard interop; makes the project composable |
| **Streaming** | SSE streaming of the final briefing — user sees research happening in real-time: "Searching for NVDA earnings... Analyzing margins... Generating charts..." | Long research tasks need progressive feedback; don't make users stare at a spinner for 2 minutes |
| **Braintrust** | Trace every LLM call, tool use, and decision. Run evals on research quality. A/B test prompts. Score outputs. | Can't improve what you can't measure |

---

## Skill Definitions

### Skill 1: `ResearchSkill`
**Purpose:** Gather raw information from the web.

- **Model:** Claude Sonnet (planning what to search) + GPT-4o (structured extraction)
- **Tools:** Hyperbrowser search, Hyperbrowser web fetch
- **Flow:**
  1. Takes a research question (e.g., "NVIDIA's revenue growth last 3 years")
  2. Claude plans 3-5 search queries
  3. Executes searches via Hyperbrowser
  4. Fetches top results, extracts content
  5. GPT-4o extracts structured data (revenue numbers, dates, sources) into JSON
  6. Returns structured research bundle + raw sources

### Skill 2: `QuantAnalysisSkill`
**Purpose:** Run quantitative financial analysis with code.

- **Model:** Claude Sonnet (generating analysis code)
- **Tools:** E2B sandbox
- **Flow:**
  1. Takes structured financial data + an analysis request
  2. Claude writes Python code (pandas, matplotlib, yfinance)
  3. Executes in E2B sandbox
  4. Returns computed metrics, DataFrames, and base64-encoded charts
  5. If code errors, self-heals up to 3 retries

### Skill 3: `MemorySkill`
**Purpose:** Store and retrieve knowledge across sessions.

- **Model:** GPT-4o (generating embeddings via `text-embedding-3-small`)
- **Tools:** Turbopuffer API
- **Flow:**
  1. **Store:** After research, chunk findings → embed → upsert to Turbopuffer with metadata (company ticker, date, source, topic)
  2. **Retrieve:** Before new research, query Turbopuffer for existing knowledge on the topic
  3. **Dedup:** Skip re-researching topics where existing knowledge is < 7 days old
  4. Namespace by company ticker for clean separation

### Skill 4: `ReportSkill`
**Purpose:** Synthesize everything into a final deliverable.

- **Model:** Claude Sonnet (writing) + Gemini (if synthesizing very long source material)
- **Tools:** Streaming output
- **Flow:**
  1. Takes: research bundles, analysis results, charts, memory context
  2. Streams a structured briefing:
     - **Executive Summary** (2-3 sentences)
     - **Key Metrics** (table)
     - **Competitive Analysis** (comparison)
     - **Bull Case / Bear Case**
     - **Charts** (embedded from QuantAnalysis)
     - **Sources** (with URLs)
  3. Progressively streams each section so user sees results immediately

---

## MCP Server Design

SAGE exposes itself as an MCP server with these tools:

```python
# Tools exposed via MCP
@mcp.tool()
async def research_company(ticker: str, question: str) -> str:
    """Deep-research a company. Returns structured findings."""

@mcp.tool()
async def analyze_financials(ticker: str, metrics: list[str], period: str) -> str:
    """Run quantitative analysis. Returns metrics + charts."""

@mcp.tool()
async def get_briefing(ticker: str, focus: str) -> str:
    """Generate a full investment briefing with bull/bear cases."""

@mcp.tool()
async def recall_research(query: str) -> str:
    """Search past research from memory."""

# Resources exposed via MCP
@mcp.resource("sage://portfolio/{watchlist_name}")
async def get_watchlist(watchlist_name: str) -> str:
    """Returns saved watchlist data."""
```

This means your friend can use SAGE from Claude Desktop, Cursor, or build a web UI that talks to it.

---

## Streaming Design

Use Server-Sent Events (SSE) to stream progress + results:

```python
# Event types the client receives:
{"type": "status",   "data": "🔍 Searching for NVDA recent earnings..."}
{"type": "status",   "data": "📄 Reading Q4 2024 earnings transcript..."}
{"type": "status",   "data": "🧮 Running margin analysis in sandbox..."}
{"type": "chunk",    "data": "## Executive Summary\nNVIDIA continues to..."}
{"type": "chart",    "data": {"title": "Revenue Growth", "image": "base64..."}}
{"type": "chunk",    "data": "## Bull Case\n1. Data center demand..."}
{"type": "sources",  "data": [{"title": "...", "url": "..."}]}
{"type": "done",     "data": {"total_time": 47.2, "models_used": 3}}
```

---

## Braintrust Observability Setup

```python
import braintrust

# Wrap every LLM call
@braintrust.traced
async def call_llm(model: str, messages: list, purpose: str):
    # Routes to OpenAI / Gemini / Claude based on model string
    ...

# Log structured evaluations
braintrust.log(
    input={"query": "NVDA competitive analysis"},
    output=briefing_text,
    scores={
        "factual_accuracy": auto_score_with_citations(briefing_text, sources),
        "completeness": check_all_sections_present(briefing_text),
        "chart_quality": validate_charts_generated(charts),
    },
    metadata={
        "models_used": ["claude-sonnet", "gpt-4o", "gemini-pro"],
        "total_latency_ms": 47200,
        "num_searches": 5,
        "sandbox_retries": 1,
    }
)
```

**Eval suite ideas:**
- "Given this earnings transcript, does the agent extract the correct EPS?"
- "Does the bull/bear case cite specific numbers from the research?"
- "Does the agent reuse memory instead of re-searching known data?"

---

## Two-Week Build Plan

### Week 1: Foundation

| Day | Focus | Deliverable |
|---|---|---|
| **1** | Project setup, env config | Repo scaffolded, all API keys working, basic CLI that calls each API once |
| **2** | `ResearchSkill` v1 | Hyperbrowser search + fetch working. Can search for a company and extract article text |
| **3** | `QuantAnalysisSkill` v1 | E2B sandbox working. Can execute Python code, return chart images. Test with yfinance |
| **4** | `MemorySkill` v1 | Turbopuffer integration. Store embeddings, retrieve with similarity search. Namespace by ticker |
| **5** | Multi-model routing | Router that picks Claude/GPT-4o/Gemini based on task type. All three APIs working |
| **6-7** | Integration | Wire skills together. First end-to-end flow: query → research → analyze → store → report (no streaming yet) |

### Week 2: Polish & Production

| Day | Focus | Deliverable |
|---|---|---|
| **8** | Streaming | SSE streaming for the report. Progressive status updates during research |
| **9** | MCP Server | Expose SAGE as MCP tools. Test from Claude Desktop or MCP Inspector |
| **10** | Braintrust | Add tracing to all LLM calls. Build 3-5 eval cases. Dashboard showing traces |
| **11** | `ReportSkill` polish | Better formatting, inline charts, citation links, bull/bear structure |
| **12** | Memory intelligence | Dedup logic, freshness checks, "what do I already know?" before researching |
| **13** | Error handling & retries | Sandbox self-healing, search fallbacks, graceful degradation if one model is down |
| **14** | Demo day prep | Record demo video, write README, clean up code, run full eval suite |

---

## Example Interaction

```
User: What's the investment case for Palantir right now?

SAGE: 🔍 Checking what I already know about PLTR...
      📚 Found 3 past research notes (last updated 12 days ago — refreshing)
      🔍 Searching: "Palantir Q4 2025 earnings results"
      🔍 Searching: "Palantir government contracts 2025"
      🔍 Searching: "Palantir AIP commercial growth"
      📄 Reading earnings transcript from palantir.com...
      📄 Reading analyst coverage from seekingalpha...
      🧮 Spinning up sandbox — computing revenue growth, margins, valuation multiples...
      📊 Generated 3 charts

      ## Executive Summary
      Palantir reported Q4 revenue of $X.XXB, up XX% YoY, driven by accelerating
      AIP platform adoption in commercial markets...

      ## Key Metrics
      | Metric           | Q4 2025  | Q4 2024  | Change |
      |-----------------|----------|----------|--------|
      | Revenue          | $X.XXB   | $X.XXB   | +XX%   |
      | Adj. Op. Margin  | XX%      | XX%      | +Xpp   |
      | Commercial Rev   | $XXXM    | $XXXM    | +XX%   |
      | Gov Rev          | $XXXM    | $XXXM    | +XX%   |

      ## 📈 Bull Case
      1. AIP is creating a new category — commercial revenue is inflecting...
      2. Government contracts provide durable base revenue...
      3. Rule of 40 score of XX suggests efficient growth...

      ## 📉 Bear Case
      1. Valuation at XXx forward revenue assumes perfection...
      2. Customer concentration risk remains...
      3. Stock-based compensation dilution of X%...

      ## Charts
      [Revenue Growth Chart] [Margin Expansion Chart] [Valuation Comp Chart]

      ## Sources
      1. Palantir Q4 2025 Earnings Release — palantir.com
      2. ...
```

---

## Stretch Goals (If She Finishes Early)

- **Watchlist monitoring:** Cron job that checks news for a list of tickers daily, alerts on material events
- **Multi-agent debate:** Spawn a "bull agent" and "bear agent" that argue, then a "judge agent" synthesizes
- **Portfolio analysis:** Upload a portfolio CSV, SAGE analyzes concentration risk, sector exposure, and correlation
- **Voice interface:** Integrate with a TTS API so SAGE can deliver audio briefings
- **Web UI:** Simple Next.js frontend with streaming display (great excuse to learn Vercel AI SDK)

---

## Key Learning Outcomes

By building SAGE, she will have hands-on experience with:

1. **Agent architecture** — orchestrator pattern, skill-based decomposition, tool routing
2. **Multi-model systems** — when to use which LLM and why (not just "pick the best one")
3. **Web-grounded agents** — search, fetch, extract, and reason over live web data
4. **Code-executing agents** — safe sandboxed execution with self-healing retries
5. **RAG + vector memory** — embeddings, similarity search, namespace management, freshness
6. **MCP protocol** — building both an MCP server (exposing tools) and consuming MCP tools
7. **Streaming UX** — progressive rendering, status events, real-time feedback
8. **Observability** — tracing, evals, scoring, debugging multi-step agent flows
9. **Production patterns** — error handling, retries, fallbacks, rate limiting, cost tracking

This project touches every major component of the modern agent stack, but each piece has a genuine reason to exist — nothing is bolted on for show.
