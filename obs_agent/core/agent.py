"""Main Agent definition using Google ADK."""

import os
from typing import Optional

from google.adk import Agent
from google.adk.tools import FunctionTool

from obs_agent.tools import (
    analyze_image,
    match_tags,
    save_to_obsidian,
)


AGENT_INSTRUCTION = """你是一个截图信息整理助手，帮助用户从截图中提取信息并保存到 Obsidian。

你的工作流程：
1. 当用户上传截图时，使用 analyze_image 工具分析截图内容
2. 根据分析结果，使用 match_tags 工具匹配合适的标签
3. 如果用户确认保存，使用 save_to_obsidian 工具保存到 Obsidian

支持的截图来源：
- bilibili (B站)
- 小红书
- 微信公众号

提取的信息包括：
- 标题
- 作者
- 来源平台
- 摘要
- 正文内容
- 发布日期

请用中文与用户交流。
"""


def create_agent(api_key: Optional[str] = None) -> Agent:
    """Create and configure the ObsAgent.

    Args:
        api_key: Google API key. If not provided, uses GOOGLE_API_KEY env var.

    Returns:
        Configured Agent instance
    """
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is required")

    tools = [
        FunctionTool(analyze_image),
        FunctionTool(match_tags),
        FunctionTool(save_to_obsidian),
    ]

    agent = Agent(
        name="obs_agent",
        model="gemini-2.0-flash",
        instruction=AGENT_INSTRUCTION,
        tools=tools,
    )

    return agent


obs_agent = None


def get_agent() -> Agent:
    """Get or create the singleton agent instance."""
    global obs_agent
    if obs_agent is None:
        obs_agent = create_agent()
    return obs_agent
