from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_async_session
from app.services.github.schema import ChatRequest, ChatResponse, AgentRequest, AgentResponse
from app.services.chat.service import ChatService
from app.services.agent.service import AgentService

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)

# Initialize services
chat_service = ChatService()
agent_service = AgentService()


@router.post("/{owner}/{repo}", response_model=ChatResponse)
async def chat_with_repository(
    owner: str,
    repo: str,
    chat_request: ChatRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Chat with a repository using AI-powered understanding of the codebase.
    """
    try:
        return await chat_service.chat_with_repository(owner, repo, chat_request, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agent", response_model=AgentResponse)
async def trigger_agent(
    agent_request: AgentRequest,
):
    """
    Simple mock endpoint that takes a prompt and triggers an agent.
    """
    try:
        return await agent_service.process_prompt(agent_request)
    except Exception as e:
        logger.error(f"Error processing agent request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}") 