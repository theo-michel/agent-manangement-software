from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_async_session
from app.services.extract_github.schema import DocsResponse, FileDescription
from fastapi_backend.app.services.docs.service import DocsService

router = APIRouter(prefix="/docs", tags=["documentation"])

logger = logging.getLogger(__name__)

# Initialize service
docs_service = DocsService()


@router.get("/{owner}/{repo}", response_model=DocsResponse)
async def get_repository_docs(
    owner: str, repo: str, session: AsyncSession = Depends(get_async_session)
):
    """ 
    Get documentation for a repository.
    """
    try:
        return await docs_service.get_repository_docs(owner, repo, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{owner}/{repo}/file", response_model=FileDescription)
async def get_file_docs(
    owner: str, repo: str, path: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Get documentation for a specific file in a repository.
    """
    try:
        return await docs_service.get_file_docs(owner, repo, path, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 