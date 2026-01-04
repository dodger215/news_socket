import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://3news.com/?s=Tilapia+Corner", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        # Find all links containing Tilapia Corner
        links = await page.query_selector_all("a")
        for link in links:
            text = await link.inner_text()
            if "Tilapia Corner" in text:
                href = await link.get_attribute("href")
                print(f"Found link: {text} -> {href}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
