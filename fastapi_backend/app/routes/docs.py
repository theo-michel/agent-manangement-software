from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import logging

from app.database import get_async_session
from app.models.repo_models import Repository, RepositoryFile, RepoStatus
from app.services.extract_github.schema import DocsResponse, FileDescription
from app.services.extract_github.service import GitHubService
from app.config import settings

router = APIRouter(prefix="/docs", tags=["documentation"])

logger = logging.getLogger(__name__)

# Initialize GitHub service
github_service = GitHubService(settings.GITHUB_TOKEN)


@router.get("/{owner}/{repo}", response_model=DocsResponse)
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
    try:
        repo_info = await github_service.get_repository_info(owner, repo)
    except ValueError as e:
        # Repository might be available in the database but not on GitHub anymore
        # Use information from the database
        repo_info = {
            "id": repository.github_id,
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "default_branch": repository.default_branch,
            "stars": repository.stars,
            "forks": repository.forks,
            "created_at": repository.created_at.isoformat(),
            "updated_at": repository.updated_at.isoformat(),
            "size": repository.size,
            "owner": {
                "login": owner,
                "id": None,  # We don't store this in the database
                "avatar_url": None,  # We don't store this in the database
            }
        }

    return DocsResponse(
        repository=repo_info,
        files=file_descriptions,
    )


@router.get("/{owner}/{repo}/file", response_model=FileDescription)
async def get_file_docs(
    owner: str, repo: str, path: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Get documentation for a specific file in a repository.
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

    # Get file with description
    result = await session.execute(
        select(RepositoryFile)
        .where(RepositoryFile.repository_id == repository.id)
        .where(RepositoryFile.path == path)
    )
    file = result.scalars().first()

    if not file:
        raise HTTPException(status_code=404, detail=f"File {path} not found in repository")

    return FileDescription(
        path=file.path,
        description=file.description or "",
        type=file.type,
        size=file.size,
        language=file.language,
    ) 