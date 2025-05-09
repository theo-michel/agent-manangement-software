from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.services.extract_github.service import GitHubService
from app.services.extract_github.schema import DocsResponse, FileDescription
from app.models.models import Repository, RepositoryFile, RepoStatus
from app.config import settings

logger = logging.getLogger(__name__)

class DocsService:
    def __init__(self, github_service: GitHubService = None):
        self.github_service = github_service or GitHubService(settings.GITHUB_TOKEN)
        
    async def validate_repository(
        self, owner: str, repo: str, #session: AsyncSession
    ) -> Repository:
        """
        Validate that a repository exists and is indexed.
        Raises ValueError if not found or not indexed.
        """
    #     result = await session.execute(
    #         select(Repository).where(Repository.full_name == f"{owner}/{repo}")
    #     )
    #     repository = result.scalars().first()

    #     if not repository:
    #         raise ValueError("Repository not found")
        
    #     if repository.status != RepoStatus.INDEXED:
    #         raise ValueError(f"Repository is not indexed. Current status: {repository.status.value}")
            
    #     return repository
    
    # async def get_repository_docs(
    #     self, owner: str, repo: str, session: AsyncSession
    # ) -> DocsResponse:
    #     """
    #     Get documentation for a repository.
    #     """
    #     # Validate repository
    #     repository = await self.validate_repository(owner, repo, session)

    #     # Get files with descriptions
    #     result = await session.execute(
    #         select(RepositoryFile).where(RepositoryFile.repository_id == repository.id)
    #     )
    #     files = result.scalars().all()

    #     # Format file descriptions
    #     file_descriptions = [
    #         FileDescription(
    #             path=file.path,
    #             description=file.description or "",
    #             type=file.type,
    #             size=file.size,
    #             language=file.language,
    #         )
    #         for file in files
    #     ]

        # Get repository info from GitHub or fallback to database
        try:
            repo_info = await self.github_service.get_repository_info(owner, repo)
            print("Here is the repo")
            print(repo_info)
        except ValueError as e:
            pass
        #     logger.warning(f"Could not fetch repository info from GitHub: {str(e)}")
        #     # Fallback to database info
        #     repo_info = {
        #         "id": repository.github_id,
        #         "name": repository.name,
        #         "full_name": repository.full_name,
        #         "description": repository.description,
        #         "default_branch": repository.default_branch,
        #         "stars": repository.stars,
        #         "forks": repository.forks,
        #         "created_at": repository.created_at.isoformat(),
        #         "updated_at": repository.updated_at.isoformat(),
        #         "size": repository.size,
        #         "owner": {
        #             "login": owner,
        #             "id": None,  # We don't store this in the database
        #             "avatar_url": None,  # We don't store this in the database
        #         }
        #     }

        # return DocsResponse(
        #     repository=repo_info,
        #     files=file_descriptions,
        # )
    
    async def get_file_docs(
        self, owner: str, repo: str, path: str, session: AsyncSession
    ) -> FileDescription:
        """
        Get documentation for a specific file in a repository.
        """
        # Validate repository
        repository = await self.validate_repository(owner, repo, session)

        # Get file with description
        result = await session.execute(
            select(RepositoryFile)
            .where(RepositoryFile.repository_id == repository.id)
            .where(RepositoryFile.path == path)
        )
        file = result.scalars().first()

        if not file:
            raise ValueError(f"File {path} not found in repository")

        return FileDescription(
            path=file.path,
            description=file.description or "",
            type=file.type,
            size=file.size,
            language=file.language,
        ) 