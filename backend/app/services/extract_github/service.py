import os
import base64
from typing import Dict, List, Optional, Any, Tuple
import httpx
from github import Github, GithubException
import logging

from app.services.extract_github.schema import FileNode, RepositoryInfo, RepositoryOwner

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self, github_token: str = None):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.github_client = Github(self.github_token)
        self.httpx_client = httpx.AsyncClient(
            headers={"Authorization": f"token {self.github_token}"} if self.github_token else {},
            timeout=60.0,
        )
        
    async def get_repository_info(self, owner: str, repo: str) -> RepositoryInfo:
        """Get basic repository information."""
        try:
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            return RepositoryInfo(
                id=repo_obj.id,
                name=repo_obj.name,
                full_name=repo_obj.full_name,
                description=repo_obj.description,
                default_branch=repo_obj.default_branch,
                stars=repo_obj.stargazers_count,
                forks=repo_obj.forks_count,
                created_at=repo_obj.created_at.isoformat(),
                updated_at=repo_obj.updated_at.isoformat(),
                size=repo_obj.size,
                owner=RepositoryOwner(
                    login=repo_obj.owner.login,
                    id=repo_obj.owner.id,
                    avatar_url=repo_obj.owner.avatar_url,
                )
            )
        except GithubException as e:
            logger.error(f"Error fetching repository info: {str(e)}")
            raise ValueError(f"Repository not found or access denied: {owner}/{repo}")
            
    async def get_file_tree(self, owner: str, repo: str, recursive: bool = True) -> List[FileNode]:
        """Get the file tree of a repository."""
        try:
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            branch = repo_obj.default_branch
            
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive={str(recursive).lower()}"
            response = await self.httpx_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            file_nodes = []
            
            for item in data.get("tree", []):
                if item["type"] in ["blob", "tree"]:
                    file_nodes.append(
                        FileNode(
                            path=item["path"],
                            type="file" if item["type"] == "blob" else "directory",
                            size=item.get("size")
                        )
                    )
            
            return file_nodes
        except (GithubException, httpx.HTTPError) as e:
            logger.error(f"Error fetching file tree: {str(e)}")
            raise ValueError(f"Error fetching file tree for {owner}/{repo}")
    
    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
        """Get the content of a file."""
        try:
            repo_obj = self.github_client.get_repo(f"{owner}/{repo}")
            if not ref:
                ref = repo_obj.default_branch
                
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
            response = await self.httpx_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get("encoding") == "base64" and data.get("content"):
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                return content
            else:
                raise ValueError(f"Unexpected content format for file {path}")
        except (GithubException, httpx.HTTPError) as e:
            logger.error(f"Error fetching file content: {str(e)}")
            raise ValueError(f"Error fetching content for {path} in {owner}/{repo}")
    
    async def count_files(self, owner: str, repo: str) -> int:
        """Count the number of files in a repository."""
        file_tree = await self.get_file_tree(owner, repo)
        return sum(1 for node in file_tree if node.type == "file")
    
    async def close(self):
        """Close the HTTP client."""
        if self.httpx_client:
            await self.httpx_client.aclose()
