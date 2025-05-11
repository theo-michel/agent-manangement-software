from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import stripe

import logging

from app.database import get_async_session
from app.config import settings
from app.models.models import Repository, RepositoryFile, RepoStatus
from app.services.github.schema import (
    RepositoryInfo,
    RepositoryStatusResponse,
    CheckoutResponse,
    DocsResponse,
    FileDescription,
)
from app.services.indexer.service import IndexerService
from app.services.github.service import GithubService


router = APIRouter(prefix="/repos", tags=["repository"])
logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

# Initialize GitHub service
github_service = GithubService()
indexer_service = IndexerService()

@router.get("/{owner}/{repo}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    owner: str, repo: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Check the indexing status of a repository.
    """
    try:
        return await github_service.get_repository_status(owner, repo, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{owner}/{repo}/index", response_model=CheckoutResponse)
async def index_repository(
    owner: str,
    repo: str,
):
    """
    Start the indexing process for a repository.
    Creates a Stripe checkout session for payment.
    """
    try:
        cache_name = indexer_service.insert_index_and_cache(f"https://github.com/{owner}/{repo}") # TODO make this into owner and repo
        return CheckoutResponse(cache_name=cache_name)
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
            detail=f"Repository is not indexed. Current status: {repository.status.value}",
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



@router.get("/{owner}/{repo}/info", response_model=RepositoryInfo)
async def get_github_repo_info(owner: str, repo: str):
    """
    Get basic information about a GitHub repository.
    """
    repo_info = await github_service.get_repository_info(owner, repo)
    return repo_info
