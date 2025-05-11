import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from app.services.chat.schema import GoalRewriteModel,get_necesary_files,get_markdown_documentation
from app.services.chat.utils import SAFE,get_gemini_pro_25_response
from app.services.monitor.langfuse import get_langfuse_context,trace,generate_trace_id
from app.services.llm_service.service import TemplateManager
import instructor
import os
import dotenv
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
import instructor
from google.generativeai import caching
import google.generativeai as genai
from pathlib import Path
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)


dotenv.load_dotenv()

#TODO PUT ALL LLM CLIENTS IN LLM_SERVICE


def process_structured_llm_call(
    client_gemini,
    symstem_prompt: str,
    user_prompt: str,
    model_name: str,
    span=None,
    pydantic_model: BaseModel = None,
    span_name: str = "gemini",
) -> dict:

        messages = [
            {"role": "system", "content": symstem_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if span:
            generation = span.generation(
                name=span_name,
                model=model_name,
                model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 8000},
                input={
                    "system_prompt": symstem_prompt,
                    "user_prompt": user_prompt,
                },
            )

        try:
            completion, raw = client_gemini.chat.create_with_completion(
                messages=messages,
                response_model=pydantic_model,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1,
                    "candidate_count": 1,
                    "max_output_tokens": 8000 if '2.5' not in model_name else 60000,
                },
                max_retries=5,
            )
            result = completion.model_dump()
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

def create_instructor_gemini_client(model_name: str="", GEMINI_API_KEY: str = "", cache_id: str = ""):
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    if cache_id:
        cache = caching.CachedContent.get(cache_id)
        return instructor.from_gemini(
            client=genai.GenerativeModel.from_cached_content(
                cached_content=cache, safety_settings=SAFE
            ),
            mode=instructor.Mode.GEMINI_JSON,
        )
    else:
        return instructor.from_gemini(
            client=genai.GenerativeModel(model_name=model_name, safety_settings=SAFE),
            mode=instructor.Mode.GEMINI_JSON,
        )

def add_file_contents_to_promps(symstem_prompt: str = "", 
                                user_prompt: str = "", 
                                files_list: dict = {}, 
                                files_list_md_config: dict = {}, 
                                documentation: dict = {}, 
                                documentation_md: dict = {}, 
                                config: dict = {},
                                is_just_chat: bool = True) -> dict:

    CODE_FILES = ""
    README_FILES = ""
    CONFIGS_FILES = ""

    for file in files_list_md_config:
        file_id = int(file["file_id"])
        file_name = file["file_name"]
        if ".md" in file_name:
            path = documentation_md["documentation_md"][file_id]["file_paths"]
            try:
                with open(path, "r") as f:
                    if is_just_chat:
                        symstem_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
                    else:
                        README_FILES += f"\n<file_name : {file_name}, file_id : {file_id}>\n" + f.read() + f"\n</file_name : {file_name}, file_id : {file_id}>"
            except:
                # raise Exception(
                #     f"Error while reading the file {path}, {traceback.format_exc()}"
                # )
                pass
        else:
            try:
                path = config["config"][file_id]["file_paths"]
                with open(path, "r") as f:
                    if is_just_chat:
                        symstem_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
                    else:
                        CONFIGS_FILES += f"\n<file_name : {file_name}, file_id : {file_id}>\n" + f.read() + f"\n</file_name : {file_name}, file_id : {file_id}>"
            except:
                # raise Exception(
                #     f"Error while reading the file {path}, {traceback.format_exc()}"
                # )
                pass
    # Get file names from the documentation : files_list
    for file in files_list:
        file_id = int(file["file_id"])
        file_name = file["file_name"]
        path = documentation["documentation"][file_id]["file_paths"]
        try:
            with open(path, "r") as f:
                if is_just_chat:
                    user_prompt += f"\n<{file_name}>\n" + f.read() + f"\n</{file_name}>"
                else:
                    CODE_FILES += f"\n<file_name : {file_name}, file_id : {file_id}>\n" + f.read() + f"\n</file_name : {file_name}, file_id : {file_id}>"
        except:
            raise Exception(
                f"Error while reading the file {path}, {traceback.format_exc()}"
            )

    return {
        "symstem_prompt": symstem_prompt,
        "user_prompt": user_prompt,
        "CODE_FILES": CODE_FILES,
        "README_FILES": README_FILES,
        "CONFIGS_FILES": CONFIGS_FILES
    }



