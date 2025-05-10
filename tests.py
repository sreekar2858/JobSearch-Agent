# Install with pip install firecrawl-py
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key='fc-8016efbf69b04b92a8f7e797e76506f3')

response = app.scrape_url(url='firecrawl.dev/', params={
	'formats': [ 'markdown' ],
})