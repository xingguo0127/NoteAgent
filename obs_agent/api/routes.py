"""API routes for ObsAgent."""

import base64
from datetime import date

from fastapi import APIRouter, HTTPException

from obs_agent.models import Article, ProcessRequest, ProcessResponse
from obs_agent.tools import (
    GitManager,
    ImageAnalyzer,
    ObsidianWriter,
    TagMatcher,
    fetch_source_url,
)

router = APIRouter(prefix="/api")


@router.post("/process", response_model=ProcessResponse)
async def process_screenshot(request: ProcessRequest) -> ProcessResponse:
    """Process a screenshot: analyze, save to Obsidian, and sync with Git.

    Complete workflow:
    1. Git pull to update local Obsidian vault
    2. Analyze screenshot using AI
    3. Match tags for the content
    4. Write article to Obsidian vault
    5. Git commit and push changes

    Args:
        request: ProcessRequest with app_name (optional) and image_base64

    Returns:
        ProcessResponse with status and extracted information
    """
    try:
        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")

        # Detect mime type from image data or default to PNG
        mime_type = "image/png"
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            mime_type = "image/gif"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            mime_type = "image/webp"

        # Step 1: Git pull to update local vault
        git_manager = GitManager()
        pull_success, pull_msg = git_manager.pull()
        if not pull_success:
            return ProcessResponse(
                success=False,
                message=f"Git pull failed: {pull_msg}",
                git_status=pull_msg,
            )

        # Step 2: Analyze screenshot
        analyzer = ImageAnalyzer()
        result = await analyzer.analyze(image_data, mime_type)

        # Use provided app_name if available, otherwise use detected one
        app_name = request.app_name if request.app_name else result.app_name

        # Step 3: Match tags
        matcher = TagMatcher()
        tags = await matcher.match_tags(result)

        # Step 3.5: Fetch source URL
        source_url = await fetch_source_url(app_name, result.title, result.author)

        # Step 4: Write to Obsidian
        writer = ObsidianWriter()
        article = Article(
            title=result.title,
            author=result.author,
            source=app_name,
            summary=result.summary,
            content=result.content,
            tags=tags,
            capture_date=date.today(),
            url=source_url,
        )
        file_path = writer.write_article(article)

        # Step 5: Git commit and push
        commit_message = f"Add: {result.title[:50]}" if result.title else f"Add clipping from {app_name}"

        # Add changes
        add_success, add_msg = git_manager.add_all()
        if not add_success:
            return ProcessResponse(
                success=False,
                message=f"Git add failed: {add_msg}",
                app_name=app_name,
                title=result.title,
                author=result.author,
                summary=result.summary,
                tags=tags,
                file_path=file_path,
                git_status=f"Pull: OK | Add: {add_msg}",
                url=source_url,
            )

        # Commit
        commit_success, commit_msg = git_manager.commit(commit_message)
        if not commit_success:
            return ProcessResponse(
                success=False,
                message=f"Git commit failed: {commit_msg}",
                app_name=app_name,
                title=result.title,
                author=result.author,
                summary=result.summary,
                tags=tags,
                file_path=file_path,
                git_status=f"Pull: OK | Add: OK | Commit: {commit_msg}",
                url=source_url,
            )

        # Push (only if there were changes committed)
        git_status = f"Pull: OK | Add: OK | Commit: {commit_msg}"
        if "No changes to commit" not in commit_msg:
            push_success, push_msg = git_manager.push()
            if not push_success:
                return ProcessResponse(
                    success=False,
                    message=f"Git push failed: {push_msg}",
                    app_name=app_name,
                    title=result.title,
                    author=result.author,
                    summary=result.summary,
                    tags=tags,
                    file_path=file_path,
                    git_status=f"Pull: OK | Add: OK | Commit: OK | Push: {push_msg}",
                    url=source_url,
                )
            git_status = f"Pull: OK | Add: OK | Commit: OK | Push: OK"

        return ProcessResponse(
            success=True,
            message=f"Article saved and synced: {file_path}",
            app_name=app_name,
            title=result.title,
            author=result.author,
            summary=result.summary,
            tags=tags,
            file_path=file_path,
            git_status=git_status,
            url=source_url,
        )

    except HTTPException:
        raise
    except Exception as e:
        return ProcessResponse(
            success=False,
            message=f"Processing failed: {str(e)}",
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