class ClassifierConfig:
    def __init__(self):
        self.current_dir = Path(__file__).parent
        # Initialize TemplateManager with the correct search directory
        self.template_manager = TemplateManager(default_search_dir=self.current_dir)
        self.prompts_config = {
        }
        self.file_class_model_0 = os.getenv("FILE_CLASSICATION_MODEL_0")
        self.file_class_model_1 = os.getenv("FILE_CLASSICATION_MODEL_1")
        self.file_class_model_2 = os.getenv("FILE_CLASSICATION_MODEL_2")
        self.file_class_model_3 = os.getenv("FILE_CLASSICATION_MODEL_3")
        self.querry_rewriting_model = os.getenv("QUERRY_REWRITING_MODEL")
        self.documentation_context_retriver_model = os.getenv("DOCUMENTATION_CONTEXT_RETRIVER")
        self.context_caching_retriver_model = os.getenv("CONTEXT_CACHING_RETRIVER")
        self.final_response_generator_model = os.getenv("FINAL_ANSWER_GENERATOR")
        self.prompts_config = {
            "system_prompt_rewrite": "prompts/prompt_rewrite/system_prompt_rewrite.jinja2",
            "user_prompt_rewrite": "prompts/prompt_rewrite/user_prompt_rewrite.jinja2",
            "system_prompt_code_generator": "prompts/prompt_coder/system_prompt_code_generator.jinja2",
            "user_prompt_code_generator": "prompts/prompt_coder/user_prompt_code_generator.jinja2",
            "system_prompt_librari_retriver": "prompts/system_prompt_librari_retriver.jinja2",
            "user_prompt_librari_retriver": "prompts/user_prompt_librari_retriver.jinja2",
            "user_prompt_configuration_retriver": "prompts/prompt_user_config_retriver.jinja2",
            "user_prompt_full_doc": "prompts/prompt_full_doc/user_prompt_full_doc.jinja2",
            "system_prompt_full_doc": "prompts/prompt_full_doc/system_prompt_full_doc.jinja2",
        }

class Querry_Rewritter_Node(ClassifierConfig):
    def __init__(self):
        super().__init__()


    @trace
    def querry_rewritter(
        self,
        symstem_prompt: str,
        user_prompt: str,
        GEMINI_API_KEY: str = "",
        ANTHROPIC_API_KEY: str = "",
        OPENAI_API_KEY: str = "",
        trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063",
    ) -> str:
        span = get_langfuse_context().get("span")

            
        client_gemini = create_instructor_gemini_client(self.querry_rewriting_model, GEMINI_API_KEY)

        rewrite = process_structured_llm_call(
            client_gemini=client_gemini, 
            symstem_prompt=symstem_prompt, 
            user_prompt=user_prompt, 
            model_name=self.querry_rewriting_model, 
            span=span, 
            pydantic_model=GoalRewriteModel,
            span_name="querry_rewritter",
        )

        return rewrite

                
class Documentation_Context_Retriver_Node(ClassifierConfig):
    def __init__(self):
        super().__init__()

    @trace
    def documentation_context_retriver(
        self,
        symstem_prompt: str,
        user_prompt: str,
        max_workers: int = 10,  # Number of parallel workers
        config_doc: dict = None,
        documentation_md: dict = None,
        GEMINI_API_KEY: str = "",
        ANTHROPIC_API_KEY: str = "",
        OPENAI_API_KEY: str = "",
        trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063",
    ) -> dict:
        span = get_langfuse_context().get("span")
        # Load documentations md and configs
        documentation = []

        documentation_md = documentation_md.get("documentation_md")
        config_doc = config_doc.get("config")
        if documentation_md and documentation_md[0] != {}:
            documentation = documentation + documentation_md
            if config_doc and config_doc[0] != {}:
                documentation = documentation + config_doc

        for index, doc in enumerate(documentation):
            doc["file_id"] = index

        user_prompt = user_prompt.replace("FILES_HERE", str(documentation))

        if len(documentation) == 0:
            return {"files_list": []}


        # Configure Gemini with API key from request if provided
        client_gemini = create_instructor_gemini_client(self.documentation_context_retriver_model, GEMINI_API_KEY)
            


        result = process_structured_llm_call(
            client_gemini=client_gemini, 
            symstem_prompt=symstem_prompt, 
            user_prompt=user_prompt, 
            model_name=self.documentation_context_retriver_model, 
            span=span, 
            pydantic_model=get_necesary_files({"documentation": documentation}),
            span_name="md_documentation_context_retriver",
        )

        return result


