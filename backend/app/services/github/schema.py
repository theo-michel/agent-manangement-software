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

    REPORTING = "reporting_task"
    RESEARCH = "research_task"


class NewCardData(BaseModel):
    """
    Defines the structure for a single task card, now with dependency tracking.
    """

    card_id: str = Field(
        ...,
        description="A unique temporary ID for this card within the response (e.g., 'task-1').",
    )
    title: str
    description: str
    task_type: TaskType
    status: Literal["todo"] = "todo"
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of card_ids this card depends on.",
    )


class NewCardAgentResponse(BaseModel):
    """The final response, containing a list of generated cards."""

    card_data: list[NewCardData]
    agent_id: str
    execution_time: float
    metadata: Dict[str, Any]