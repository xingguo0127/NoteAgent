"""Tag matcher using LiteLLM and YAML configuration."""

import json
import os
from pathlib import Path
from typing import Optional

import yaml
import litellm

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

    # Separate topic categories and content type category
    topic_categories = []
    type_category = None

    for category in config.categories:
        if category.id == "type":
            type_category = category
        else:
            topic_categories.append(category)

    # Build topic tags description
    for category in topic_categories:
        tags_desc = []
        for tag in category.tags:
            keywords_str = f" (关键词: {', '.join(tag.keywords)})" if tag.keywords else ""
            tags_desc.append(f"  - {tag.id}: {tag.name}{keywords_str}")
        categories_desc.append(f"{category.name} ({category.id}/):\n" + "\n".join(tags_desc))

    # Build content type description
    type_desc = ""
    if type_category:
        type_tags = []
        for tag in type_category.tags:
            keywords_str = f" (关键词: {', '.join(tag.keywords)})" if tag.keywords else ""
            type_tags.append(f"  - {tag.id}: {tag.name}{keywords_str}")
        type_desc = f"\n内容类型 (type/)（必选1个）:\n" + "\n".join(type_tags)

    return f"""根据以下文章信息，从给定的标签中选择最合适的标签。

## 主题领域标签（可多选，每个分类最多选2个）：
{chr(10).join(categories_desc)}
{type_desc}

## 规则：
1. 主题领域标签可以选择多个，但每个分类最多2个
2. 内容类型标签必须且只能选择1个
3. 返回格式为 JSON 数组，包含完整的标签 ID（如 "ai/coding", "type/tutorial"）

请只返回 JSON 数组，不要包含任何其他文字。

示例返回格式: ["ai/coding", "dev/tools", "type/tutorial"]
"""


class TagMatcher:
    """Match tags to content using LiteLLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize the tag matcher.

        Args:
            api_key: OpenRouter API key. If not provided, uses OPENROUTER_API_KEY env var.
            model: Model name. If not provided, uses LLM_MODEL env var or default.
            config_path: Path to tags.yaml configuration file.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.model = model or os.getenv("LLM_MODEL", "openrouter/google/gemini-2.5-flash-preview")
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
            return []

        content_desc = f"""
标题: {analyze_result.title}
作者: {analyze_result.author}
摘要: {analyze_result.summary}
内容: {analyze_result.content[:500] if analyze_result.content else ''}
"""

        prompt = get_tags_prompt(self.config) + f"\n\n文章信息:\n{content_desc}"

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])

        # Handle both array and object responses
        parsed = json.loads(result_text)
        if isinstance(parsed, list):
            tags = parsed
        elif isinstance(parsed, dict):
            # Try to extract tags from common keys
            tags = parsed.get("tags", parsed.get("result", []))
        else:
            tags = []

        valid_tags = self.get_all_tag_ids()
        matched_tags = [tag for tag in tags if tag in valid_tags]

        return matched_tags


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
