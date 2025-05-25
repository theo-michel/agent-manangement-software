from datetime import datetime
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.github.schema import RepositoryStatusResponse
from app.models.models import RepoStatus, Repository

logger = logging.getLogger(__name__)

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
            # Count files from indexed_data if available
            file_count = 0
            if repository.indexed_data:
                documentation = repository.indexed_data.get("documentation", [])
                documentation_md = repository.indexed_data.get("documentation_md", [])
                config = repository.indexed_data.get("config", [])
                file_count = len(documentation) + len(documentation_md) + len(config)
            
            return RepositoryStatusResponse(
                status=repository.status,
                file_count=file_count,
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
            if status == RepoStatus.INDEXED:
                repository.indexed_at = datetime.utcnow()
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
                indexed_at=datetime.utcnow() if status == RepoStatus.INDEXED else None,
            )
            session.add(repository)
        
        await session.commit()
        await session.refresh(repository)
        return repository

    async def save_indexed_data(
        self,
        repository: Repository,
        documentation_data: Dict[str, Any],
        documentation_md_data: Dict[str, Any],
        config_data: Dict[str, Any],
        session: AsyncSession
    ) -> None:
        """
        Save indexed repository data to the single JSON field.
        
        Args:
            repository: The repository object
            documentation_data: JSON data from docstrings_json
            documentation_md_data: JSON data from ducomentations_json  
            config_data: JSON data from configs_json
            session: Database session
        """
        try:
            # Combine all data into a single JSON structure
            combined_data = {
                "documentation": documentation_data.get("documentation", []),
                "documentation_md": documentation_md_data.get("documentation_md", []),
                "config": config_data.get("config", []),
                "summary": {
                    "total_files": (
                        len(documentation_data.get("documentation", [])) +
                        len(documentation_md_data.get("documentation_md", [])) +
                        len(config_data.get("config", []))
                    ),
                    "indexed_at": datetime.utcnow().isoformat(),
                    "documentation_files": len(documentation_data.get("documentation", [])),
                    "markdown_files": len(documentation_md_data.get("documentation_md", [])),
                    "config_files": len(config_data.get("config", []))
                }
            }
            
            # Save to the single JSON field
            repository.indexed_data = combined_data
            repository.status = RepoStatus.INDEXED
            repository.indexed_at = datetime.utcnow()
            
            await session.commit()
            logger.info(f"Successfully saved indexed data for repository {repository.full_name}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving indexed data for repository {repository.full_name}: {str(e)}")
            raise

    async def get_indexed_data(
        self,
        owner: str,
        repo: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Retrieve indexed data for a repository.
        
        Returns:
            Dictionary containing all indexed data or empty dict if not found
        """
        result = await session.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo}")
        )
        repository = result.scalars().first()
        
        if repository and repository.indexed_data:
            return repository.indexed_data
        
        return {}