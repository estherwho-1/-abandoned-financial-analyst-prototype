"""Server-Sent Events (SSE) streaming for real-time progress updates."""
import json
import asyncio
from typing import AsyncIterator, Literal
from dataclasses import dataclass, asdict


@dataclass
class StreamEvent:
    """A streaming event."""
    type: Literal["status", "chunk", "chart", "sources", "done", "error"]
    data: dict | str | list
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        if isinstance(self.data, (dict, list)):
            data_str = json.dumps(self.data)
        else:
            data_str = str(self.data)
        
        return f"event: {self.type}\ndata: {data_str}\n\n"


class StreamManager:
    """Manages streaming events for SAGE operations."""
    
    def __init__(self):
        self.events: list[StreamEvent] = []
        self._callbacks: list = []
    
    def on_event(self, callback):
        """Register a callback for new events."""
        self._callbacks.append(callback)
    
    async def emit(self, event: StreamEvent):
        """Emit a streaming event."""
        self.events.append(event)
        
        # Call all registered callbacks
        for callback in self._callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
    
    async def status(self, message: str, emoji: str = "⚙️"):
        """Emit a status update."""
        await self.emit(StreamEvent(
            type="status",
            data=f"{emoji} {message}"
        ))
    
    async def chunk(self, text: str):
        """Emit a text chunk for the final report."""
        await self.emit(StreamEvent(
            type="chunk",
            data=text
        ))
    
    async def chart(self, title: str, image_base64: str, description: str = ""):
        """Emit a chart."""
        await self.emit(StreamEvent(
            type="chart",
            data={
                "title": title,
                "image": image_base64,
                "description": description,
            }
        ))
    
    async def sources(self, sources: list[dict]):
        """
        Emit source citations.
        
        Args:
            sources: List of dicts with keys: title, url, date (optional)
        """
        await self.emit(StreamEvent(
            type="sources",
            data=sources
        ))
    
    async def done(self, metadata: dict):
        """
        Emit completion event.
        
        Args:
            metadata: Dict with total_time, models_used, etc.
        """
        await self.emit(StreamEvent(
            type="done",
            data=metadata
        ))
    
    async def error(self, message: str, details: dict | None = None):
        """Emit an error."""
        await self.emit(StreamEvent(
            type="error",
            data={"message": message, "details": details or {}}
        ))
    
    async def stream_events(self) -> AsyncIterator[str]:
        """Stream all events as SSE format."""
        for event in self.events:
            yield event.to_sse()
    
    def print_console(self):
        """Print all events to console (for CLI mode)."""
        from rich.console import Console
        from rich.markdown import Markdown
        
        console = Console()
        
        for event in self.events:
            if event.type == "status":
                console.print(f"[cyan]{event.data}[/cyan]")
            
            elif event.type == "chunk":
                # Render markdown chunks
                try:
                    console.print(Markdown(str(event.data)))
                except:
                    console.print(event.data)
            
            elif event.type == "chart":
                console.print(f"[green]📊 Chart: {event.data['title']}[/green]")
                if event.data.get('description'):
                    console.print(f"   {event.data['description']}")
            
            elif event.type == "sources":
                console.print("\n[yellow]📚 Sources:[/yellow]")
                for i, source in enumerate(event.data, 1):
                    console.print(f"   {i}. {source['title']} - {source['url']}")
            
            elif event.type == "done":
                console.print(f"\n[green]✅ Completed in {event.data.get('total_time', 0):.1f}s[/green]")
                console.print(f"   Models used: {', '.join(event.data.get('models_used', []))}")
            
            elif event.type == "error":
                console.print(f"[red]❌ Error: {event.data['message']}[/red]")
