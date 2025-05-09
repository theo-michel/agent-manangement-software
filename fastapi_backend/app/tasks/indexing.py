import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy import update

from app.database import get_async_session
from app.models.models import Repository, RepositoryFile, CodeUnit, RepoStatus
from app.services.extract_github.service import GitHubService
from fastapi_backend.app.services.ai.service import AIService
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize services
github_service = GitHubService(settings.GITHUB_TOKEN)
ai_service = AIService(settings.OPENAI_API_KEY)


async def index_repository(
    owner: str, 
    repo: str, 
    repository_id: int, 
    branch: Optional[str] = None
) -> None:
    """
    Background task to index a repository.
    
    Args:
        owner: The GitHub username/organization
        repo: The repository name
        repository_id: The database ID of the repository
        branch: Optional branch to index (defaults to the repository's default branch)
    """
    # Connect to database
    async_session = get_async_session()
    session = await anext(async_session)
    
    try:
        # Update repository status to PENDING if not already
        await session.execute(
            update(Repository)
            .where(Repository.id == repository_id)
            .values(status=RepoStatus.PENDING)
        )
        await session.commit()
        
        # Get repository info
        repo_info = await github_service.get_repository_info(owner, repo)
        
        # Get repository's default branch if not specified
        if not branch:
            branch = repo_info["default_branch"]
        
        # Initialize vector database service with namespace for this repository
        
        # Get file tree from GitHub
        file_tree = await github_service.get_file_tree(owner, repo)
        # TODO @David do your magic here
        # Update repository status to INDEXED
        await session.execute(
            update(Repository)
            .where(Repository.id == repository_id)
            .values(status=RepoStatus.INDEXED, indexed_at=datetime.utcnow())
        )
        await session.commit()
        
    except Exception as e:
        logger.error(f"Error indexing repository {owner}/{repo}: {str(e)}")
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


def parse_code_into_units(content: str, language: Optional[str], file_path: str) -> List[Dict[str, Any]]:
    """
    Parse code into units (functions, classes, methods, etc.).
    
    This is a simple implementation. In a production environment, this would use
    a proper parser like tree-sitter for more accurate parsing.
    
    Args:
        content: The file content
        language: The programming language
        file_path: The file path
        
    Returns:
        A list of code units with name, type, start_line, end_line, and content
    """
    # Simple implementation for demonstration
    lines = content.split("\n")
    
    # If content is small, treat the whole file as one unit
    if len(lines) <= 20:
        return [
            {
                "name": os.path.basename(file_path),
                "type": "file",
                "start_line": 1,
                "end_line": len(lines),
                "content": content,
            }
        ]
    
    # For larger files, try to split into functions/classes (very basic approach)
    units = []
    
    if language == "Python":
        current_unit = None
        for i, line in enumerate(lines, 1):
            line_strip = line.strip()
            
            # Detect function or class definition
            if line_strip.startswith("def ") or line_strip.startswith("class "):
                # If we were tracking a unit, add it
                if current_unit:
                    current_unit["end_line"] = i - 1
                    current_unit["content"] = "\n".join(lines[current_unit["start_line"] - 1:i - 1])
                    units.append(current_unit)
                
                # Start new unit
                unit_type = "function" if line_strip.startswith("def ") else "class"
                name_end = line_strip.find("(") if unit_type == "function" else line_strip.find(":")
                if name_end == -1:
                    name_end = len(line_strip)
                    
                name = line_strip[4:name_end].strip() if unit_type == "function" else line_strip[6:name_end].strip()
                
                current_unit = {
                    "name": name,
                    "type": unit_type,
                    "start_line": i,
                    "end_line": None,
                    "content": None,
                }
        
        # Add the last unit if any
        if current_unit:
            current_unit["end_line"] = len(lines)
            current_unit["content"] = "\n".join(lines[current_unit["start_line"] - 1:])
            units.append(current_unit)
    
    # If we couldn't identify any units, treat the whole file as one unit
    if not units:
        units = [
            {
                "name": os.path.basename(file_path),
                "type": "file",
                "start_line": 1,
                "end_line": len(lines),
                "content": content,
            }
        ]
    
    return units 