from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OutboundCallRequest(BaseModel):
    target_number: str = Field(..., description="Numéro de téléphone du destinataire (format E.164)")
    market_overview: str = Field(..., description="Texte de la Market Overview à résumer")
    name: str = Field(..., description="Nom de la personne à qui on passe l'appel")
    action_to_take: str = Field(..., description="Action à entreprendre pendant l'appel")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_number": "+33611421334",
                "market_overview": "The European ed-tech market grew 23% last year, with France and Germany leading demand in AI-powered language tools, while competition in the UK intensifies.",
                "name": "John Doe",
                "action_to_take": "Schedule a follow-up meeting to discuss investment opportunities"
            }
        }


class OutboundCallResponse(BaseModel):
    success: bool
    call_id: Optional[str] = None
    message: str
    assistant_id: Optional[str] = None
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None 