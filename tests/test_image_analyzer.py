"""Tests for image analyzer."""

import pytest
from obs_agent.models import AnalyzeResult


def test_analyze_result_model():
    """Test AnalyzeResult model creation."""
    result = AnalyzeResult(
        app_name="bilibili",
        title="测试标题",
        author="测试作者",
        summary="测试摘要",
        content="测试内容",
        publish_date="2026-01-16",
    )
    assert result.app_name == "bilibili"
    assert result.title == "测试标题"
    assert result.author == "测试作者"


def test_analyze_result_defaults():
    """Test AnalyzeResult with default values."""
    result = AnalyzeResult(
        app_name="小红书",
        title="标题",
    )
    assert result.author == ""
    assert result.summary == ""
    assert result.content == ""
    assert result.publish_date == ""
