"""
comments.py - Updated Reddit Comment Scraping Functions
This module contains improved comment scraping methods for the Reddit Selenium scraper.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
from typing import List, Dict, Any

class CommentScraper:
    """Enhanced comment scraping functionality for Reddit profiles"""
    
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
    
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
    
    def scrape_comments(self, username: str) -> List[Dict[str, Any]]:
        """Scrape user comments from their profile with updated selectors"""
        comments = []
        url = f"https://www.reddit.com/user/{username}/comments/"
        
        try:
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for comments to load
            time.sleep(5)
            self.dismiss_popups()
            
            try:
                # Wait for the main content area to load
                self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "shreddit-profile-comment")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[aria-label*='comment']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='comment']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".Comment")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='hover:bg-neutral-background-hover']"))
                    )
                )
                print("Comments section loaded successfully")
            except TimeoutException:
                print("No comments found or page didn't load properly")
                # Debug: Print page source snippet
                print("Page source snippet:")
                print(self.driver.page_source[:1000])
                return comments
            
            # Scroll to load more content
            self.wait_and_scroll(8)
            
            # Updated comment selectors based on the console image
            comment_selectors = [
                "shreddit-profile-comment",
                "article[aria-label*='comment']", 
                "div[class*='hover:bg-neutral-background-hover'][class*='relative']",
                "div[data-testid='comment']",
                ".Comment",
                "article[class*='mb-0'][class*='w-full']"
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comment_elements:
                        print(f"Found {len(comment_elements)} comments using selector: {selector}")
                        break
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not comment_elements:
                print("No comment elements found with any selector. Trying fallback...")
                # Fallback: look for any element containing comment-like structure
                fallback_selectors = [
                    "div[class*='text-12'][class*='relative']",
                    "div[class*='post-revision-content']",
                    "div[aria-label*='comment']"
                ]
                
                for selector in fallback_selectors:
                    try:
                        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if comment_elements:
                            print(f"Found {len(comment_elements)} elements with fallback selector: {selector}")
                            break
                    except:
                        continue
            
            # Extract data from each comment
            for i, element in enumerate(comment_elements[:7]):
                try:
                    comment_data = self.extract_comment_data(element, i)
                    if comment_data and comment_data.get('body'):
                        comments.append(comment_data)
                        print(f"✓ Extracted comment {i+1}: {comment_data['body'][:60]}...")
                    else:
                        print(f"✗ Failed to extract comment {i+1}")
                except Exception as e:
                    print(f"✗ Error extracting comment {i+1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error scraping comments: {e}")
            import traceback
            traceback.print_exc()
        
        return comments
    
    def extract_comment_data(self, element, index: int) -> Dict[str, Any]:
        """Extract data from a single comment element with updated selectors"""
        comment_data = {'index': index}
        
        try:
            # Debug: Print element HTML for first few comments
            if index < 3:
                print(f"Debug - Comment {index} HTML snippet:")
                print(element.get_attribute('outerHTML')[:500])
            
            # Extract comment text with updated selectors
            text_selectors = [
                "div[class*='post-revision-content']",
                "div[slot='comment']",
                "div[data-testid='comment-text']",
                "div[class*='text-neutral-content-strong'][class*='overflow-hidden']",
                "div[class*='usertext-body']",
                "div p",
                "div[class*='md']",
                "[slot='text-body']",
                # More specific selectors based on the structure
                "div[class*='relative'] div[class*='text-neutral-content-strong']",
                "div[class*='overflow-hidden'] p"
            ]
            
            for selector in text_selectors:
                try:
                    text_elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for text_element in text_elements:
                        comment_text = text_element.text.strip()
                        if comment_text and len(comment_text) > 10:  # Ensure it's actual content
                            comment_data['body'] = comment_text
                            break
                    if comment_data.get('body'):
                        break
                except Exception as e:
                    print(f"Text selector {selector} failed: {e}")
                    continue
            
            # Extract subreddit with updated selectors
            subreddit_selectors = [
                "a[href*='/r/'][class*='hover:underline']",
                "a[href*='/r/']",
                "[data-testid='subreddit-name']",
                "faceplate-tracker a[href*='/r/']"
            ]
            
            for selector in subreddit_selectors:
                try:
                    subreddit_element = element.find_element(By.CSS_SELECTOR, selector)
                    subreddit_text = subreddit_element.text.strip()
                    if subreddit_text and ('r/' in subreddit_text or subreddit_text.startswith('r/')):
                        comment_data['subreddit'] = subreddit_text.replace('r/', '')
                        break
                except:
                    continue
            
            # Extract score with updated selectors
            score_selectors = [
                "shreddit-score",
                "div[class*='ml-[22px]'] span",
                "faceplate-number",
                ".score",
                "[aria-label*='upvote']",
                "div[class*='text-12'] span"
            ]
            
            for selector in score_selectors:
                try:
                    score_element = element.find_element(By.CSS_SELECTOR, selector)
                    score_text = score_element.text.strip()
                    if score_text and score_text != '•' and score_text.isdigit():
                        comment_data['score'] = score_text
                        break
                except:
                    continue
            
            # Extract timestamp with updated selectors
            time_selectors = [
                "faceplate-timeago",
                "time",
                "[data-testid='comment-timestamp']",
                "div[class*='text-12'] time",
                "span[class*='text-12']"
            ]
            
            for selector in time_selectors:
                try:
                    time_element = element.find_element(By.CSS_SELECTOR, selector)
                    timestamp = time_element.get_attribute('datetime') or time_element.text
                    if timestamp and ('ago' in timestamp or 'T' in timestamp):
                        comment_data['timestamp'] = timestamp
                        break
                except:
                    continue
            
            # Extract parent post title/context with updated selectors
            context_selectors = [
                "a[href*='/comments/'][class*='hover:underline']",
                "a[href*='/comments/']",
                "[data-testid='post-title']",
                "div[class*='text-12'] a"
            ]
            
            for selector in context_selectors:
                try:
                    context_element = element.find_element(By.CSS_SELECTOR, selector)
                    context_text = context_element.text.strip()
                    if context_text and len(context_text) > 5:
                        comment_data['post_context'] = context_text
                        # Also extract the post URL
                        post_url = context_element.get_attribute('href')
                        if post_url:
                            comment_data['post_url'] = post_url
                        break
                except:
                    continue
            
            # Try to extract additional metadata
            try:
                # Look for any additional text that might be metadata
                metadata_elements = element.find_elements(By.CSS_SELECTOR, "div[class*='text-12'] span")
                for meta_element in metadata_elements:
                    meta_text = meta_element.text.strip()
                    if 'points' in meta_text.lower() or 'point' in meta_text.lower():
                        comment_data['score'] = meta_text
                    elif 'ago' in meta_text.lower():
                        comment_data['timestamp'] = meta_text
            except:
                pass
            
        except Exception as e:
            print(f"Error extracting comment data: {e}")
            import traceback
            traceback.print_exc()
        
        return comment_data if comment_data.get('body') else None
    
    def debug_comment_structure(self, username: str):
        """Debug method to analyze comment page structure"""
        url = f"https://www.reddit.com/user/{username}/comments/"
        
        try:
            print(f"Debugging comment structure for: {url}")
            self.driver.get(url)
            time.sleep(5)
            self.dismiss_popups()
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page source and analyze structure
            page_source = self.driver.page_source
            
            # Look for common patterns
            patterns = [
                r'class="[^"]*comment[^"]*"',
                r'data-testid="[^"]*comment[^"]*"',
                r'aria-label="[^"]*comment[^"]*"',
                r'shreddit-[^"]*comment[^"]*'
            ]
            
            print("\nFound comment-related patterns:")
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    print(f"Pattern {pattern}: {matches[:5]}")  # Show first 5 matches
            
            # Try to find all elements that might be comments
            potential_selectors = [
                "article",
                "div[class*='hover']",
                "div[class*='relative']",
                "shreddit-profile-comment",
                "*[aria-label*='comment']"
            ]
            
            for selector in potential_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"\nSelector '{selector}' found {len(elements)} elements")
                    if elements and len(elements) > 0:
                        print(f"First element HTML: {elements[0].get_attribute('outerHTML')[:200]}...")
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    
        except Exception as e:
            print(f"Debug error: {e}")
            import traceback
            traceback.print_exc()