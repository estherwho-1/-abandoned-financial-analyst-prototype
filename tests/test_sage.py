#!/usr/bin/env python3
"""
SAGE Test Suite
Tests all components in mock mode (no API keys required).

To test individual services in production mode, set per-service flags:
  MOCK_LLM=false .venv/bin/python tests/test_sage.py      # real LLM calls
  MOCK_SEARCH=false .venv/bin/python tests/test_sage.py    # real Hyperbrowser
  MOCK_E2B=false .venv/bin/python tests/test_sage.py       # real E2B sandbox
  MOCK_MEMORY=false .venv/bin/python tests/test_sage.py    # real Turbopuffer
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import Orchestrator
from core.models import ModelClient, Message
from core.streaming import StreamManager
from skills.research import ResearchSkill
from skills.quant_analysis import QuantAnalysisSkill
from skills.memory import MemorySkill
from skills.report import ReportSkill


async def test_model_client():
    """Test multi-model client."""
    print("\n🧪 Testing Model Client...")
    
    client = ModelClient()
    
    # Test orchestrator model (Claude)
    result = await client.complete(
        messages=[Message(role="user", content="What is 2+2?")],
        model="orchestrator",
    )
    print(f"  ✅ Orchestrator model: {result.model}")
    
    # Test extractor model (GPT-4o)
    result = await client.complete(
        messages=[Message(role="user", content="Extract data")],
        model="extractor",
    )
    print(f"  ✅ Extractor model: {result.model}")
    
    print("  ✅ Model client working\n")


async def test_research_skill():
    """Test research skill."""
    print("🧪 Testing Research Skill...")
    
    client = ModelClient()
    stream = StreamManager()
    research = ResearchSkill(client, stream)
    
    result = await research.research("NVIDIA revenue growth")
    
    print(f"  ✅ Found {len(result.findings)} findings")
    print(f"  ✅ Found {len(result.raw_sources)} sources")
    if result.extracted_data:
        print(f"  ✅ Extracted {len(result.extracted_data)} metrics")
    
    print("  ✅ Research skill working\n")


async def test_quant_skill():
    """Test quantitative analysis skill."""
    print("🧪 Testing Quant Analysis Skill...")
    
    client = ModelClient()
    stream = StreamManager()
    quant = QuantAnalysisSkill(client, stream)
    
    result = await quant.analyze(
        data={"revenue": "$18.1B", "growth": "45%"},
        analysis_request="Calculate revenue metrics",
    )
    
    print(f"  ✅ Computed {len(result.metrics)} metrics")
    print(f"  ✅ Generated {len(result.charts)} charts")
    print(f"  ✅ Executed code ({len(result.code_executed)} chars)")
    
    print("  ✅ Quant analysis skill working\n")


async def test_memory_skill():
    """Test memory skill."""
    print("🧪 Testing Memory Skill...")
    
    client = ModelClient()
    stream = StreamManager()
    memory = MemorySkill(client, stream)
    
    # Store memory
    await memory.store(
        content="NVIDIA Q4 revenue was $18.1B",
        metadata={"ticker": "NVDA", "topic": "earnings"},
        namespace="NVDA",
    )
    print("  ✅ Stored memory")
    
    # Recall memory
    result = await memory.recall("NVIDIA revenue", namespace="NVDA")
    print(f"  ✅ Recalled {len(result.results)} memories")
    
    print("  ✅ Memory skill working\n")


async def test_report_skill():
    """Test report generation skill."""
    print("🧪 Testing Report Skill...")
    
    client = ModelClient()
    stream = StreamManager()
    report = ReportSkill(client, stream)
    
    # Mock research results
    class MockResearch:
        findings = [{"fact": "Revenue grew 45%", "source": "example.com"}]
        raw_sources = [{"title": "Test", "url": "example.com"}]
        extracted_data = {"revenue": "$18.1B"}
    
    # Mock analysis results
    class MockAnalysis:
        metrics = {"cagr": 42.3, "margin": 68.2}
        charts = []
    
    result = await report.generate(
        query="NVIDIA analysis",
        research_results=MockResearch(),
        analysis_results=MockAnalysis(),
    )
    
    print(f"  ✅ Generated report with {len(result.sections)} sections")
    print(f"  ✅ Executive summary: {result.executive_summary[:50]}...")
    
    print("  ✅ Report skill working\n")


async def test_full_orchestration():
    """Test full end-to-end orchestration."""
    print("🧪 Testing Full Orchestration (End-to-End)...")
    
    orchestrator = Orchestrator()
    
    result = await orchestrator.execute(
        query="What is NVIDIA's competitive position in AI chips?",
        namespace="NVDA",
    )
    
    print(f"  ✅ Query: {result.query}")
    print(f"  ✅ Total time: {result.metadata['total_time']:.2f}s")
    print(f"  ✅ Models used: {', '.join(result.metadata['models_used'])}")
    
    # Print streamed events
    stream = orchestrator.get_stream()
    print(f"  ✅ Generated {len(stream.events)} stream events")
    
    print("  ✅ Full orchestration working\n")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("🏦 SAGE Test Suite (Mock Mode)")
    print("="*60)
    
    try:
        await test_model_client()
        await test_research_skill()
        await test_quant_skill()
        await test_memory_skill()
        await test_report_skill()
        await test_full_orchestration()
        
        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSAGE is working in MOCK mode!")
        print("Add API keys to config/.env to use production mode.\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