class Context_Caching_Retriver_Node(ClassifierConfig):
    def __init__(self):
        super().__init__()

    @trace
    def context_caching_retrival(
        self,
        documentation: dict,
        cache_id: str,
        symstem_prompt: str,
        user_prompt: str,
        GEMINI_API_KEY: str = "",
        ANTHROPIC_API_KEY: str = "",
        OPENAI_API_KEY: str = "",
        trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063",
    ) -> str:
        span = get_langfuse_context().get("span")

        # Configure Gemini with API key from request if provided
        client_gemini = create_instructor_gemini_client(self.context_caching_retriver_model, GEMINI_API_KEY, cache_id)


        list_of_files = process_structured_llm_call(
            client_gemini=client_gemini, 
            symstem_prompt=symstem_prompt, 
            user_prompt=user_prompt, 
            model_name=self.context_caching_retriver_model, 
            span=span, 
            pydantic_model=get_necesary_files(documentation),
            span_name="context_caching_files_retriver",
        )

        return list_of_files



class Final_Response_Generator_Node(ClassifierConfig):
    def __init__(self):
        super().__init__()

    @trace#TODO REMOVED HARDCODED MODEL NAME
    def answer_user_querry_with_context(
        self,
        files_list: dict,
        files_list_md_config: dict,
        documentation: dict,
        documentation_md: dict,
        config: dict,
        cache_id: str,
        symstem_prompt: str,
        user_prompt: str,
        GEMINI_API_KEY: str = "",
        ANTHROPIC_API_KEY: str = "",
        OPENAI_API_KEY: str = "",
        trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063",
        ) -> str:
        span = get_langfuse_context().get("span")
        # Configure safety settings
        safe = SAFE

        # Configure Gemini with API key from request if provided
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        else:
            # Use default API key from environment
            genai.configure()

        # Configure Anthropic client with API key from request if provided



        added_file_contents = add_file_contents_to_promps(symstem_prompt=symstem_prompt, 
                                                          user_prompt=user_prompt, 
                                                          files_list=files_list, 
                                                          files_list_md_config=files_list_md_config, 
                                                          documentation=documentation, 
                                                          documentation_md=documentation_md, 
                                                          config=config, 
                                                          is_just_chat=True)
        symstem_prompt = added_file_contents["symstem_prompt"]
        user_prompt = added_file_contents["user_prompt"]
        messages = []

        # Add system prompt if provided

        # Add user message
        try:
            if span:
                generation = span.generation(
                    name="gemini",
                    model=self.final_response_generator_model,
                    model_parameters={"temperature": 0, "top_p": 1, "max_new_tokens": 60000},
                    input={"system_prompt": symstem_prompt, "user_prompt": user_prompt},
                )

            # Use custom function to pass API key
            if GEMINI_API_KEY:
                logger.info(f"Using Gemini API key: {GEMINI_API_KEY}")
                genai.configure(api_key=GEMINI_API_KEY)
                
                logger.info(f"Creating new client instance with Gemini API key...")
                final_answer_generator = genai.GenerativeModel(
                    model_name=self.final_response_generator_model,
                    safety_settings=safe,
                    generation_config={"temperature": 0.95, "top_p": 1, "max_output_tokens": 60000},
                )
                
                logger.info(f"Generating response with Gemini API key...")
                Answer = final_answer_generator.generate_content(symstem_prompt + "\n" + user_prompt)
            else:
                # Use the default function
                Answer = get_gemini_pro_25_response(symstem_prompt + "\n" + user_prompt)

            if span:
                generation.end(
                    output=f"# {self.final_response_generator_model} \n" + Answer.text,
                    usage={
                        "input": Answer.usage_metadata.prompt_token_count,
                        "output": Answer.usage_metadata.candidates_token_count,
                    },
                )
            return Answer.text
        
        except Exception as e:
            logger.error(f"Error while answering the user querry, {e}, traceback: {traceback.format_exc()}")
            raise Exception(f"Error while answering the user querry, {e}, traceback: {traceback.format_exc()}")

