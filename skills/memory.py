"""MemorySkill - Vector storage and retrieval for persistent knowledge."""
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel
from core.models import ModelClient, Message
from core.streaming import StreamManager
from config.config import config


class MemoryEntry(BaseModel):
    """A stored memory entry."""
    id: str
    content: str
    metadata: dict
    timestamp: datetime
    embedding: list[float] | None = None


class MemoryResult(BaseModel):
    """Results from memory retrieval."""
    query: str
    results: list[dict]  # List of {content, metadata, score}
    freshness_check: str  # "fresh", "stale", or "none"


class MemorySkill:
    """
    Stores and retrieves knowledge using vector embeddings.
    
    Flow:
    1. Before research: Check what we already know
    2. After research: Store new findings
    3. Dedup: Skip re-researching recent topics
    
    Uses Turbopuffer for vector storage.
    """
    
    def __init__(self, model_client: ModelClient, stream: StreamManager):
        self.model = model_client
        self.stream = stream
        self.is_mock = config.is_mock_mode()
        self.memory_store = {}  # Mock in-memory storage
    
    async def recall(
        self,
        query: str,
        namespace: str = "default",
        max_age_days: int = 7,
    ) -> MemoryResult:
        """
        Retrieve relevant memories for a query.
        
        Args:
            query: What to search for
            namespace: Namespace to search (e.g., ticker symbol)
            max_age_days: Consider memories older than this "stale"
        
        Returns:
            MemoryResult with retrieved memories and freshness info
        """
        await self.stream.status(f"Checking memory for: {query}", "🧠")
        
        if self.is_mock:
            results = await self._mock_recall(query, namespace)
        else:
            results = await self._turbopuffer_recall(query, namespace)
        
        # Check freshness
        freshness = self._check_freshness(results, max_age_days)
        
        return MemoryResult(
            query=query,
            results=results,
            freshness_check=freshness,
        )
    
    async def store(
        self,
        content: str,
        metadata: dict,
        namespace: str = "default",
    ):
        """
        Store a new memory.
        
        Args:
            content: The content to store
            metadata: Metadata (ticker, topic, source, etc.)
            namespace: Namespace (e.g., ticker symbol)
        """
        await self.stream.status(f"Storing memory in namespace: {namespace}", "💾")
        
        # Generate embedding
        if self.is_mock:
            await self._mock_store(content, metadata, namespace)
        else:
            await self._turbopuffer_store(content, metadata, namespace)
    
    async def _mock_recall(self, query: str, namespace: str) -> list[dict]:
        """Mock memory retrieval."""
        # Return some mock results if they exist
        if namespace in self.memory_store:
            return [
                {
                    "content": entry["content"],
                    "metadata": entry["metadata"],
                    "score": 0.85,
                    "timestamp": entry["timestamp"],
                }
                for entry in self.memory_store[namespace][:3]
            ]
        
        # Return empty if no memories
        return []
    
    async def _mock_store(self, content: str, metadata: dict, namespace: str):
        """Mock memory storage."""
        if namespace not in self.memory_store:
            self.memory_store[namespace] = []
        
        entry = {
            "id": hashlib.md5(content.encode()).hexdigest()[:16],
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.memory_store[namespace].append(entry)
    
    async def _turbopuffer_recall(self, query: str, namespace: str) -> list[dict]:
        """Real Turbopuffer retrieval."""
        # Implementation would use Turbopuffer API
        raise NotImplementedError("Add TURBOPUFFER_API_KEY to use real memory")
    
    async def _turbopuffer_store(self, content: str, metadata: dict, namespace: str):
        """Real Turbopuffer storage."""
        # Implementation would use Turbopuffer API
        raise NotImplementedError("Add TURBOPUFFER_API_KEY to use real memory")
    
    def _check_freshness(self, results: list[dict], max_age_days: int) -> str:
        """Check if memories are fresh or stale."""
        if not results:
            return "none"
        
        # Get most recent result
        most_recent = max(results, key=lambda r: r.get("timestamp", ""))
        timestamp_str = most_recent.get("timestamp", "")
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age = datetime.now() - timestamp.replace(tzinfo=None)
            
            if age < timedelta(days=max_age_days):
                return "fresh"
            else:
                return "stale"
        except:
            return "unknown"
    
    async def should_skip_research(
        self,
        query: str,
        namespace: str = "default",
    ) -> tuple[bool, str]:
        """
        Determine if we can skip research based on existing memories.
        
        Returns:
            (should_skip, reason)
        """
        memory_result = await self.recall(query, namespace, max_age_days=7)
        
        if memory_result.freshness_check == "fresh" and memory_result.results:
            return True, f"Found fresh research from {len(memory_result.results)} memories (< 7 days old)"
        
        return False, "No fresh memories found, proceeding with research"
