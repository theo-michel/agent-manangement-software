from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import logging

from app.database import get_async_session
from app.models.repo_models import Repository, CodeUnit, RepoStatus
from app.services.extract_github.schema import ChatRequest, ChatResponse
from app.services.ai import AIService
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)

# Initialize services
ai_service = AIService(settings.OPENAI_API_KEY)


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
    
    # Initialize vector database service

    
    try:
        # Generate embedding for the query
        query_embedding = await ai_service.generate_embedding(chat_request.message)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding for query")
        
        
        # TODO Implement the retrieving @David
        results = None
        
        if not results:
            # If no results, provide a general response
            return ChatResponse(
                response="I couldn't find specific code in this repository that answers your question. Could you provide more details or rephrase your question?",
                code_snippets=[],
                source_files=[],
            )
        
        # Get code units for the matched results
        code_units = []
        source_files = []
        
        for result in results:
            if "code_unit_id" in result["metadata"]:
                code_unit_id = result["metadata"]["code_unit_id"]
                
                # Query database for code unit
                unit_result = await session.execute(
                    select(CodeUnit).where(CodeUnit.id == code_unit_id)
                )
                unit = unit_result.scalars().first()
                
                if unit:
                    code_units.append({
                        "id": unit.id,
                        "name": unit.name,
                        "type": unit.type,
                        "content": unit.content,
                        "description": unit.description,
                        "score": result["score"],
                        "path": result["metadata"]["path"],
                        "start_line": unit.start_line,
                        "end_line": unit.end_line,
                    })
                    
                    # Add source file
                    if result["metadata"]["path"] not in [file["path"] for file in source_files]:
                        source_files.append({
                            "path": result["metadata"]["path"],
                            "url": f"https://github.com/{owner}/{repo}/blob/{repository.default_branch}/{result['metadata']['path']}",
                        })
        
        # Generate the chat response using the AI service
        system_prompt = f"""You are an AI assistant that helps users understand code from the GitHub repository {owner}/{repo}.
Use the following code snippets as context to answer the user's question.
Be concise, clear, and helpful. Reference specific parts of the code when relevant.
If you don't know the answer, say so honestly and suggest what the user could look for instead."""
        
        # Build context from code units
        context = "\n\n".join([
            f"File: {unit['path']}\n"
            f"Code unit: {unit['name']} ({unit['type']})\n"
            f"Description: {unit['description']}\n"
            f"Content:\n```\n{unit['content']}\n```"
            for unit in code_units
        ])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nUser question: {chat_request.message}"}
        ]
        
        # Get AI response
        response = await ai_service.chat_completion(messages)
        
        # Format code snippets for response
        formatted_snippets = [
            {
                "name": unit["name"],
                "type": unit["type"],
                "path": unit["path"],
                "content": unit["content"],
                "start_line": unit["start_line"],
                "end_line": unit["end_line"],
                "relevance_score": unit["score"],
            }
            for unit in code_units
        ]
        
        return ChatResponse(
            response=response,
            code_snippets=formatted_snippets,
            source_files=source_files,
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}") 