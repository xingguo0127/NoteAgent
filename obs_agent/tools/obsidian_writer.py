"""Obsidian Bases writer for saving articles."""

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from obs_agent.models import Article


def sanitize_filename(title: str) -> str:
    """Convert title to a safe filename.

    Args:
        title: Original title string

    Returns:
        Sanitized filename without extension
    """
    filename = re.sub(r'[<>:"/\\|?*]', "", title)
    filename = re.sub(r"\s+", " ", filename).strip()
    filename = filename[:100]
    return filename


def generate_markdown(article: Article) -> str:
    """Generate markdown content with YAML frontmatter.

    Args:
        article: Article object with all metadata

    Returns:
        Complete markdown string with frontmatter
    """
    frontmatter = article.to_frontmatter()
    yaml_str = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )

    content_parts = [
        "---",
        yaml_str.strip(),
        "---",
        "",
        f"# {article.title}",
        "",
    ]

    if article.url:
        content_parts.extend([f"[原文链接]({article.url})", ""])

    if article.summary:
        content_parts.extend([f"> {article.summary}", ""])

    if article.content:
        content_parts.extend(["## 正文", "", article.content, ""])

    return "\n".join(content_parts)


class ObsidianWriter:
    """Write articles to Obsidian vault in Bases-compatible format."""

    def __init__(
        self,
        vault_path: Optional[str] = None,
        clippings_folder: str = "Clippings",
    ):
        """Initialize the writer.

        Args:
            vault_path: Path to Obsidian vault. If not provided, uses OBSIDIAN_VAULT_PATH env var.
            clippings_folder: Name of the folder inside vault for clippings.
        """
        self.vault_path = Path(vault_path or os.getenv("OBSIDIAN_VAULT_PATH", ""))
        if not self.vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH is required")

        self.clippings_folder = clippings_folder
        self.clippings_path = self.vault_path / clippings_folder

    def ensure_folder_exists(self) -> None:
        """Create the clippings folder if it doesn't exist."""
        self.clippings_path.mkdir(parents=True, exist_ok=True)

    def ensure_base_file_exists(self) -> None:
        """Create the .base file for Obsidian Bases if it doesn't exist."""
        base_file = self.clippings_path / "Clippings.base"
        if base_file.exists():
            return

        base_config = {
            "filter": {},
            "columns": [
                {"name": "title", "label": "标题"},
                {"name": "source", "label": "来源"},
                {"name": "author", "label": "作者"},
                {"name": "tags", "label": "标签"},
                {"name": "capture_date", "label": "收录时间"},
            ],
            "sort": [
                {"column": "capture_date", "direction": "desc"}
            ],
        }
        base_content = yaml.dump(
            base_config,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
        base_file.write_text(base_content, encoding="utf-8")

    def write_article(self, article: Article) -> str:
        """Write an article to the Obsidian vault.

        Args:
            article: Article object to save

        Returns:
            Path to the created file (relative to vault)
        """
        self.ensure_folder_exists()
        self.ensure_base_file_exists()

        filename = sanitize_filename(article.title)
        if not filename:
            filename = f"clipping_{article.capture_date.isoformat()}"

        file_path = self.clippings_path / f"{filename}.md"

        counter = 1
        while file_path.exists():
            file_path = self.clippings_path / f"{filename}_{counter}.md"
            counter += 1

        markdown_content = generate_markdown(article)
        file_path.write_text(markdown_content, encoding="utf-8")

        return str(file_path.relative_to(self.vault_path))


async def save_to_obsidian(
    title: str,
    author: str = "",
    source: str = "",
    summary: str = "",
    content: str = "",
    tags: Optional[list[str]] = None,
    url: str = "",
) -> dict:
    """Tool function for ADK agent to save articles to Obsidian.

    Args:
        title: Article title
        author: Author name
        source: Source platform
        summary: Article summary
        content: Article content
        tags: List of tag IDs
        url: Source URL

    Returns:
        Dictionary with success status and file path
    """
    writer = ObsidianWriter()
    article = Article(
        title=title,
        author=author,
        source=source,
        summary=summary,
        content=content,
        tags=tags or [],
        capture_date=date.today(),
        url=url,
    )

    try:
        file_path = writer.write_article(article)
        return {
            "success": True,
            "file_path": file_path,
            "message": f"Article saved to {file_path}",
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": "",
            "message": str(e),
        }
