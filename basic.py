from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from tools.hb import search, web_fetch

load_dotenv()

ant = AsyncAnthropic()

async def main():
    response = await ant.messages.create(
        system="QINYU FILL OUT",
        messages=[{"role": "user", "content": "Do a comprehensive research on NVDA stock and make a buy/sell recommendation along with an equity research style report. "}],
        tools=[
            {
                "type": "custom", 
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The query to search for"}
                    }
                },
                "name": "search",
                "description": "Search the web for information",
            }, 
            {
                "type": "custom",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to fetch"}
                    }
                },
                "name": "web_fetch",
                "description": "Fetch the content of a web page",
            }
        ],
        model="claude-sonnet-4-6",
        max_tokens=1024,
    )

    print(response.model_dump_json(indent=2))
