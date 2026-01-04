import asyncio
from scraper import scrub_article_detail
import json

async def main():
    url = "https://3news.com/news/politics/some-views-may-be-extreme-but-they-are-permissible-in-a-democracy-edudzi-on-call-for-3rd-term-for-mahama"
    print(f"--- Testing Article Detail for {url} ---")
    detail = await scrub_article_detail(url)
    if detail:
        print(json.dumps(detail.model_dump(), indent=2))
    else:
        print("Failed to scrub article detail.")

if __name__ == "__main__":
    asyncio.run(main())
