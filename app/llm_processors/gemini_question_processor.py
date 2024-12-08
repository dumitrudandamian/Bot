import ast
import vertexai
import os
from vertexai.generative_models import GenerativeModel, GenerationConfig, HarmCategory, HarmBlockThreshold, Part, Content
from config import Config
from llm_processors.base_question_processor import BaseQuestionProcessor
from typing import Tuple, List
import logging

vertexai.init(project=Config.PROJECT, location=Config.LOCATION)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = Config.GOOGLE_APPLICATION_CREDENTIALS

class GeminiQuestionProcessor(BaseQuestionProcessor):
    def __init__(self, model_name):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
    # def answer_question(self, intrebare):
    #     self.logger.debug("Entered into answer_question() method.")
    #     categorii_response = self.generate_content(f"Întrebare utilizator: {intrebare}\n\nContext: " + Config.get_PROMPT("CATEG_PROMPT"))
    #     categorii = ast.literal_eval(categorii_response.text)
    #     categorii, surse = self.retrieve_question_context(categorii)
    #     if "categorie-necunoscută" in categorii:
    #         self.logger.error(f"The LLM could not find a proper category for the question: {intrebare}")

    #     print(f"Întrebare utilizator: {intrebare}\n" + Config.get_PROMPT("QA_PROMPT") + f"\n{surse}")
    #     qa_response = self.generate_content(f"Întrebare utilizator: {intrebare}\n\nContext: " + Config.get_PROMPT("QA_PROMPT") + f"{surse}")
    #     return categorii, qa_response.text

    def generate_content(self, system_prompt, user_prompts, response_format="text"):

        self.logger.debug("Entered into generate_content() method.")
        model = GenerativeModel(self.model_name, system_instruction=[system_prompt])
        all_messages= []
        for i, user_prompt in enumerate(user_prompts):
            the_role = "user" if i % 2 == 0 else "assistant"
            all_messages.append(Content(role=the_role, parts=[Part.from_text(user_prompt)]))

        generation_config = GenerationConfig(
            candidate_count=1,
            max_output_tokens=8192,
            temperature=0.0,
            seed = 398945215
        )

        if response_format == "json_object":
            generation_config = GenerationConfig(
                candidate_count=1,
                max_output_tokens=8192,
                temperature=0.0,
                seed = 398945215,
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "raspuns": {
                            "type": "string"
                        },
                        "categorii": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["raspuns", "categorii"],
                }          
            )
        response = model.generate_content(all_messages, generation_config=generation_config, safety_settings=Config.SAFETY_SETTINGS)
        return response.text