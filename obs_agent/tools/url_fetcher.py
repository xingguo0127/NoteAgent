"""URL fetcher module for retrieving source URLs from different platforms."""

import os
from abc import ABC, abstractmethod
from typing import Optional

import httpx


class BaseUrlFetcher(ABC):
    """Abstract base class for URL fetchers."""

    @abstractmethod
    async def fetch_url(self, title: str, author: str = "") -> str:
        """Fetch the source URL for given title and author.

        Args:
            title: Article/video title
            author: Author name (optional)

        Returns:
            Source URL or empty string if not found
        """
        pass


class BilibiliUrlFetcher(BaseUrlFetcher):
    """URL fetcher for Bilibili videos."""

    SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
    VIDEO_URL_TEMPLATE = "https://www.bilibili.com/video/{bvid}"

    def __init__(self, sessdata: Optional[str] = None):
        """Initialize with SESSDATA cookie.

        Args:
            sessdata: Bilibili SESSDATA cookie value
        """
        self.sessdata = sessdata or os.getenv("BILIBILI_SESSDATA", "")

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Search Bilibili and return the first matching video URL.

        Args:
            title: Video title to search for
            author: Author name (optional, for better matching)

        Returns:
            Video URL or empty string if not found
        """
        if not title:
            return ""

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://search.bilibili.com",
                "Origin": "https://search.bilibili.com",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            # Add SESSDATA cookie if configured (required for stable API access)
            if self.sessdata:
                headers["Cookie"] = f"SESSDATA={self.sessdata}"

            params = {
                "search_type": "video",
                "keyword": title,
            }

            # Use trust_env=False to bypass system proxy for direct Bilibili API access
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.get(
                    self.SEARCH_API,
                    headers=headers,
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") != 0:
                    return ""

                results = data.get("data", {}).get("result", [])
                if not results:
                    return ""

                # Return the first result's URL
                bvid = results[0].get("bvid", "")
                if bvid:
                    return self.VIDEO_URL_TEMPLATE.format(bvid=bvid)

                return ""

        except Exception:
            return ""


class XiaohongshuUrlFetcher(BaseUrlFetcher):
    """URL fetcher for Xiaohongshu (placeholder)."""

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Placeholder for Xiaohongshu URL fetching.

        Returns:
            Empty string (not implemented yet)
        """
        return ""


class WechatUrlFetcher(BaseUrlFetcher):
    """URL fetcher for WeChat articles (placeholder)."""

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Placeholder for WeChat URL fetching.

        Returns:
            Empty string (not implemented yet)
        """
        return ""


class UrlFetcherFactory:
    """Factory for creating URL fetchers based on platform."""

    _fetchers = {
        "bilibili": BilibiliUrlFetcher,
        "小红书": XiaohongshuUrlFetcher,
        "微信公众号": WechatUrlFetcher,
    }

    @classmethod
    def create(cls, platform: str) -> BaseUrlFetcher:
        """Create a URL fetcher for the specified platform.

        Args:
            platform: Platform name (bilibili, 小红书, 微信公众号)

        Returns:
            URL fetcher instance
        """
        normalized = platform.lower() if platform else ""
        fetcher_class = cls._fetchers.get(normalized)
        if fetcher_class:
            return fetcher_class()

        # Return a no-op fetcher for unknown platforms
        return XiaohongshuUrlFetcher()


async def fetch_source_url(platform: str, title: str, author: str = "") -> str:
    """Convenience function to fetch source URL for a given platform.

    Args:
        platform: Platform name (bilibili, 小红书, 微信公众号)
        title: Article/video title
        author: Author name (optional)

    Returns:
        Source URL or empty string if not found
    """
    fetcher = UrlFetcherFactory.create(platform)
    return await fetcher.fetch_url(title, author)
