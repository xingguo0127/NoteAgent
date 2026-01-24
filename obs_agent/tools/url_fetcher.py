"""URL fetcher module for retrieving source URLs from different platforms."""

import os
import re
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from duckduckgo_search import DDGS


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


class SearchEngineUrlFetcher(BaseUrlFetcher):
    """URL fetcher using DuckDuckGo search with site: syntax."""

    # Platform to domain mapping
    PLATFORM_DOMAINS = {
        "bilibili": "bilibili.com",
        "小红书": "xiaohongshu.com",
        "微信公众号": "mp.weixin.qq.com",
        "youtube": "youtube.com",
        "抖音": "douyin.com",
        "知乎": "zhihu.com",
        "微博": "weibo.com",
        "豆瓣": "douban.com",
        "今日头条": "toutiao.com",
        "快手": "kuaishou.com",
    }

    # URL patterns for each platform to validate results
    URL_PATTERNS = {
        "bilibili": r"https?://(?:www\.)?bilibili\.com/video/[A-Za-z0-9]+",
        "小红书": r"https?://(?:www\.)?xiaohongshu\.com/(?:explore|discovery/item|user/profile)/[A-Za-z0-9]+",
        "微信公众号": r"https?://mp\.weixin\.qq\.com/s[/?]",
        "youtube": r"https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]+",
        "抖音": r"https?://(?:www\.)?douyin\.com/video/\d+",
        "知乎": r"https?://(?:www\.)?zhihu\.com/(?:question|answer|p)/\d+|https?://zhuanlan\.zhihu\.com/p/\d+",
        "微博": r"https?://(?:www\.)?weibo\.com/\d+/[A-Za-z0-9]+",
    }

    def __init__(self, platform: str):
        """Initialize with target platform.

        Args:
            platform: Platform name for site-specific search
        """
        self.platform = platform.lower() if platform else ""
        self.domain = self.PLATFORM_DOMAINS.get(self.platform, "")
        self.url_pattern = self.URL_PATTERNS.get(self.platform)

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Search using DuckDuckGo with site: restriction.

        Tries multiple search strategies:
        1. site: + quoted title
        2. site: + unquoted title
        3. Platform name + title (filter by domain)

        Args:
            title: Content title to search for
            author: Author name (optional, included in search query)

        Returns:
            URL or empty string if not found
        """
        if not title or not self.domain:
            return ""

        # Try different search strategies
        search_queries = [
            # Strategy 1: site: with quoted title
            f'site:{self.domain} "{title}"' + (f" {author}" if author else ""),
            # Strategy 2: site: with unquoted title
            f"site:{self.domain} {title}" + (f" {author}" if author else ""),
            # Strategy 3: Platform name + title (more results, filter later)
            f"{self.domain} {title}" + (f" {author}" if author else ""),
        ]

        for query in search_queries:
            url = self._search_and_extract(query)
            if url:
                return url

        return ""

    def _search_and_extract(self, query: str) -> str:
        """Execute search and extract matching URL.

        Args:
            query: Search query

        Returns:
            Matching URL or empty string
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))

            if not results:
                return ""

            # Find the best matching URL
            for result in results:
                url = result.get("href", "")
                if not url:
                    continue

                # Must contain the domain
                if self.domain not in url:
                    continue

                # Validate URL matches expected platform pattern
                if self.url_pattern:
                    if re.search(self.url_pattern, url):
                        return url
                else:
                    return url

            # If no pattern match, return first result with domain
            for result in results:
                url = result.get("href", "")
                if self.domain in url:
                    return url

            return ""

        except Exception:
            return ""


class XiaohongshuUrlFetcher(BaseUrlFetcher):
    """URL fetcher for Xiaohongshu. Currently disabled due to unreliable search results."""

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Xiaohongshu URL fetching is disabled.

        Search engines cannot reliably find Xiaohongshu note URLs.
        Returns empty string for now.

        Args:
            title: Note title
            author: Author name (optional)

        Returns:
            Empty string (disabled)
        """
        return ""


class WechatUrlFetcher(BaseUrlFetcher):
    """URL fetcher for WeChat articles using search engine."""

    def __init__(self):
        self._search_fetcher = SearchEngineUrlFetcher("微信公众号")

    async def fetch_url(self, title: str, author: str = "") -> str:
        """Fetch WeChat article URL using search engine.

        Args:
            title: Article title
            author: Author/公众号 name (optional)

        Returns:
            Article URL or empty string if not found
        """
        return await self._search_fetcher.fetch_url(title, author)


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
            platform: Platform name (bilibili, 小红书, 微信公众号, etc.)

        Returns:
            URL fetcher instance
        """
        normalized = platform.lower() if platform else ""
        fetcher_class = cls._fetchers.get(normalized)
        if fetcher_class:
            return fetcher_class()

        # For unknown platforms, try search engine approach
        if normalized in SearchEngineUrlFetcher.PLATFORM_DOMAINS:
            return SearchEngineUrlFetcher(normalized)

        # Return a no-op fetcher for completely unknown platforms
        return _NoOpUrlFetcher()


class _NoOpUrlFetcher(BaseUrlFetcher):
    """No-op URL fetcher for unsupported platforms."""

    async def fetch_url(self, title: str, author: str = "") -> str:
        return ""


async def fetch_source_url(platform: str, title: str, author: str = "") -> str:
    """Convenience function to fetch source URL for a given platform.

    Args:
        platform: Platform name (bilibili, 小红书, 微信公众号, etc.)
        title: Article/video title
        author: Author name (optional)

    Returns:
        Source URL or empty string if not found
    """
    fetcher = UrlFetcherFactory.create(platform)
    return await fetcher.fetch_url(title, author)


async def fetch_url_with_fallback(platform: str, title: str, author: str = "") -> str:
    """Fetch URL with search engine fallback.

    First tries platform-specific API, then falls back to search engine.

    Args:
        platform: Platform name
        title: Content title
        author: Author name (optional)

    Returns:
        Source URL or empty string if not found
    """
    # Platforms with unreliable search results - skip entirely
    DISABLED_PLATFORMS = {"小红书"}

    normalized = platform.lower() if platform else ""
    if normalized in DISABLED_PLATFORMS:
        return ""

    # Try platform-specific fetcher first
    fetcher = UrlFetcherFactory.create(platform)
    url = await fetcher.fetch_url(title, author)

    if url:
        return url

    # Fallback to search engine if platform-specific failed
    if normalized in SearchEngineUrlFetcher.PLATFORM_DOMAINS:
        search_fetcher = SearchEngineUrlFetcher(normalized)
        return await search_fetcher.fetch_url(title, author)

    return ""