class GenrateDetailedDocumentationNode(ClassifierConfig):
    def __init__(self):
        super().__init__()

    @trace
    def run_genrate_detailed_documentation(self, 
                                           files_list: dict,
                                           files_list_md_config: dict,
                                           documentation: dict,
                                           documentation_md: dict,
                                           config: dict,
                                           cache_id: str = "",
                                           GEMINI_API_KEY: str = "",
                                           ANTHROPIC_API_KEY: str = "",
                                           OPENAI_API_KEY: str = "",
                                           trace_id: str = "df8187ba-a07e-4ea9-9117-5a7662eaa063") -> dict:
        span = get_langfuse_context().get("span")
        markdown_documentation_pydantic_model = get_markdown_documentation(code_documentation_json=documentation["documentation"], readme_doc_json=documentation_md["documentation_md"], config_doc_json=config["config"])

        client_gemini = create_instructor_gemini_client(self.final_response_generator_model, GEMINI_API_KEY, cache_id)

        CODE_FILES= ""
        README_FILES= ""
        CONFIGS_FILES= ""

        added_file_contents = add_file_contents_to_promps(files_list=files_list, 
                                                          files_list_md_config=files_list_md_config, 
                                                          documentation=documentation, 
                                                          documentation_md=documentation_md, 
                                                          config=config, 
                                                          is_just_chat=False)
        CODE_FILES = added_file_contents["CODE_FILES"]
        README_FILES = added_file_contents["README_FILES"]
        CONFIGS_FILES = added_file_contents["CONFIGS_FILES"]

        

        symstem_prompt = self.template_manager.render_template(
            template_relative_path=self.prompts_config["system_prompt_full_doc"],
        )

        user_prompt = self.template_manager.render_template(
            template_relative_path=self.prompts_config["user_prompt_full_doc"],
            context={
                "CODE_FILES": CODE_FILES,
                "README_FILES": README_FILES,
                "CONFIGS_FILES": CONFIGS_FILES
                }
        )


        
        generated_documentation = process_structured_llm_call(
            client_gemini=client_gemini,
            symstem_prompt=symstem_prompt,
            user_prompt=user_prompt,
            model_name=self.final_response_generator_model,
            span=span,
            pydantic_model=markdown_documentation_pydantic_model,
            span_name="genrate_detailed_documentation",
        )

        return generated_documentation


class ChatService(ClassifierConfig):
    def __init__(self):
        super().__init__()
        self.trace_id = generate_trace_id()
        self.querry_rewritter = Querry_Rewritter_Node()
        self.doc_context_retriver = Documentation_Context_Retriver_Node()
        self.context_caching_retriver = Context_Caching_Retriver_Node()
        self.final_response_generator = Final_Response_Generator_Node()
        self.genrate_detailed_documentation = GenrateDetailedDocumentationNode()
    
    def run_pipeline(self, repository_name: str, 
                     cache_id: str = "", 
                     documentation: dict = {},
                     user_problem: str = "", 
                     documentation_md: dict = {},
                     config_input: dict = {},
                     GEMINI_API_KEY : str = "",
                     is_documentation_mode: bool = False) -> str | dict:

        # 0. check if it's a documentation mode
        if is_documentation_mode:
            user_problem = "The documentation of this repo is not very good. I need you to generate a complete precide documentation of this repo. Really detailled."

        # 1. prompt_user_rewriter
        prompt_user_rewriter_output = self.template_manager.render_template(    
            template_relative_path=self.prompts_config["user_prompt_rewrite"],
             context={"user_query": user_problem}
        )
        # 2. prompt_system_rewriter
        prompt_system_rewriter_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["system_prompt_rewrite"],
            context={"library_name": repository_name}
        )
        # 3. querry_rewriter
        querry_rewriter_output = self.querry_rewritter.querry_rewritter(
            #TODO : ADD API KEY
            symstem_prompt=prompt_system_rewriter_output,
            user_prompt=prompt_user_rewriter_output,
            trace_id=self.trace_id
        )
        # 4. prompt_system_librari_retriver
        prompt_system_librari_retriver_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["system_prompt_librari_retriver"],
            context={"repository_name": repository_name}
        )
        # 5. user_prompt_librari_retriver
        user_prompt_librari_retriver_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["user_prompt_librari_retriver"],
            context={"user_problem": querry_rewriter_output}
        )
        # 6. call documentation from context_caching_retriver node
        documentation_from_context_caching_retriver_output = self.context_caching_retriver.context_caching_retrival(
            cache_id=cache_id,
            documentation=documentation,
            symstem_prompt=prompt_system_librari_retriver_output,
            user_prompt=user_prompt_librari_retriver_output,
            trace_id=self.trace_id
        )
        
        # 7. user_prompt_config_retriver
        user_prompt_config_retriver_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["user_prompt_configuration_retriver"],
            context={"user_problem": querry_rewriter_output}
        )
        # 8. call final_response_generator node
        md_documentation_output = self.doc_context_retriver.documentation_context_retriver(
            symstem_prompt=prompt_system_librari_retriver_output, # Uses output from step 4
            user_prompt=user_prompt_config_retriver_output,
            config_doc=config_input, # This is inputs.config
            documentation_md=documentation_md,
            trace_id=self.trace_id
        )

        # 9. prompts for final answer
        prompt_user_code_generator_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["user_prompt_code_generator"],
            context={"user_problem": querry_rewriter_output}
        )
        prompt_system_code_generator_output = self.template_manager.render_template(
            template_relative_path=self.prompts_config["system_prompt_code_generator"],
            context={"library_name": repository_name}
        )

        # 10. call final_response_generator node
        if not is_documentation_mode:
            final_response_generator_output = self.final_response_generator.answer_user_querry_with_context(
                files_list=documentation_from_context_caching_retriver_output["files_list"],
                files_list_md_config=md_documentation_output["files_list"],
                documentation=documentation,
                documentation_md=documentation_md,
                config=config_input,
                cache_id=cache_id,
                symstem_prompt=prompt_system_code_generator_output,
                user_prompt=prompt_user_code_generator_output,
                trace_id=self.trace_id
            )
        else:
            final_response_generator_output = self.genrate_detailed_documentation.run_genrate_detailed_documentation(
                files_list=documentation_from_context_caching_retriver_output["files_list"],
                files_list_md_config=md_documentation_output["files_list"],
                documentation=documentation,
                documentation_md=documentation_md,
                config=config_input,
                trace_id=self.trace_id
            )
        return final_response_generator_output



