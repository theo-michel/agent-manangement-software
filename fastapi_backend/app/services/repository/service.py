from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import stripe
import logging
import json
from fastapi import Request

from app.services.extract_github.service import GitHubService
from app.services.extract_github.schema import (
    RepositoryStatusResponse, 
    CheckoutResponse,
    RepoStatus as SchemaRepoStatus
)
from app.models.repo_models import Repository, RepositoryFile, RepoStatus
from app.config import settings
from app.tasks.indexing import index_repository

logger = logging.getLogger(__name__)

class RepositoryService:
    def __init__(self, github_service: GitHubService = None):
        self.github_service = github_service or GitHubService(settings.GITHUB_TOKEN)
        if settings.STRIPE_API_KEY:
            stripe.api_key = settings.STRIPE_API_KEY
        
    async def get_repository_status(
        self, owner: str, repo: str, session: AsyncSession
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

        # Repository not in database, get file count for estimation
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
    
    async def start_indexing(
        self, 
        owner: str, 
        repo: str, 
        session: AsyncSession,
    ) -> CheckoutResponse:
        """
        Start the indexing process for a repository.
        """
        # Check repository status
        result = await session.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo}")
        )
        repository = result.scalars().first()

        # If already indexed or pending, raise an error
        if repository and repository.status in [RepoStatus.INDEXED, RepoStatus.PENDING]:
            raise ValueError(f"Repository already {repository.status.value}")

        # Get repository information from GitHub
        try:
            repo_info = await self.github_service.get_repository_info(owner, repo)
            file_count = await self.github_service.count_files(owner, repo)
        except ValueError as e:
            logger.error(f"Error getting repository info: {str(e)}")
            raise ValueError(f"Repository not found or access denied: {owner}/{repo}")

        # Calculate price
        price_per_file = settings.PRICE_PER_FILE
        max_price = settings.MAX_PRICE
        total_price = min(file_count * price_per_file, max_price)
        
        # Format price for Stripe (in cents)
        price_in_cents = int(total_price * 100)
        
        if price_in_cents <= 0:
            price_in_cents = 100  # Minimum $1

        # Create or update repository
        repository = await self.create_or_update_repository(
            owner=owner,
            repo=repo,
            repo_info=repo_info,
            status=RepoStatus.PENDING,
            session=session
        )

        # If Stripe API key not set, start indexing immediately (development mode)
        if not settings.STRIPE_API_KEY:
            # Start indexing task directly
            await index_repository(owner, repo, repository.id)
            return CheckoutResponse(checkout_url="http://localhost:8000/mock-payment-success")

        # Create Stripe checkout session
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
    
    async def process_webhook(
        self, 
        request: Request,
        session: AsyncSession
    ) -> Dict[str, str]:
        """
        Process Stripe webhook requests.
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            # For development without Stripe webhook
            return {"status": "success"}

        # Get the signature from headers
        signature = request.headers.get("stripe-signature")
        if not signature:
            raise ValueError("Missing Stripe signature")
            
        # Get the request body
        payload = await request.body()
        
        try:
            # Verify and construct the event
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

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
                await index_repository(repository.owner, repository.name, repository.id)
                return {"status": "success"}
        
        return {"status": "ignored"} 