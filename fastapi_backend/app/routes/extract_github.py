from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List, Dict, Any, Optional
import stripe
from datetime import datetime

from app.database import get_async_session
from app.config import settings
from app.models.repo_models import Repository, RepositoryFile, CodeUnit, RepoStatus
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

router = APIRouter(prefix="/repos", tags=["repository"])

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

# Initialize GitHub service
github_service = GitHubService(settings.GITHUB_TOKEN)


@router.get("/{owner}/{repo}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    owner: str, repo: str, session: AsyncSession = Depends(get_async_session)
):
    """
    Check the indexing status of a repository.
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

    # Repository not in database, get file count for estimation
    try:
        file_count = await github_service.count_files(owner, repo)
        return RepositoryStatusResponse(
            status=RepoStatus.NOT_INDEXED,
            file_count=file_count,
            message="Repository not indexed yet",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{owner}/{repo}/index", response_model=CheckoutResponse)
async def index_repository(
    owner: str,
    repo: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Start the indexing process for a repository.
    Creates a Stripe checkout session for payment.
    """
    # Check repository status
    result = await session.execute(
        select(Repository).where(Repository.full_name == f"{owner}/{repo}")
    )
    repository = result.scalars().first()

    # If already indexed or pending, return status
    if repository and repository.status in [RepoStatus.INDEXED, RepoStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Repository already {repository.status.value}",
        )

    # Get repository information from GitHub
    try:
        repo_info = await github_service.get_repository_info(owner, repo)
        file_count = await github_service.count_files(owner, repo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Calculate price (e.g., $0.01 per file with a cap)
    price_per_file = settings.PRICE_PER_FILE  # e.g., 0.01 in dollars
    max_price = settings.MAX_PRICE  # e.g., 10.00 in dollars
    total_price = min(file_count * price_per_file, max_price)
    
    # Format price for Stripe (in cents)
    price_in_cents = int(total_price * 100)
    
    if price_in_cents <= 0:
        price_in_cents = 100  # Minimum $1

    # Create or update repository in database
    if repository:
        repository.status = RepoStatus.PENDING
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
            status=RepoStatus.PENDING,
        )
        session.add(repository)
    
    await session.commit()
    await session.refresh(repository)

    # Create Stripe checkout session
    if not settings.STRIPE_API_KEY:
        # For development without Stripe, start indexing immediately
        background_tasks.add_task(
            start_indexing_task, owner, repo, repository.id
        )
        return CheckoutResponse(checkout_url="http://localhost:8000/mock-payment-success")

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Index Repository: {owner}/{repo}",
                        "description": f"Indexing {file_count} files for AI-powered documentation and chat",
                    },
                    "unit_amount": price_in_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{settings.FRONTEND_URL}/{owner}/{repo}?success=true",
        cancel_url=f"{settings.FRONTEND_URL}/{owner}/{repo}?canceled=true",
        metadata={
            "repository_id": repository.id,
            "owner": owner,
            "repo": repo,
        },
    )

    # Update repository with checkout session ID
    repository.checkout_session_id = checkout_session.id
    await session.commit()

    return CheckoutResponse(checkout_url=checkout_session.url)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Dict[str, Any], session: AsyncSession = Depends(get_async_session)
):
    """
    Webhook for handling Stripe payment events.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        # For development without Stripe webhook
        return {"status": "success"}

    # Get the signature from headers
    signature = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session_id = event["data"]["object"]["id"]
        
        # Get repository from database using session_id
        result = await session.execute(
            select(Repository).where(Repository.checkout_session_id == session_id)
        )
        repository = result.scalars().first()
        
        if repository:
            # Start indexing task
            background_tasks = BackgroundTasks()
            background_tasks.add_task(
                start_indexing_task, 
                repository.owner, 
                repository.name, 
                repository.id
            )
            
            return {"status": "success"}
    
    return {"status": "ignored"}


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
