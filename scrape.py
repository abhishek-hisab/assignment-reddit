"""
REDDIT SELENIUM SCRAPER - NOT RECOMMENDED
This violates Reddit's Terms of Service and is provided for educational purposes only.
Use the official Reddit API instead.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
import json
from typing import List, Dict, Any
from datetime import datetime
from comments import CommentScraper

class RedditSeleniumScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Initialize Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Essential options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
        
        return self.driver
    
    def extract_username_from_url(self, profile_url: str) -> str:
        """Extract username from Reddit profile URL"""
        patterns = [
            r'reddit\.com/u/([^/?]+)',
            r'reddit\.com/user/([^/?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, profile_url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid Reddit profile URL")
    
    def wait_and_scroll(self, scrolls: int = 8):
        """Scroll page to load more content with better timing"""
        for i in range(scrolls):
            print(f"Scrolling... {i+1}/{scrolls}")
            
            # Get current page height
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(3)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == current_height:
                print("No new content loaded, stopping scroll")
                break
    
    def scrape_posts(self, username: str) -> List[Dict[str, Any]]:
        """Scrape user posts from their profile"""
        posts = []
        url = f"https://www.reddit.com/user/{username}/submitted/"
        
        try:
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load and accept any cookies/popups
            time.sleep(3)
            
            # Try to dismiss any popups
            self.dismiss_popups()
            
            # Wait for posts to load - using more specific selectors
            try:
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "shreddit-post")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='post-container']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='post-container']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-click-id='body']"))
                    )
                )
                print("Posts loaded successfully")
            except TimeoutException:
                print("Timeout waiting for posts to load")
                # Try to check if we're on the right page
                current_url = self.driver.current_url
                page_source_snippet = self.driver.page_source[:500]
                print(f"Current URL: {current_url}")
                print(f"Page source snippet: {page_source_snippet}")
                return posts
            
            # Scroll to load more content
            self.wait_and_scroll(6)
            
            # Updated selectors based on current Reddit structure
            post_selectors = [
                "shreddit-post",
                "article[data-testid='post-container']",
                "[data-testid='post-container']",
                "div[data-click-id='body']",
                ".Post",
                "[data-adclicklocation='title']"
            ]
            
            post_elements = []
            for selector in post_selectors:
                try:
                    post_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if post_elements:
                        print(f"Found {len(post_elements)} posts using selector: {selector}")
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not post_elements:
                print("No post elements found. Trying fallback approach...")
                # Fallback: try to find any links that might be posts
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/comments/']")
                print(f"Found {len(post_elements)} post links as fallback")
            
            # Extract data from each post
            for i, element in enumerate(post_elements[:7]):
                try:
                    post_data = self.extract_post_data(element, i)
                    if post_data and post_data.get('title'):
                        posts.append(post_data)
                        print(f"✓ Extracted post {i+1}: {post_data['title'][:60]}...")
                    else:
                        print(f"✗ Failed to extract post {i+1}")
                except Exception as e:
                    print(f"✗ Error extracting post {i+1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error scraping posts: {e}")
            import traceback
            traceback.print_exc()
        
        return posts
    
    def dismiss_popups(self):
        """Try to dismiss common Reddit popups"""
        popup_selectors = [
            "button[aria-label='Close']",
            "button[data-testid='close-button']",
            "button:contains('Continue')",
            "button:contains('Accept')",
            ".icon-close",
            "[data-testid='cookie-banner'] button"
        ]
        
        for selector in popup_selectors:
            try:
                popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                if popup.is_displayed():
                    popup.click()
                    time.sleep(1)
                    print(f"Dismissed popup with selector: {selector}")
            except:
                continue
    
    def extract_post_data(self, element, index: int) -> Dict[str, Any]:
        """Extract data from a single post element with improved selectors"""
        post_data = {'index': index}
        
        try:
            # Extract title with multiple approaches
            title_selectors = [
                "h3",
                "[data-testid='post-title']",
                "[slot='title']",
                "a[data-testid='post-title']",
                "[data-adclicklocation='title']",
                ".Post-title",
                "h1",
                "[data-click-id='title']"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    title_text = title_element.text.strip()
                    if title_text:
                        post_data['title'] = title_text
                        break
                except:
                    continue
            
            # Extract URL/permalink
            url_selectors = [
                "a[href*='/comments/']",
                "a[data-testid='post-title']",
                "[data-click-id='title'] a"
            ]
            
            for selector in url_selectors:
                try:
                    url_element = element.find_element(By.CSS_SELECTOR, selector)
                    href = url_element.get_attribute('href')
                    if href and '/comments/' in href:
                        post_data['url'] = href
                        break
                except:
                    continue
            
            # Extract subreddit
            subreddit_selectors = [
                "a[href*='/r/'][data-testid='subreddit-name']",
                "a[href*='/r/']",
                "[data-testid='subreddit-name']",
                "faceplate-tracker a[href*='/r/']"
            ]
            
            for selector in subreddit_selectors:
                try:
                    subreddit_element = element.find_element(By.CSS_SELECTOR, selector)
                    subreddit_text = subreddit_element.text.strip()
                    if subreddit_text:
                        post_data['subreddit'] = subreddit_text.replace('r/', '')
                        break
                except:
                    continue
            
            # Extract score/upvotes
            score_selectors = [
                "shreddit-score",
                "[data-testid='vote-arrows'] span",
                "faceplate-number",
                ".score",
                "[aria-label*='upvote']"
            ]
            
            for selector in score_selectors:
                try:
                    score_element = element.find_element(By.CSS_SELECTOR, selector)
                    score_text = score_element.text.strip()
                    if score_text and score_text != '•':
                        post_data['score'] = score_text
                        break
                except:
                    continue
            
            # Extract timestamp
            time_selectors = [
                "faceplate-timeago",
                "[data-testid='post-timestamp']",
                "time",
                "[data-testid='post-metadata'] time"
            ]
            
            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    timestamp = time_element.get_attribute('datetime') or time_element.text
                    if timestamp:
                        post_data['timestamp'] = timestamp
                        break
                except:
                    continue
            
            # Extract post content/selftext
            content_selectors = [
                "[data-testid='post-content']",
                ".usertext-body",
                "[slot='text-body']",
                "div[data-adclicklocation='media']"
            ]
            
            for selector in content_selectors:
                try:
                    content_element = element.find_element(By.CSS_SELECTOR, selector)
                    content_text = content_element.text.strip()
                    if content_text:
                        post_data['content'] = content_text
                        break
                except:
                    continue
            
            # Extract number of comments
            comment_selectors = [
                "a[href*='/comments/'] span",
                "[data-testid='comment-count']",
                "a[data-click-id='comments']"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_element = element.find_element(By.CSS_SELECTOR, selector)
                    comment_text = comment_element.text.strip()
                    if 'comment' in comment_text.lower():
                        post_data['comment_count'] = comment_text
                        break
                except:
                    continue
            
        except Exception as e:
            print(f"Error extracting post data: {e}")
        
        return post_data if post_data.get('title') else None
      
    
    def scrape_user_profile(self, profile_url: str) -> Dict[str, Any]:
        if not self.driver:
            self.setup_driver()
    
        username = self.extract_username_from_url(profile_url)
        print(f"Scraping profile for user: {username}")
    
        print("\n" + "="*50)
        print("SCRAPING POSTS")
        print("="*50)
        posts = self.scrape_posts(username)
    
        time.sleep(5)
    
        print("\n" + "="*50)
        print("SCRAPING COMMENTS")
        print("="*50)
    
    # ✅ Use CommentScraper from comments.py
        comment_scraper = CommentScraper(self.driver, self.wait)
        comments = comment_scraper.scrape_comments(username)
    
        return {
            'username': username,
            'profile_url': profile_url,
            'scraped_at': datetime.now().isoformat(),
            'posts': posts,
            'comments': comments,
            'total_posts': len(posts),
            'total_comments': len(comments)
        }

    
    def save_to_file(self, data: Dict[str, Any], filename: str = None):
        """Save scraped data to JSON file"""
        if not filename:
            filename = f"{data['username']}_scraped_data.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()

def main():
    """Example usage of the scraper"""
    
    # IMPORTANT WARNING
    print("WARNING: This scraper violates Reddit's Terms of Service!")
    print("Use the official Reddit API instead.")
    print("This is for educational purposes only.\n")
    
    # Example URLs
    profile_urls = [
        "https://www.reddit.com/user/Seshat_the_Scribe/"
    ]
    
    # Changed to headless=False so you can watch the browser
    scraper = RedditSeleniumScraper(headless=False)
    
    try:
        for url in profile_urls:
            print(f"\n{'='*60}")
            print(f"Scraping: {url}")
            print(f"{'='*60}")
            
            # Scrape user profile
            data = scraper.scrape_user_profile(url)
            
            # Print summary
            print(f"\n📊 SCRAPING SUMMARY:")
            print(f"   Posts found: {data['total_posts']}")
            print(f"   Comments found: {data['total_comments']}")
            
            # Save to file
            scraper.save_to_file(data)
            
            # Add delay between profiles
            time.sleep(10)
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()