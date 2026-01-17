"""Data models for ObsAgent."""

from datetime import date
from pydantic import BaseModel, Field


class AnalyzeResult(BaseModel):
    """Result of screenshot analysis."""

    app_name: str = Field(description="Source platform (bilibili/小红书/微信公众号)")
    title: str = Field(description="Article title")
    author: str = Field(default="", description="Author name")
    summary: str = Field(default="", description="Article summary")
    content: str = Field(default="", description="Main content")
    publish_date: str = Field(default="", description="Publish date if available")


class TagConfig(BaseModel):
    """Single tag configuration."""

    id: str
    name: str
    keywords: list[str] = Field(default_factory=list)


class TagCategory(BaseModel):
    """Tag category containing multiple tags."""

    id: str
    name: str
    tags: list[TagConfig]


class TagsConfig(BaseModel):
    """Root tags configuration."""

    categories: list[TagCategory]


class Article(BaseModel):
    """Complete article with analysis result and tags."""

    title: str
    author: str = ""
    source: str = ""
    summary: str = ""
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    capture_date: date = Field(default_factory=date.today)

    def to_frontmatter(self) -> dict:
        """Convert to frontmatter dictionary."""
        return {
            "title": self.title,
            "author": self.author,
            "source": self.source,
            "tags": self.tags,
            "capture_date": self.capture_date.isoformat(),
            "summary": self.summary,
        }


class AnalyzeRequest(BaseModel):
    """Request for analyze endpoint (metadata only, file sent separately)."""

    pass


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""

    app_name: str
    title: str
    author: str
    summary: str
    content: str
    tags: list[str]


class SaveRequest(BaseModel):
    """Request to save article to Obsidian."""

    title: str
    author: str = ""
    source: str = ""
    summary: str = ""
    content: str = ""
    tags: list[str] = Field(default_factory=list)


class SaveResponse(BaseModel):
    """Response from save endpoint."""

    success: bool
    file_path: str = ""
    message: str = ""


class ProcessRequest(BaseModel):
    """Request for the unified process endpoint."""

    app_name: str = Field(default="", description="App name (e.g., bilibili, 小红书). If provided, overrides detected app_name.")
    image_base64: str = Field(description="Base64 encoded image data")


class ProcessResponse(BaseModel):
    """Response from the unified process endpoint."""

    success: bool
    message: str = ""
    app_name: str = ""
    title: str = ""
    author: str = ""
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    file_path: str = ""
    git_status: str = ""
