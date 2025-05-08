from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.models.repo_models import Repository, CodeUnit, RepoStatus
from app.services.extract_github.schema import ChatRequest, ChatResponse
from app.services.ai import AIService
from app.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, ai_service: AIService = None):
        self.ai_service = ai_service or AIService(settings.OPENAI_API_KEY)
        
    async def validate_repository(
        self, owner: str, repo: str, session: AsyncSession
    ) -> Repository:
        """
        Validate that a repository exists and is indexed.
        Raises ValueError if not found or not indexed.
        """
        result = await session.execute(
            select(Repository).where(Repository.full_name == f"{owner}/{repo}")
        )
        repository = result.scalars().first()

        if not repository:
            raise ValueError("Repository not found")
        
        if repository.status != RepoStatus.INDEXED:
            raise ValueError(f"Repository is not indexed. Current status: {repository.status.value}")
            
        return repository
    
    async def get_relevant_code_units(
        self, 
        query_embedding: List[float],
        repository_id: int,
        owner: str,
        repo: str,
        repository_default_branch: str,
        session: AsyncSession
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
        """
        Get code units relevant to the given query.
        This is a placeholder that would normally use a vector DB.
        
        Returns a tuple of (code_units, source_files).
        """
        # This is a placeholder implementation
        # In a real implementation, this would query a vector database using the embedding
        
        # Get a few code units from the repository for demonstration
        result = await session.execute(
            select(CodeUnit)
            .where(CodeUnit.repository_id == repository_id)
            .limit(3)
        )
        units = result.scalars().all()
        
        if not units:
            return [], []
            
        code_units = []
        source_files = []
        
        # Process each unit
        for unit in units:
            # Get the file for this unit
            file_result = await session.execute(
                select(Repository.files).where(Repository.id == repository_id)
            )
            files = file_result.scalars().all()
            file = next((f for f in files if f.id == unit.file_id), None)
            
            if file:
                # Add code unit
                code_units.append({
                    "id": unit.id,
                    "name": unit.name,
                    "type": unit.type,
                    "content": unit.content,
                    "description": unit.description,
                    "score": 0.9,  # Mocked relevance score
                    "path": file.path,
                    "start_line": unit.start_line,
                    "end_line": unit.end_line,
                })
                
                # Add source file if not already added
                if file.path not in [f["path"] for f in source_files]:
                    source_files.append({
                        "path": file.path,
                        "url": f"https://github.com/{owner}/{repo}/blob/{repository_default_branch}/{file.path}",
                    })
        
        return code_units, source_files
        
    async def chat_with_repository(
        self, 
        owner: str, 
        repo: str, 
        chat_request: ChatRequest, 
        session: AsyncSession
    ) -> ChatResponse:
        """
        Chat with a repository.
        """
        # Validate repository
        repository = await self.validate_repository(owner, repo, session)
        
        try:
            # Generate embedding for the query
            query_embedding = await self.ai_service.generate_embedding(chat_request.message)
            
            if not query_embedding:
                raise ValueError("Failed to generate embedding for query")
            
            # Get relevant code units
            code_units, source_files = await self.get_relevant_code_units(
                query_embedding=query_embedding,
                repository_id=repository.id,
                owner=owner,
                repo=repo,
                repository_default_branch=repository.default_branch,
                session=session
            )
            
            if not code_units:
                # If no results, provide a general response
                return ChatResponse(
                    response="I couldn't find specific code in this repository that answers your question. Could you provide more details or rephrase your question?",
                    code_snippets=[],
                    source_files=[],
                )
            
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
            response = await self.ai_service.chat_completion(messages)
            
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
            raise ValueError(f"Error processing chat request: {str(e)}") 