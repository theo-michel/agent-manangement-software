import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv
from vapi import Vapi

from .schema import OutboundCallRequest, OutboundCallResponse

logger = logging.getLogger(__name__)


class VapiService:
    """Service pour gérer les appels Vapi"""
    
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv()
        
        # Configuration Vapi
        api_key = os.getenv("VAPI_API_KEY")
        if not api_key:
            raise ValueError("VAPI_API_KEY environment variable is required")
            
        self.client = Vapi(token=api_key)
        self.logger = logger
        
        # Configuration des IDs (tes vraies valeurs)
        self.phone_number_id = "a8e48b07-00d4-40dc-89bd-25211eaf744b"
        self.assistant_id = "ad4b6b43-8188-47b5-9c68-aa4905002264"
        
        # Prompt système pour l'assistant
        self.system_prompt = """
You are InsightBot, an internal voice assistant.
Your job is to give a *very short* (maximum two-sentence) recap of the latest Market Overview, then immediately ask one question to invite the listener to continue.

Guidelines:
- Be concise, friendly and confident.
- After the recap, ask something like: "Would you like to explore any point further?".
- If the listener asks follow-up questions, answer helpfully.
- Use the person's name when appropriate: {{name}}
- Keep in mind the action to take: {{action_to_take}}

Here is the Market Overview you must summarise:
{{market_overview}}
"""
    
    async def make_outbound_call(self, request: OutboundCallRequest) -> OutboundCallResponse:
        """
        Déclenche un appel sortant avec la Market Overview
        """
        start_time = time.time()
        
        self.logger.info(f"Starting outbound call to {request.target_number}")
        
        try:
            # Lancement de l'appel avec les variables dynamiques
            call = self.client.calls.create(
                assistant_id=self.assistant_id,
                phone_number_id=self.phone_number_id,
                customer={
                    "number": request.target_number,
                },
                assistant_overrides={
                    "variable_values": {
                        "market_overview": request.market_overview,
                        "name": request.name,
                        "action_to_take": request.action_to_take
                    }
                },
            )
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Outbound call initiated successfully: {call.id}")
            
            # Métadonnées pour le suivi
            metadata = {
                "target_number": request.target_number,
                "market_overview_length": len(request.market_overview),
                "name": request.name,
                "action_to_take": request.action_to_take,
                "phone_number_id": self.phone_number_id,
                "assistant_id": self.assistant_id
            }
            
            return OutboundCallResponse(
                success=True,
                call_id=call.id,
                message="Appel sortant déclenché avec succès",
                assistant_id=self.assistant_id,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as error:
            execution_time = time.time() - start_time
            error_message = f"Erreur lors du déclenchement de l'appel: {str(error)}"
            
            self.logger.error(error_message)
            
            return OutboundCallResponse(
                success=False,
                call_id=None,
                message=error_message,
                assistant_id=self.assistant_id,
                execution_time=execution_time,
                metadata={"error": str(error)}
            )
    
    async def make_simple_call(self, target_number: str) -> OutboundCallResponse:
        """
        Déclenche un appel simple sans variables dynamiques
        """
        start_time = time.time()
        
        self.logger.info(f"Starting simple outbound call to {target_number}")
        
        try:
            call = self.client.calls.create(
                assistant_id=self.assistant_id,
                phone_number_id=self.phone_number_id,
                customer={
                    "number": target_number,
                },
            )
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Simple outbound call initiated successfully: {call.id}")
            
            metadata = {
                "target_number": target_number,
                "phone_number_id": self.phone_number_id,
                "assistant_id": self.assistant_id,
                "call_type": "simple"
            }
            
            return OutboundCallResponse(
                success=True,
                call_id=call.id,
                message="Appel simple déclenché avec succès",
                assistant_id=self.assistant_id,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as error:
            execution_time = time.time() - start_time
            error_message = f"Erreur lors du déclenchement de l'appel simple: {str(error)}"
            
            self.logger.error(error_message)
            
            return OutboundCallResponse(
                success=False,
                call_id=None,
                message=error_message,
                assistant_id=self.assistant_id,
                execution_time=execution_time,
                metadata={"error": str(error), "call_type": "simple"}
            ) 