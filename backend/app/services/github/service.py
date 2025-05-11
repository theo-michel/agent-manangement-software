from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import stripe
import logging


from app.services.extract_github.service import GitHubService
from app.services.extract_github.schema import (
    RepositoryStatusResponse, 

    RepoStatus as SchemaRepoStatus
)
from app.config import settings
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from app.db.github_data_service import GithubDataService

logger = logging.getLogger(__name__)

class GithubService:
    def __init__(self):
        self.github_service = GitHubService(settings.GITHUB_TOKEN)
        self.github_data_service = GithubDataService()
        if settings.STRIPE_API_KEY:
            stripe.api_key = settings.STRIPE_API_KEY

    def clone_github_repo(self, folder_path: str, repo_url: str) -> Optional[str]:
        """
        Clone a GitHub repository into a specified folder or return path if already cloned.

        Args:
            folder_path (str): The path where the repository should be cloned
            repo_url (str): The GitHub repository URL (e.g., 'https://github.com/username/repo')

        Returns:
            Optional[str]: The path to the cloned repository if successful, None if failed

        Raises:
            ValueError: If the inputs are invalid
            subprocess.CalledProcessError: If the git clone operation fails
        """
        # Validate inputs
        if not folder_path or not repo_url:
            raise ValueError("Both folder_path and repo_url must be provided")

        # Parse the repository URL to get the repository name
        parsed_url = urlparse(repo_url.rstrip("/"))
        if not parsed_url.path:
            raise ValueError("Invalid GitHub repository URL")

        # Extract repository name from the URL path
        # Handle both 'github.com/owner/repo' and 'github.com/owner/repo.git'
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) != 2:
            raise ValueError("Invalid GitHub repository URL format")

        repo_name = path_parts[1].replace(".git", "")

        # Create the target directory if it doesn't exist
        folder_path = Path(folder_path).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)

        # Generate the full path where the repository will be cloned
        repo_path = folder_path / repo_name

        # If repository already exists and has .git folder, return its path
        logger.info(f"Repository path: {repo_path}")
        if repo_path.exists() or (repo_path / ".git").exists():
            return str(repo_path)

        try:
            # Check if git is installed
            subprocess.run(["git", "--version"], check=True, capture_output=True)

            # Construct the git URL
            git_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}.git"

            # Clone the repository
            subprocess.run(
                ["git", "clone", git_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Verify the repository was cloned successfully
            if not (repo_path / ".git").exists():
                raise subprocess.CalledProcessError(1, "git clone")

            return str(repo_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository: {e}")
            if e.stderr:
                logger.error(f"Git error message: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    async def get_repository_status(
        self, owner: str, repo: str, session: AsyncSession
    ) -> RepositoryStatusResponse:
        """
        Get the status of a repository.
        """
        repository_status = await self.github_data_service.get_repository_status(owner=owner, repo=repo, session=session)
        if repository_status.status != SchemaRepoStatus.NOT_INDEXED:
            return repository_status

        try:
            file_count = await self.github_service.count_files(owner, repo)
            return RepositoryStatusResponse(
                status=SchemaRepoStatus.NOT_INDEXED,
                file_count=file_count,
                message="Repository not indexed yet",
            )
        except ValueError as e:
            logger.error(f"Error getting file count: {str(e)}")
            raise ValueError(f"Repository not found or access denied: {owner}/{repo}")
