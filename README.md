# ObsAgent

截图信息整理 Agent，自动提取截图内容并保存到 Obsidian，支持 Git 自动同步。

## 功能特点

- 支持 bilibili、小红书、微信公众号截图识别
- 使用 LiteLLM + OpenRouter 调用 Gemini 2.5 Flash 多模态 API 提取信息
- AI 自动打标签
- 保存为 Obsidian Bases 兼容格式
- 自动 Git 同步（pull -> write -> commit -> push）

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

需要配置：
- `OPENROUTER_API_KEY`: OpenRouter API 密钥 (从 https://openrouter.ai/keys 获取)
- `LLM_MODEL`: 模型名称（可选，默认 `openrouter/google/gemini-2.5-flash-preview`）
- `OBSIDIAN_GIT_REPO`: Obsidian 笔记的 GitHub 仓库地址（推荐使用 SSH 格式）
- `OBSIDIAN_GIT_BRANCH`: Git 分支名称（默认 main）
- `OBSIDIAN_VAULT_PATH`: 本地 Obsidian Vault 路径

### 3. 启动服务

```bash
python -m obs_agent
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/process` | 处理截图（分析 + 保存 + Git 同步） |
| GET | `/api/health` | 健康检查 |
| GET | `/docs` | API 文档 |

### POST /api/process

处理截图的完整工作流：
1. Git pull 更新本地仓库
2. 分析截图提取信息
3. 匹配标签
4. 写入 Obsidian 笔记
5. Git commit 和 push

**请求格式：**

```json
{
  "app_name": "小红书",      // 可选，指定来源 APP，会覆盖自动识别的结果
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."  // 必填，Base64 编码的图片
}
```

**响应格式：**

```json
{
  "success": true,
  "message": "Article saved and synced: Clippings/文章标题.md",
  "app_name": "小红书",
  "title": "文章标题",
  "author": "作者名",
  "summary": "文章摘要",
  "tags": ["tech", "sharing"],
  "file_path": "Clippings/文章标题.md",
  "git_status": "Pull: OK | Add: OK | Commit: OK | Push: OK"
}
```

**调用示例：**

```bash
# 使用 curl
curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "小红书",
    "image_base64": "'$(base64 -i screenshot.png)'"
  }'
```

```python
# 使用 Python
import base64
import requests

with open("screenshot.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

response = requests.post(
    "http://localhost:8080/api/process",
    json={
        "app_name": "小红书",  # 可选
        "image_base64": image_base64
    }
)
print(response.json())
```

## 项目结构

```
ObsAgent/
├── config/
│   └── tags.yaml           # 标签配置
├── obs_agent/
│   ├── core/
│   │   └── agent.py        # ADK Agent
│   ├── tools/
│   │   ├── image_analyzer.py   # 图像分析
│   │   ├── tag_matcher.py      # 标签匹配
│   │   ├── obsidian_writer.py  # Obsidian 写入
│   │   └── git_manager.py      # Git 操作
│   ├── models/
│   │   └── article.py      # 数据模型
│   └── api/
│       ├── app.py          # FastAPI 应用
│       └── routes.py       # API 路由
└── tests/
```

## 标签配置

编辑 `config/tags.yaml` 自定义标签分类：

```yaml
categories:
  - id: topic
    name: 主题分类
    tags:
      - id: tech
        name: 科技
        keywords: [AI, 编程, 技术]
```

## Obsidian Bases 集成

文章保存为 Markdown + YAML Frontmatter 格式：

```yaml
---
title: "文章标题"
author: "作者"
source: "小红书"
tags:
  - tech
  - xiaohongshu
capture_date: 2026-01-17
summary: "摘要"
---
```

首次保存会自动创建 `Clippings.base` 文件用于数据库视图。

## 开发

安装开发依赖：

```bash
pip install -e ".[dev]"
```

运行测试：

```bash
pytest
```

## License

MIT
