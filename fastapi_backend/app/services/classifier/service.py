from fastapi_backend.app.services.llm_service.service import GeminiService



class ClassifierService:
    def __init__(self):
        self.model = None
        self.gemini_service = GeminiService()
        
    def classify(self, text: str) -> str:
        return self.gemini_service.get_chat_completion(text)

    