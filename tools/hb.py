from dotenv import load_dotenv
from hyperbrowser import AsyncHyperbrowser
from hyperbrowser.models import FetchParams, WebSearchParams

load_dotenv()

_client = AsyncHyperbrowser()

async def search(query: str):
    resp = await _client.web.search(WebSearchParams(query=query))
    return str(resp.data.results)

async def web_fetch(url: str):
    resp = await _client.web.fetch(FetchParams(url=url, stealth="auto", outputs=["markdown"]))
    return resp.data.markdown or f"Failed to fetch {url}"
