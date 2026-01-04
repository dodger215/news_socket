import asyncio
from scraper import get_soup
import sys

async def main():
    url = "https://3news.com/news/politics/some-views-may-be-extreme-but-they-are-permissible-in-a-democracy-edudzi-on-call-for-3rd-term-for-mahama"
    soup = await get_soup(url)
    with open("article_dump.html", "w") as f:
        f.write(soup.prettify())
    print("Dumped HTML to article_dump.html")

if __name__ == "__main__":
    asyncio.run(main())
