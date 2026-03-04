#!/usr/bin/env python3
"""
SAGE - Strategic Analyst & Guided Equity-researcher
Main CLI entry point
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import Orchestrator
from config.config import config


async def main():
    """Main CLI entry point."""
    # # Parse arguments
    # if len(sys.argv) < 2:
    #     print("Usage: python main.py 'Your research question'")
    #     print("Example: python main.py 'What is NVIDIA competitive position in AI chips?'")
    #     sys.exit(1)
    
    # query = " ".join(sys.argv[1:])
    query = """
    NVDA competitive analysis, financials, and market position.
    """
    
    # Check configuration
    if not config.is_mock_mode():
        missing = config.validate_production()
        if missing:
            print("⚠️  Missing API keys for production mode:")
            for key in missing:
                print(f"  - {key}")
            print("\nRunning in MOCK mode instead.")
            print("To use real APIs, add keys to config/.env\n")
    
    # Run SAGE
    print(f"\n{'='*60}")
    print(f"🏦 SAGE - Strategic Analyst & Guided Equity-researcher")
    print(f"{'='*60}")
    print(f"Mode: {'MOCK' if config.is_mock_mode() else 'PRODUCTION'}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    # Create orchestrator
    orchestrator = Orchestrator()
    stream = orchestrator.get_stream()

    # Print events to console in real-time as they are emitted
    stream.on_event(stream.print_event)

    # Execute query
    result = await orchestrator.execute(query)
    
    print("\n" + "="*60)
    print("✅ Analysis complete!")
    print(f"Total time: {result.metadata['total_time']:.1f}s")
    print(f"Models used: {', '.join(result.metadata['models_used'])}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
