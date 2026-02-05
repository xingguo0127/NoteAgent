# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ObsAgent is a screenshot information extraction agent that processes screenshots from Bilibili, Xiaohongshu, and WeChat Official Accounts, then saves extracted content to an Obsidian vault with automatic Git synchronization.

**Tech Stack**: Python 3.11+, FastAPI/Uvicorn, LiteLLM + OpenRouter (Gemini 2.5 Flash), Pydantic, httpx

## Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run server (development with auto-reload)
python -m obs_agent --reload

# Run server (production)
python -m obs_agent --host 0.0.0.0 --port 8080

# Using startup scripts
./start.sh [--port PORT] [--host HOST]
./stop.sh [--force]

# Run tests
pytest
```

## Architecture

### Processing Pipeline (`POST /api/process`)

1. Decode Base64 image → detect MIME type
2. Git pull to update local vault
3. Analyze screenshot via Gemini 2.5 Flash (extract title, author, summary, content, publish_date)
4. Detect source platform from app_name
5. Match tags using AI against `config/tags.yaml`
6. Write Markdown + YAML frontmatter to Obsidian vault (URL from request body)
7. Git add → commit → push
8. Return ProcessResponse with success status and git_status

### Key Modules (`obs_agent/tools/`)

| Module | Purpose |
|--------|---------|
| `image_analyzer.py` | Screenshot analysis via LiteLLM multimodal API |
| `tag_matcher.py` | AI-based tag matching with YAML config |
| `obsidian_writer.py` | Write articles to vault with frontmatter |
| `git_manager.py` | Git operations (pull/add/commit/push) via subprocess |

### API Endpoints (`obs_agent/api/routes.py`)

- `POST /api/process` - Main processing endpoint
- `GET /api/health` - Health check
- `GET /docs` - Swagger documentation

### Data Models (`obs_agent/models/article.py`)

- `ProcessRequest` - Input: app_name + image_base64 + url
- `ProcessResponse` - Output: extracted data + file_path + git_status
- `AnalyzeResult` - Screenshot analysis result
- `Article` - Complete article with metadata

## Configuration

Environment variables (`.env`):
- `OPENROUTER_API_KEY` - Required for LLM API
- `OBSIDIAN_VAULT_PATH` - Local vault path
- `OBSIDIAN_GIT_REPO` - GitHub repo URL (SSH recommended)
- `LLM_MODEL` - Default: `openrouter/google/gemini-2.5-flash-preview`

Tag categories defined in `config/tags.yaml`:
- Topic tags: `ai/`, `hardware/`, `dev/`, `creative/`, `productivity/`, `life/`
- Content type: `type/tutorial`, `type/news`, `type/review`, `type/insight`, `type/resource`, `type/reference`

## Design Patterns

- **Async-first**: All tool functions are async
- **Tuple Returns**: Git operations return `(success: bool, message: str)` for partial failure handling
- **Pydantic Models**: Strong typing with validation throughout
