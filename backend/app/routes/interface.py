from fastapi import APIRouter, HTTPException
import logging

from app.services.agent import new_card_service, deep_search_service
from app.services.github.schema import AgentRequest, AgentResponse, NewCardAgentResponse
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

@router.post("/new-card", response_model=NewCardAgentResponse)
async def create_new_card_from_prompt(
        agent_request: AgentRequest,
):
        """
        Takes a natural language prompt and uses a smolagent to create a
        structured new task card.
        """
        if not agent_request.prompt or not agent_request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        try:
            return await new_card_service.process_prompt(agent_request)
        except ValueError as e:
            # Catches user errors or bad output from the model (4xx error)
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            # Catches backend service failures (5xx error)
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            # Catch-all for any other unexpected server error
            logger.exception(f"Unhandled exception in /new-card endpoint: {e}")
            raise HTTPException(
                status_code=500, detail="An internal server error occurred."
            )

@router.post("/deep-search", response_model=AgentResponse)
async def perform_deep_search(
    agent_request: AgentRequest,
):
    """
    Takes a prompt and uses a web-searching agent to find a
    comprehensive answer.
    """
    if not agent_request.prompt or not agent_request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        return await deep_search_service.run_search(agent_request)
    except RuntimeError as e:
        # Catches backend service failures (e.g., agent execution)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Catch-all for any other unexpected server error
        logger.exception(f"Unhandled exception in /deep-search endpoint: {e}")
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )

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