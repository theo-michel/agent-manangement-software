from enum import Enum
from typing import List, Dict, Any, Literal, Optional

from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    code_snippets: Optional[List[Dict[str, Any]]] = None
    source_files: Optional[List[Dict[str, str]]] = None


class RepositoryStatusResponse(BaseModel):
    status: str
    file_count: Optional[int] = None
    indexed_at: Optional[str] = None
    message: Optional[str] = None


class AgentRequest(BaseModel):
    """Generic request for any agent that takes a simple prompt."""

    prompt: str
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Generic response for an agent that returns a simple text response."""

    response: str
    agent_id: str
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None


class TaskType(str, Enum):
    """The types of tasks our agent can create. Start with one, add more later."""

    RESEARCH = "research_task"


class ResearchParameters(BaseModel):
    """Parameters for a research task. Pydantic validates this for us."""

    topics: List[str] = Field(..., min_length=1)
    scope: str


class NewCardData(BaseModel):
    """The structured data for our Kanban card. This is our target output."""

    title: str
    description: str
    task_type: TaskType
    status: Literal["todo"] = "todo"
    parameters: ResearchParameters


class NewCardAgentResponse(BaseModel):
    """The final, structured response from our endpoint."""

    card_data: list[NewCardData]
    agent_id: str
    execution_time: float
    metadata: Dict[str, Any]