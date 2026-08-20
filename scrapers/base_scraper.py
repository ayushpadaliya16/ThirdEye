import asyncio
import logging
from typing import Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, page: Page):
        self.page = page

    def get_standardized_payload(self) -> Dict[str, Any]:
        """
        Returns the strict output dictionary format.
        """
        return {
            "target_handle": "",
            "platform": "",
            "account_creation_date": None,
            "follower_count": 0,
            "following_count": 0,
            "bio_text": "",
            "recent_posts": [],
            "profile_picture_url": ""
        }

    async def safe_navigate(self, url: str, timeout: int = 30000) -> bool:
        """
        Safely navigates to a URL with error handling for timeouts.
        """
        try:
            logger.info(f"Navigating to {url}")
            await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Timeout navigating to {url}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False

    async def extract_data(self, handle: str) -> Dict[str, Any]:
        """
        Base method to be implemented by child classes.
        """
        raise NotImplementedError("Subclasses must implement extract_data")
