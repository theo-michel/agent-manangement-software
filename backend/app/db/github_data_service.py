   
   
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.extract_github.schema import RepositoryStatusResponse
from app.models.models import RepoStatus, Repository
   
   
   
   
   
class GithubDataService:
    
    async def get_repository_status(
        self, 
        owner: str, 
        repo: str, 
        session: AsyncSession
    ) -> RepositoryStatusResponse:
        """
        Get the status of a repository.
        """
        # Check if repository exists in the database
        result = await session.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo}")
        )
        repository = result.scalars().first()
        if repository:
            return RepositoryStatusResponse(
                status=repository.status,
                file_count=len(repository.files) if repository.files else None,
                indexed_at=repository.indexed_at.isoformat() if repository.indexed_at else None,
            )
        return RepositoryStatusResponse(status=RepoStatus.NOT_INDEXED, file_count=None, message="Repository not indexed yet")
    
    
    async def create_or_update_repository(
        self, 
        owner: str, 
        repo: str, 
        repo_info: Dict[str, Any],
        status: RepoStatus,
        session: AsyncSession
    ) -> Repository:
        """
        Create or update a repository in the database.
        """
        # Check if repository already exists
        result = await session.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo}")
        )
        repository = result.scalars().first()
        
        if repository:
            repository.status = status
            repository.github_id = repo_info["id"]
            repository.description = repo_info["description"]
            repository.default_branch = repo_info["default_branch"]
            repository.stars = repo_info["stars"]
            repository.forks = repo_info["forks"]
            repository.size = repo_info["size"]
            repository.updated_at = datetime.utcnow()
        else:
            repository = Repository(
                github_id=repo_info["id"],
                owner=owner,
                name=repo,
                full_name=f"{owner}/{repo}",
                description=repo_info["description"],
                default_branch=repo_info["default_branch"],
                stars=repo_info["stars"],
                forks=repo_info["forks"],
                size=repo_info["size"],
                status=status,
            )
            session.add(repository)
        
        await session.commit()
        await session.refresh(repository)
        return repository