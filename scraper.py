import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from models import Headline, ArticleDetail, LiveTV
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://3news.com"

async def get_soup(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            # Increase timeout for slow pages
            await page.goto(url, wait_until="networkidle", timeout=60000)
            # Wait for articles or some content to load
            await page.wait_for_selector("article, .post-item, section.bg-white", timeout=10000)
        except Exception as e:
            print(f"Playwright wait error for {url}: {e}")
            
        content = await page.content()
        await browser.close()
        return BeautifulSoup(content, "html.parser")

async def scrub_headlines(category: str) -> List[Headline]:
    url = f"{BASE_URL}/news/{category.lower()}" if category.upper() != "HOME" else BASE_URL
    if category.upper() == "ELECTIONS":
        url = f"{BASE_URL}/elections"
    
    try:
        soup = await get_soup(url)
        headlines = []
        
        # Standard scraping on rendered HTML
        articles = soup.select("article") or soup.select(".post-item") or soup.select("section.bg-white article")
        
        for idx, article in enumerate(articles):
            # Try multiple selectors for title/link
            title_tag = (
                article.select_one("h2 a") or 
                article.select_one("h3 a") or
                article.select_one("h4 a") or
                article.select_one(".entry-title a") or 
                article.select_one("a.post-title") or
                article.select_one("a[href*='/news/']")
            )
            if not title_tag:
                continue
                
            topic = title_tag.get_text(strip=True) or title_tag.get("title") or ""
            # If topic is generic, try to find a better one
            if not topic or topic.upper() in ["NEWS", "READ MORE", "LATEST", "POLITICS", "SPORTS", "BUSINESS", "ENTERTAINMENT"]:
                parent_h = article.select_one("h2") or article.select_one("h3") or article.select_one("h4")
                if parent_h:
                    topic = parent_h.get_text(strip=True)
            
            link = title_tag.get("href") or ""
            if not link:
                continue
            if not link.startswith("http"):
                link = f"{BASE_URL}{link}"
            
            # If topic is still generic, skip it
            if topic.upper() in ["NEWS", "READ MORE", "LATEST"]:
                continue
                
            # Improved image selection
            # New structure: article a div img
            img_tags = article.select("img")
            images = []
            for img in img_tags:
                src = img.get("data-src") or img.get("src") or img.get("srcset")
                if src and not src.startswith("data:"):
                    # If it's a srcset, take the first URL
                    if "," in src:
                        src = src.split(",")[0].split(" ")[0]
                    if not src.startswith("http"):
                        src = f"{BASE_URL}{src}"
                    images.append(src)
            
            # Categories
            cat_tags = article.select(".category") or article.select(".post-categories a") or article.select(".entry-meta .cat-links a")
            categories = [cat.get_text(strip=True) for cat in cat_tags]
            if not categories and "/news/" in link:
                # Infer category from URL if missing
                parts = link.split("/")
                if len(parts) > 4:
                    categories = [parts[4].capitalize()]
            
            headlines.append(Headline(
                topic=topic,
                images=list(set(images)), # Unique images
                categories=categories,
                isLatest=(idx == 0),
                url=link,
                route=link.replace(BASE_URL, "") if link.startswith(BASE_URL) else link
            ))
            
        return headlines
    except Exception as e:
        print(f"Error scrubbing headlines for {category}: {e}")
        return []

async def scrub_article_detail(url: str) -> Optional[ArticleDetail]:
    try:
        soup = await get_soup(url)
        
        title_tag = soup.select_one("h1.entry-title") or soup.select_one("h1")
        topic = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        # Improved image selection for article detail
        img_tags = soup.select("article img") + soup.select(".article-content img")
        images = []
        for img in img_tags:
            src = img.get("data-src") or img.get("src")
            if src and not src.startswith("data:"):
                # Filter out common UI badges/icons
                if any(x in src.lower() for x in ["badge", "icon", "logo", "gravatar", "preferred_source"]):
                    continue
                    
                # Extract original URL from Next.js image proxy if present
                if "/_next/image?url=" in src:
                    from urllib.parse import urlparse, parse_qs, unquote
                    parsed = urlparse(src)
                    query = parse_qs(parsed.query)
                    if "url" in query:
                        src = unquote(query["url"][0])
                
                if not src.startswith("http"):
                    src = f"{BASE_URL}{src}"
                images.append(src)
        
        # Improved category and tag selection
        cat_tags = soup.select("nav[aria-label='Breadcrumb'] ol li a") or soup.select(".md:mb-8 a[href*='/tag/']") or soup.select(".post-categories a") or soup.select(".breadcrumb a")
        categories = list(set([cat.get_text(strip=True) for cat in cat_tags if cat.get_text(strip=True) and cat.get_text(strip=True).upper() not in ["HOME", "3NEWS", "LATEST POSTS"]]))
        
        # Improved content selection
        content_divs = soup.select(".article-content") or soup.select(".entry-content") or soup.select(".post-content")
        descriptions = []
        for div in content_divs:
            descriptions.extend([p.get_text(strip=True) for p in div.select("p") if p.get_text(strip=True)])
            
        return ArticleDetail(
            topic=topic,
            images=list(set(images)),
            categories=categories,
            descriptions=descriptions,
            url=url
        )
    except Exception as e:
        print(f"Error scrubbing article detail for {url}: {e}")
        return None

async def scrub_live_tv() -> Optional[LiveTV]:
    url = f"{BASE_URL}/live/3news24"
    try:
        soup = await get_soup(url)
        # Look for YouTube iframe or other video sources
        iframes = soup.select("iframe")
        video_url = "No live stream found"
        for iframe in iframes:
            src = iframe.get("src", "")
            if "youtube.com/embed" in src or "facebook.com/plugins/video.php" in src:
                video_url = src
                break
        
        # Fallback to the first iframe if no specific one found and it's not a common ad
        if video_url == "No live stream found" and iframes:
            for iframe in iframes:
                src = iframe.get("src", "")
                if src and "googleads" not in src and "doubleclick" not in src:
                    video_url = src
                    break
        
        return LiveTV(
            video_url=video_url,
            title="3News Live TV"
        )
    except Exception as e:
        print(f"Error scrubbing live TV: {e}")
        return None

async def scrub_cartoons() -> List[Headline]:
    # Dedicated cartoon category
    url = f"{BASE_URL}/opinion/cartoon/"
    try:
        soup = await get_soup(url)
        headlines = []
        # The structure on the cartoon page might be different
        articles = soup.select("article") or soup.select(".post-item") or soup.select(".td-block-span6")
        
        for idx, article in enumerate(articles):
            title_tag = (
                article.select_one(".entry-title a") or 
                article.select_one("h2 a") or 
                article.select_one("h3 a") or
                article.select_one("a[href*='/opinion/cartoon/']")
            )
            if not title_tag:
                continue
                
            topic = title_tag.get_text(strip=True)
            link = title_tag.get("href")
            if not link.startswith("http"):
                link = f"{BASE_URL}{link}"
            
            img_tags = article.select("img")
            images = []
            for img in img_tags:
                src = img.get("data-src") or img.get("src")
                if src and not src.startswith("data:"):
                    if not src.startswith("http"):
                        src = f"{BASE_URL}{src}"
                    images.append(src)
            
            headlines.append(Headline(
                topic=topic,
                images=list(set(images)),
                categories=["Cartoons", "Tilapia Corner"],
                isLatest=(idx == 0),
                url=link,
                route=link.replace(BASE_URL, "") if link.startswith(BASE_URL) else link
            ))
        return headlines
    except Exception as e:
        print(f"Error scrubbing cartoons: {e}")
        return []

async def scrub_popular() -> List[Headline]:
    url = BASE_URL
    try:
        soup = await get_soup(url)
        headlines = []
        
        # Based on browser research, popular articles are in a sidebar with "Popular Today 24h"
        # They are within article tags inside a div.p-4.space-y-4
        
        # Find the container by class or proximity to heading
        container = soup.select_one("div.p-4.space-y-4")
        if not container:
            # Fallback: look for heading and find sibling container
            popular_heading = soup.find(lambda tag: tag.name in ["h3", "h2", "div"] and "Popular Today" in tag.get_text())
            if popular_heading:
                parent = popular_heading.find_parent("div")
                if parent:
                    container = parent.find_next_sibling("div")
        
        if not container:
            return []
            
        articles = container.select("article")
        
        for idx, article in enumerate(articles):
            # Each popular article has a number div
            number_div = article.select_one("div.shrink-0")
            if not number_div or not number_div.get_text(strip=True).isdigit():
                continue
                
            title_tag = article.select_one("h4")
            link_tag = article.select_one("a.block")
            
            if not title_tag or not link_tag:
                continue
                
            topic = title_tag.get_text(strip=True)
            link = link_tag.get("href")
            if not link:
                continue
            if not link.startswith("http"):
                link = f"{BASE_URL}{link}"
                
            headlines.append(Headline(
                topic=topic,
                images=[], # Sidebar list doesn't have images
                categories=["Popular"],
                isLatest=(idx == 0),
                url=link,
                route=link.replace(BASE_URL, "") if link.startswith(BASE_URL) else link
            ))
            
        return headlines
    except Exception as e:
        print(f"Error scrubbing popular: {e}")
        return []
