from fastapi import APIRouter, HTTPException
import logging

from app.services.github.schema import  AgentRequest, AgentResponse
from app.services.chat.service import ChatService
from app.services.agent.service import AgentService
from app.services.vapi.service import VapiService
from app.services.vapi.schema import OutboundCallRequest, OutboundCallResponse

router = APIRouter(prefix="/chat", tags=["chat"])

logger = logging.getLogger(__name__)

# Initialize services
chat_service = ChatService()
agent_service = AgentService()
vapi_service = VapiService()



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


@router.post("/outbound-call", response_model=OutboundCallResponse)
async def trigger_outbound_call(
    call_request: OutboundCallRequest,
):
    """
    Déclenche un appel sortant avec une Market Overview.
    
    - **target_number**: Numéro de téléphone du destinataire (format E.164, ex: +33611421334)
    - **market_overview**: Texte de la Market Overview à résumer pendant l'appel
    """
    try:
        logger.info(f"Triggering outbound call to {call_request.target_number}")
        return await vapi_service.make_outbound_call(call_request)
    except Exception as e:
        logger.error(f"Error triggering outbound call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Outbound call failed: {str(e)}") 
    



# exemple pour call outbound :

# Données de test
#     test_data = {
#         "target_number": "+33611421334",  # Ton numéro
#         "market_overview": "The European ed-tech market grew 23% last year, with France and Germany leading demand in AI-powered language tools, while competition in the UK intensifies. New startups are emerging with innovative solutions for personalized learning."
#     }

# response = requests.post(
#             endpoint,
#             json=test_data,
#             headers={"Content-Type": "application/json"},
#             timeout=30
#         )