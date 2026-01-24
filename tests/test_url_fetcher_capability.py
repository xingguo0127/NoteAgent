"""Test script to evaluate URL fetcher capabilities with real test cases."""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from obs_agent.tools.url_fetcher import fetch_url_with_fallback


@dataclass
class TestCase:
    """Test case for URL fetcher."""

    title: str
    author: str
    source: str
    expected_url: Optional[str] = None  # Expected URL for validation (optional)


# Platform name mapping (normalize different names to internal format)
PLATFORM_MAPPING = {
    "哔哩哔哩": "bilibili",
    "b站": "bilibili",
    "B站": "bilibili",
    "小红书": "小红书",
    "微信": "微信公众号",
    "微信公众号": "微信公众号",
    "公众号": "微信公众号",
}


def normalize_platform(source: str) -> str:
    """Normalize platform name to internal format."""
    return PLATFORM_MAPPING.get(source, source.lower())


# Test cases from user's test set
TEST_CASES = [
    TestCase(
        title="【Claude Skills】继MCP之后,又一个好东西",
        author="Hucci写代码",
        source="哔哩哔哩",
    ),
    TestCase(
        title="【上下文工程】一起读一下 Manus所理解的上下文工程",
        author="Hucci写代码",
        source="哔哩哔哩",
    ),
    TestCase(
        title="用AI工具打造代码化设计系统",
        author="Dianne Alter",
        source="小红书",
    ),
    TestCase(
        title="AI硬件新物种爆火！Looki L1理念成熟，但体验让人失望",
        author="雷科技AI硬件组",
        source="微信",
    ),
    TestCase(
        title="用ESP32和UWB做个高精度的室内定位",
        author="吴解君",
        source="微信",
    ),
    TestCase(
        title="免费的Skills合集，每一个Start都在10万+",
        author="图士比亚",
        source="小红书",
    ),
]


async def test_single_case(case: TestCase, index: int) -> dict:
    """Test a single case and return results.

    Args:
        case: Test case to run
        index: Test case index (1-based)

    Returns:
        Dictionary with test results
    """
    platform = normalize_platform(case.source)
    print(f"\n{'='*60}")
    print(f"Test #{index}: {case.title[:40]}...")
    print(f"  Author: {case.author}")
    print(f"  Platform: {case.source} -> {platform}")
    print("-" * 60)

    start_time = time.time()
    try:
        url = await fetch_url_with_fallback(platform, case.title, case.author)
        elapsed = time.time() - start_time

        if url:
            print(f"  ✓ Found URL: {url}")
            print(f"  Time: {elapsed:.2f}s")
            return {
                "index": index,
                "title": case.title,
                "source": case.source,
                "success": True,
                "url": url,
                "time": elapsed,
                "error": None,
            }
        else:
            print(f"  ✗ No URL found")
            print(f"  Time: {elapsed:.2f}s")
            return {
                "index": index,
                "title": case.title,
                "source": case.source,
                "success": False,
                "url": "",
                "time": elapsed,
                "error": "No URL found",
            }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ✗ Error: {e}")
        print(f"  Time: {elapsed:.2f}s")
        return {
            "index": index,
            "title": case.title,
            "source": case.source,
            "success": False,
            "url": "",
            "time": elapsed,
            "error": str(e),
        }


async def run_all_tests():
    """Run all test cases and print summary."""
    print("=" * 60)
    print("URL Fetcher Capability Test")
    print("=" * 60)
    print(f"Total test cases: {len(TEST_CASES)}")

    results = []
    for i, case in enumerate(TEST_CASES, 1):
        result = await test_single_case(case, i)
        results.append(result)
        # Add a small delay between requests to avoid rate limiting
        if i < len(TEST_CASES):
            await asyncio.sleep(1)

    # Print summary
    print("\n")
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\nTotal: {len(results)}")
    print(f"Success: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")

    if successful:
        avg_time = sum(r["time"] for r in successful) / len(successful)
        print(f"\nAverage time for successful fetches: {avg_time:.2f}s")

    # Print detailed results table
    print("\n" + "-" * 100)
    print(f"{'#':<3} {'Source':<8} {'Title':<45} {'Result':<8} {'URL'}")
    print("-" * 100)

    for r in results:
        title_short = r["title"][:42] + "..." if len(r["title"]) > 45 else r["title"]
        status = "✓" if r["success"] else "✗"
        url_short = r["url"][:40] + "..." if len(r["url"]) > 40 else r["url"]
        print(f"{r['index']:<3} {r['source']:<8} {title_short:<45} {status:<8} {url_short}")

    # Print failed cases details
    if failed:
        print("\n" + "=" * 60)
        print("FAILED CASES DETAILS")
        print("=" * 60)
        for r in failed:
            print(f"\n#{r['index']}: {r['title']}")
            print(f"  Source: {r['source']}")
            print(f"  Error: {r['error']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
