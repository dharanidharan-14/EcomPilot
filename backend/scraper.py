import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import json
import logging

logger = logging.getLogger("ecommerce_agent.scraper")

class UniversalScraper:
    def __init__(self):
        self.browser = None
        self.context = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_reviews(self, url: str, limit: int = 50):
        page = await self.context.new_page()
        try:
            # Use 'domcontentloaded' instead of 'networkidle' for better stability on heavy sites
            # and increase timeout to 90 seconds.
            logger.info(f"Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            
            # Allow some time for essential JS to run
            await asyncio.sleep(5)
            
            # Simple infinite scroll handling
            for _ in range(2):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Semantic detection logic:
            # 1. Look for text blocks that look like reviews (min length, contains certain patterns)
            # 2. Look for star ratings (1-5, often in aria-labels or title tags)
            # 3. Look for elements that repeat similar structures
            
            reviews = []
            
            # 1. Try to find common review containers first
            common_selectors = [
                'review-text-content', 't-w1Y2', 'review-text', 'comment-text', 
                'customer-review-text', 'user-review-content', 'cvf-review-text'
            ]
            
            for selector in common_selectors:
                elements = soup.find_all(class_=re.compile(selector, re.I))
                for el in elements:
                    text = el.get_text(strip=True)
                    if 30 < len(text) < 1500:
                        reviews.append(text)

            # 2. Heuristic fallback: Find elements with siblings that look like reviews
            if len(reviews) < 5:
                potential_review_elements = soup.find_all(['p', 'div', 'span'], text=True)
                for element in potential_review_elements:
                    text = element.get_text(strip=True)
                    # Tighten constraints: must be long enough and not too long
                    if 60 < len(text) < 800:
                        # Skip common nav/footer text keywords
                        ignore_keywords = ["shipping", "privacy", "policy", "terms", "contact", "about us", "cookie", "copyright", "home", "search"]
                        if any(kw in text.lower() for kw in ignore_keywords):
                            continue
                            
                        # Check if it's likely a review based on repeated siblings
                        parent = element.parent
                        if parent:
                            siblings = parent.find_all(element.name, recursive=False)
                            if len(siblings) >= 3:
                                reviews.append(text)
            
            # Deduplicate and sort by length (longer reviews often have more detail)
            reviews = list(set(reviews))
            reviews.sort(key=len, reverse=True)
            reviews = reviews[:limit]
            
            # Extract product title
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Unknown Product"
            if title == "Unknown Product" and soup.find('title'):
                title = soup.find('title').get_text(strip=True).split('|')[0].split(':')[0].strip()
            
            return {
                "product_name": title,
                "platform": "Detected Platform",
                "reviews": reviews
            }
        except Exception as e:
            print(f"Scraping error: {e}")
            return {"error": str(e)}
        finally:
            await page.close()

async def test_scraper():
    scraper = UniversalScraper()
    await scraper.start()
    result = await scraper.scrape_reviews("https://www.amazon.in/dp/B0CXMC2H2R") # Example URL
    print(json.dumps(result, indent=2))
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(test_scraper())