if __name__ == "__main__":
    import os
    import json
    import shutil
    import traceback

    # This test script will be placed directly in the if __name__ == "__main__" block.
    # Librairie_Service is already defined in this file.

    TEMP_DIR = "temp_test_files_for_librairie_service"



    print("--- Starting Test for Librairie_Service ---")


    # --- Prepare Fake Data for run_pipeline ---
    repository_name_test = "Arfxflix"
    cache_id_test = "test_cache_integration_001" # Ensure this cache_id exists if using actual caching system
    user_problem_test = "Presnt this repo in simple words"
    
    # The GEMINI_API_KEY is passed to run_pipeline.

    

    # This is the main "documentation" input, typically representing code files.
    documentation_input_test = None
    with open("backend/tests/tmp_test/documentation.json", "r") as f:
        documentation_input_test = {"documentation": json.load(f)}

    # This represents Markdown documentation files.
    documentation_md_input_test = None
    with open("backend/tests/tmp_test/documentation_md.json", "r") as f:
        documentation_md_input_test = {"documentation_md": json.load(f)}

    # This represents configuration files (e.g., JSON, YAML).
    config_input_test = None
    with open("backend/tests/tmp_test/config.json", "r") as f:
        config_input_test = {"config": json.load(f)}

    # --- Instantiate Service ---
    # Librairie_Service is defined in the current file.
    librairie_service_instance = ChatService()

    # --- Run Pipeline ---
    print(f"\nRunning pipeline for repository: {repository_name_test}...")
    print(f"User problem: {user_problem_test}")
    final_result = None
    try:
        print(f"Using GEMINI_API_KEY: {'Provided' if os.getenv("GEMINI_API_KEY") else 'Not provided (will rely on env or default)'}")

        final_result = librairie_service_instance.run_pipeline(
            repository_name=repository_name_test,
            cache_id="cachedContents/vinldk2v9mojw3tbr1r99ni5g652snvru6cob138", #hardocded
            documentation=documentation_input_test,
            user_problem=user_problem_test,
            documentation_md=documentation_md_input_test,
            config_input=config_input_test,
            GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")  # Pass the API key here
        )
        print("\n--- Pipeline Execution Succeeded ---")
        print("Final Result:")
        # The result is expected to be a string (the generated answer).
        print(final_result)

    except Exception as e:
        print(f"\n--- Pipeline Execution Failed ---")
        print(f"An error occurred: {e}")
        print("Traceback:")
        traceback.print_exc()
    finally:
        print("\n--- Test for Librairie_Service Finished ---")
