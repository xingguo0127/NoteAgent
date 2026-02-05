"""URL resolver for extracting and resolving URLs from text."""

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import httpx


# Known short URL domains that need resolution
SHORT_URL_DOMAINS = {
    "b23.tv",           # Bilibili
    "xhslink.com",      # Xiaohongshu
    "t.cn",             # Weibo
    "dwz.cn",           # Baidu
    "url.cn",           # QQ/WeChat
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
}

# URL pattern to extract URLs from text
URL_PATTERN = re.compile(
    r'https?://[^\s<>\[\]()（）「」【】\u4e00-\u9fff]+'
)


def extract_url(text: str) -> str:
    """Extract the first URL from text.

    Args:
        text: Text that may contain a URL mixed with other content

    Returns:
        Extracted URL or empty string if not found
    """
    if not text:
        return ""

    # If the text is already a clean URL, return it
    text = text.strip()
    if text.startswith("http://") or text.startswith("https://"):
        # Check if it's a pure URL (no spaces or Chinese characters)
        if " " not in text and not re.search(r'[\u4e00-\u9fff]', text):
            return text

    # Extract URL from text
    match = URL_PATTERN.search(text)
    if match:
        url = match.group(0)
        # Clean up trailing punctuation
        url = url.rstrip('.,;:!?\'\"')
        return url

    return ""


def is_short_url(url: str) -> bool:
    """Check if URL is a known short URL that needs resolution.

    Args:
        url: URL to check

    Returns:
        True if it's a short URL
    """
    if not url:
        return False

    for domain in SHORT_URL_DOMAINS:
        if domain in url:
            return True

    return False


async def resolve_short_url(url: str, timeout: float = 10.0) -> str:
    """Resolve a short URL to its final destination.

    Follows redirects to get the final URL.

    Args:
        url: Short URL to resolve
        timeout: Request timeout in seconds

    Returns:
        Final URL after following redirects, or original URL if resolution fails
    """
    if not url:
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers=headers,
            # Bypass proxy for direct access
            trust_env=False,
        ) as client:
            # Try HEAD first, fall back to GET if needed
            try:
                response = await client.head(url)
                final_url = str(response.url)
                # If HEAD didn't redirect, try GET
                if final_url == url:
                    response = await client.get(url)
                    final_url = str(response.url)
                return final_url
            except Exception:
                # Some servers don't support HEAD, use GET
                response = await client.get(url)
                return str(response.url)

    except Exception:
        # If resolution fails, return original URL
        return url


def clean_url(url: str) -> str:
    """Clean URL by removing tracking parameters.

    Args:
        url: URL to clean

    Returns:
        Cleaned URL
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)

        # Parameters to keep for each domain
        keep_params = {
            "bilibili.com": {"p"},  # Keep page number only
            "youtube.com": {"v", "t", "list"},  # Keep video ID, timestamp, playlist
            "youtu.be": {"t"},
        }

        # Find matching domain
        domain_key = None
        for domain in keep_params:
            if domain in parsed.netloc:
                domain_key = domain
                break

        if domain_key:
            # Filter parameters
            params = parse_qs(parsed.query)
            allowed = keep_params[domain_key]
            filtered = {k: v[0] for k, v in params.items() if k in allowed}
            new_query = urlencode(filtered) if filtered else ""
            cleaned = parsed._replace(query=new_query)
            return urlunparse(cleaned)

        return url

    except Exception:
        return url


async def extract_and_resolve_url(text: str) -> str:
    """Extract URL from text and resolve if it's a short URL.

    This is the main function to use for processing user-provided URL text.

    Args:
        text: Text containing URL (may have extra text around it)

    Returns:
        Resolved and cleaned URL, or empty string if no URL found
    """
    # Step 1: Extract URL from text
    url = extract_url(text)
    if not url:
        return ""

    # Step 2: Resolve short URL if needed
    if is_short_url(url):
        url = await resolve_short_url(url)

    # Step 3: Clean tracking parameters
    url = clean_url(url)

    return url
