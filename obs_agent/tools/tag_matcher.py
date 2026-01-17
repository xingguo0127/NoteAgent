"""Tag matcher using AI and YAML configuration."""

import json
import os
from pathlib import Path
from typing import Optional

import yaml
from google import genai
from google.genai import types

from obs_agent.models import TagsConfig, AnalyzeResult


def load_tags_config(config_path: Optional[str] = None) -> TagsConfig:
    """Load tags configuration from YAML file.

    Args:
        config_path: Path to tags.yaml. If not provided, uses default location.

    Returns:
        TagsConfig object with all tag categories
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "tags.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        return TagsConfig(categories=[])

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return TagsConfig(**data)


def get_tags_prompt(config: TagsConfig) -> str:
    """Generate prompt for AI tag matching based on config."""
    categories_desc = []
    all_tag_ids = []

    for category in config.categories:
        tags_desc = []
        for tag in category.tags:
            all_tag_ids.append(tag.id)
            keywords_str = f" (关键词: {', '.join(tag.keywords)})" if tag.keywords else ""
            tags_desc.append(f"  - {tag.id}: {tag.name}{keywords_str}")
        categories_desc.append(f"{category.name}:\n" + "\n".join(tags_desc))

    return f"""根据以下文章信息，从给定的标签中选择最合适的标签。

可用标签分类：
{chr(10).join(categories_desc)}

请返回一个 JSON 数组，包含选中的标签 ID（不是标签名称）。
每个分类最多选择 2 个最相关的标签。
只返回 JSON 数组，不要包含任何其他文字。

示例返回格式: ["tech", "bilibili", "tutorial"]
"""


class TagMatcher:
    """Match tags to content using AI."""

    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        """Initialize the tag matcher.

        Args:
            api_key: Google API key. If not provided, uses GOOGLE_API_KEY env var.
            config_path: Path to tags.yaml configuration file.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"
        self.config = load_tags_config(config_path)

    def get_all_tag_ids(self) -> list[str]:
        """Get all valid tag IDs from configuration."""
        tag_ids = []
        for category in self.config.categories:
            for tag in category.tags:
                tag_ids.append(tag.id)
        return tag_ids

    async def match_tags(self, analyze_result: AnalyzeResult) -> list[str]:
        """Match tags to analyzed content.

        Args:
            analyze_result: Result from image analysis

        Returns:
            List of matched tag IDs
        """
        if not self.config.categories:
            return [self._source_to_tag(analyze_result.app_name)]

        content_desc = f"""
标题: {analyze_result.title}
来源: {analyze_result.app_name}
作者: {analyze_result.author}
摘要: {analyze_result.summary}
内容: {analyze_result.content[:500] if analyze_result.content else ''}
"""

        prompt = get_tags_prompt(self.config) + f"\n\n文章信息:\n{content_desc}"

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text.strip()
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])

        tags = json.loads(result_text)

        valid_tags = self.get_all_tag_ids()
        matched_tags = [tag for tag in tags if tag in valid_tags]

        source_tag = self._source_to_tag(analyze_result.app_name)
        if source_tag and source_tag not in matched_tags:
            matched_tags.append(source_tag)

        return matched_tags

    def _source_to_tag(self, app_name: str) -> str:
        """Convert app name to tag ID."""
        mapping = {
            "bilibili": "bilibili",
            "小红书": "xiaohongshu",
            "微信公众号": "wechat",
        }
        return mapping.get(app_name, "")


async def match_tags(
    title: str,
    app_name: str,
    author: str = "",
    summary: str = "",
    content: str = "",
) -> list[str]:
    """Tool function for ADK agent to match tags.

    Args:
        title: Article title
        app_name: Source platform
        author: Author name
        summary: Article summary
        content: Article content

    Returns:
        List of matched tag IDs
    """
    matcher = TagMatcher()
    analyze_result = AnalyzeResult(
        app_name=app_name,
        title=title,
        author=author,
        summary=summary,
        content=content,
    )
    return await matcher.match_tags(analyze_result)
