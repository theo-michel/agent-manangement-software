from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List, Dict, Any, Optional
import stripe
from datetime import datetime
import logging

from app.database import get_async_session
from app.config import settings
from app.models.models import Repository, RepositoryFile, CodeUnit, RepoStatus
from app.services.extract_github.schema import (
    RepositoryStatusResponse,
    IndexingRequest,
    CheckoutResponse,
    ChatRequest,
    ChatResponse,
    DocsResponse,
    FileDescription,
)
from app.services.extract_github.service import GitHubService
from backend.app.services.github_repository.service import GithubRepositoryService

router = APIRouter(prefix="/repos", tags=["repository"])
logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

# Initialize GitHub service
github_service = GitHubService(settings.GITHUB_TOKEN)

# Initialize service
repository_service = GithubRepositoryService()


@router.get("/{owner}/{repo}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    owner: str, repo: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Check the indexing status of a repository.
    """
    try:
        return await repository_service.get_repository_status(owner, repo, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{owner}/{repo}/index", response_model=CheckoutResponse)
async def index_repository(
    owner: str,
    repo: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Start the indexing process for a repository.
    Creates a Stripe checkout session for payment.
    """
    try:
        return await repository_service.start_indexing(owner, repo, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request, session: AsyncSession = Depends(get_async_session)
):
    """
    Webhook for handling Stripe payment events.
    """
    try:
        return await repository_service.process_webhook(request, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{owner}/{repo}/docs", response_model=DocsResponse)
async def get_repository_docs(
    owner: str, repo: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Get documentation for a repository.
    """
    # Check if repository exists and is indexed
    result = await session.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo}")
    )
    repository = result.scalars().first()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if repository.status != RepoStatus.INDEXED:
        raise HTTPException(
            status_code=400, 
            detail=f"Repository is not indexed. Current status: {repository.status.value}"
        )

    # Get files with descriptions
    result = await session.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repository.id)
    )
    files = result.scalars().all()

    # Format response
    file_descriptions = [
        FileDescription(
            path=file.path,
            description=file.description or "",
            type=file.type,
            size=file.size,
            language=file.language,
        )
        for file in files
    ]

    # Get repository info
    repo_info = await github_service.get_repository_info(owner, repo)

    return DocsResponse(
        repository=repo_info,
        files=file_descriptions,
    )


@router.post("/{owner}/{repo}/chat", response_model=ChatResponse)
async def chat_with_repository(
    owner: str,
    repo: str,
    chat_request: ChatRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Chat with a repository.
    """
    # Check if repository exists and is indexed
    result = await session.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo}")
    )
    repository = result.scalars().first()

    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if repository.status != RepoStatus.INDEXED:
        raise HTTPException(
            status_code=400, 
            detail=f"Repository is not indexed. Current status: {repository.status.value}"
        )

    # TODO: Implement chat functionality with vector database and LLM
    # This is a placeholder implementation
    
    return ChatResponse(
        response=f"This is a placeholder response for the query: {chat_request.message}",
        code_snippets=[],
        source_files=[],
    )


async def start_indexing_task(owner: str, repo: str, repository_id: int):
    """
    Background task to index a repository.
    """
    # This function would be implemented as a Celery task in a production environment
    # For now, it's a placeholder for the indexing process
    
    # 1. Connect to database
    async_session = get_async_session()
    session = await anext(async_session)
    
    try:
        # 2. Update repository status to PENDING if not already
        await session.execute(
            update(Repository)
            .where(Repository.id == repository_id)
            .values(status=RepoStatus.PENDING)
        )
        await session.commit()
        
        # 3. Get file tree from GitHub
        file_tree = await github_service.get_file_tree(owner, repo)
        
        # 4. Process each file
        for file_node in file_tree:
            if file_node.type == "file":
                # Skip non-code files, binaries, etc.
                if should_process_file(file_node.path):
                    # Get file content
                    content = await github_service.get_file_content(owner, repo, file_node.path)
                    
                    # Create file in database
                    db_file = RepositoryFile(
                        repository_id=repository_id,
                        path=file_node.path,
                        type="file",
                        size=file_node.size,
                        language=detect_language(file_node.path),
                    )
                    session.add(db_file)
                    await session.commit()
                    await session.refresh(db_file)
                    
                    # TODO: Parse code into units (functions, classes, etc.)
                    # TODO: Generate descriptions for file and code units
                    # TODO: Generate embeddings and store in vector database
        
        # 5. Update repository status to INDEXED
        await session.execute(
            update(Repository)
            .where(Repository.id == repository_id)
            .values(status=RepoStatus.INDEXED, indexed_at=datetime.utcnow())
        )
        await session.commit()
        
    except Exception as e:
        # Update repository status to FAILED
        await session.execute(
            update(Repository)
            .where(Repository.id == repository_id)
            .values(status=RepoStatus.FAILED)
        )
        await session.commit()
        raise e
    finally:
        await session.close()


def should_process_file(path: str) -> bool:
    """
    Determine if a file should be processed based on its path.
    """
    # Skip binary files, non-code files, etc.
    skip_extensions = [
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
        ".pdf", ".zip", ".tar", ".gz", ".rar",
        ".mp3", ".mp4", ".wav", ".avi", ".mov",
        ".woff", ".woff2", ".ttf", ".eot",
        ".lock", ".bin", ".exe", ".dll",
    ]
    
    # Skip certain directories
    skip_directories = [
        "node_modules/",
        ".git/",
        "__pycache__/",
        "dist/",
        "build/",
        "vendor/",
    ]
    
    # Check if path contains any skip directory
    for directory in skip_directories:
        if directory in path:
            return False
    
    # Check file extension
    for ext in skip_extensions:
        if path.endswith(ext):
            return False
    
    return True


def detect_language(path: str) -> Optional[str]:
    """
    Detect the programming language based on file extension.
    """
    language_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React",
        ".tsx": "React TypeScript",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".md": "Markdown",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".sh": "Shell",
        ".bash": "Bash",
    }
    
    for ext, lang in language_map.items():
        if path.endswith(ext):
            return lang
    
    return None
