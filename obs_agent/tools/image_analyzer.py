"""Image analyzer using Gemini multimodal API."""

import base64
import json
import os
from typing import Optional

from google import genai
from google.genai import types

from obs_agent.models import AnalyzeResult


ANALYZE_PROMPT = """分析这张截图，提取以下信息并以 JSON 格式返回：

1. app_name: 来源平台，只能是以下三个之一：
   - "bilibili" (B站)
   - "小红书"
   - "微信公众号"
   如果无法确定平台，根据界面特征推断最可能的平台。

2. title: 文章/视频标题

3. author: 作者/UP主/博主名称

4. summary: 内容摘要（1-2句话概括主要内容）

5. content: 正文主要内容（如果是长文章，提取关键段落）

6. publish_date: 发布日期（如果可见，格式：YYYY-MM-DD）

请严格按照以下 JSON 格式返回，不要包含任何其他文字：
{
    "app_name": "平台名称",
    "title": "标题",
    "author": "作者",
    "summary": "摘要",
    "content": "正文内容",
    "publish_date": "发布日期或空字符串"
}
"""


class ImageAnalyzer:
    """Analyze screenshots using Gemini multimodal API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer with API key."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"

    async def analyze(self, image_data: bytes, mime_type: str = "image/png") -> AnalyzeResult:
        """Analyze an image and extract article information.

        Args:
            image_data: Raw image bytes
            mime_type: MIME type of the image (e.g., image/png, image/jpeg)

        Returns:
            AnalyzeResult with extracted information
        """
        image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[image_part, ANALYZE_PROMPT],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text.strip()

        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])

        result_dict = json.loads(result_text)
        return AnalyzeResult(**result_dict)

    async def analyze_file(self, file_path: str) -> AnalyzeResult:
        """Analyze an image file.

        Args:
            file_path: Path to the image file

        Returns:
            AnalyzeResult with extracted information
        """
        ext = file_path.lower().split(".")[-1]
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        mime_type = mime_types.get(ext, "image/png")

        with open(file_path, "rb") as f:
            image_data = f.read()

        return await self.analyze(image_data, mime_type)


async def analyze_image(image_data: bytes, mime_type: str = "image/png") -> dict:
    """Tool function for ADK agent to analyze images.

    Args:
        image_data: Base64 encoded image data
        mime_type: MIME type of the image

    Returns:
        Dictionary with extracted information
    """
    analyzer = ImageAnalyzer()
    result = await analyzer.analyze(image_data, mime_type)
    return result.model_dump()
