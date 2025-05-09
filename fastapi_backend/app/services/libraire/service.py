from fastapi_backend.app.services.llm_service.service import TemplateManager
from fastapi_backend.app.services.libraire.schema import GoalRewriteModel
from fastapi_backend.app.services.libraire.utils import SAFE
import instructor
import os
import dotenv
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import google.generativeai as genai
import traceback

dotenv.load_dotenv()


class ClassifierConfig:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.prompts_config = {
        }
        self.file_class_model_0 = os.getenv("FILE_CLASSICATION_MODEL_0")
        self.file_class_model_1 = os.getenv("FILE_CLASSICATION_MODEL_1")
        self.file_class_model_2 = os.getenv("FILE_CLASSICATION_MODEL_2")
        self.file_class_model_3 = os.getenv("FILE_CLASSICATION_MODEL_3")
        self.querry_rewriting_model = os.getenv("QUERRY_REWRITING_MODEL")

class Querry_Rewritter(ClassifierConfig):
    def __init__(self):
        super().__init__()

    def process_batch(
        self,
        client_gemini,
        symstem_prompt: str,
        user_prompt: str,
        span=None,
    ) -> dict:
        """Process a batch of files using Gemini API"""

        messages = [
            {"role": "system", "content": symstem_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if span:
            generation = span.generation(
                name="gemini",
                model=self.querry_rewriting_model,
                model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 8000},
                input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
            )

        try:
            completion, raw = client_gemini.chat.create_with_completion(
                messages=messages,
                response_model=GoalRewriteModel,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1,
                    "candidate_count": 1,
                    "max_output_tokens": 8000,
                },
                max_retries=10,
            )
            result = completion.model_dump()
            # if span:
            #     span.score(name="number_try", value=raw.n_attempts)
        except Exception as e:
            if span:
                generation.end(
                    output=None,
                    status_message=f"Error processing batch: {str(e)}, {traceback.format_exc()}",
                    level="ERROR",
                )
            raise e

        if span:
            generation.end(
                output=result,
                usage={
                    "input": raw.usage_metadata.prompt_token_count,
                    "output": raw.usage_metadata.candidates_token_count,
                },
            )

        return result
    #@trace
    def querry_rewritter(
        self,
        symstem_prompt: str,
        user_prompt: str,
        GEMINI_API_KEY: str = "",
        ANTHROPIC_API_KEY: str = "",
        OPENAI_API_KEY: str = "",
        trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063",
    ) -> str:
        #span = get_langfuse_context().get("span")
        span = None

        # Configure safety settings
        safe = SAFE

        # Configure Gemini with API key from request if provided
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        else:
            # Use default API key from environment
            genai.configure()
            
        client_gemini = instructor.from_gemini(
            client=genai.GenerativeModel(
                model_name=self.querry_rewriting_model, safety_settings=safe
            ),
            mode=instructor.Mode.GEMINI_JSON,
        )

        rewrite = self.process_batch(client_gemini, symstem_prompt, user_prompt, span)

        return rewrite

                

