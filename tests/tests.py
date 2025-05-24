# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="")

response = app.scrape_url(
    url="firecrawl.dev/",
    params={
        "formats": ["markdown"],
    },
)
