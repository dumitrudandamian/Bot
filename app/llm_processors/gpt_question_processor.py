import ast
import os
from config import Config
from llm_processors.base_question_processor import BaseQuestionProcessor
from typing import Tuple, List
from openai import OpenAI
import httpx as _httpx
import logging
import json

_http_client = _httpx.Client()

class GPTQuestionProcessor(BaseQuestionProcessor):
    def __init__(self, model_name):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = OpenAI(api_key=Config.OPENAI_KEY, 
                http_client=_http_client,)
        self.model_name = model_name

    # def answer_question(self, intrebare):
    #     self.logger.debug("Entered into answer_question() method.")
    #     categorii_response = self.generate_content(Config.get_PROMPT("CATEG_PROMPT"), [intrebare])
    #     categorii = ast.literal_eval(categorii_response)
    #     if "categorie-necunoscuta" in categorii:
    #         self.logger.error(f"The LLM could not find a proper category for the question: {intrebare}")
    #         qa_response = self.generate_content(Config.get_PROMPT("QA_PROMPT"), [intrebare])
    #     else:
    #         categorii, surse = self.retrieve_question_context(categorii)
    #         qa_response = self.generate_content(Config.get_PROMPT("QA_PROMPT") + surse, [intrebare])
    #     return categorii, qa_response

    # def chat(self, intrebari_raspunsuri):
    #     self.logger.debug("Entered into chat("+ str(intrebari_raspunsuri) + ") method.")
    #     json_response_string = self.generate_content(Config.get_PROMPT("ASSISTANT_CATEG_PROMPT"), intrebari_raspunsuri, "json_object")
    #     self.logger.debug("Problem Understanding Asistant response: " + json_response_string)
    #     json_response = json.loads(json_response_string)
    #     # intrebari_raspunsuri.append(json_response["raspuns"])
    #     categorii = json_response["categorii"]
        
    #     if "categorie-necunoscuta" not in categorii and "transfer" not in categorii:
    #         categorii, surse = self.retrieve_question_context(categorii)
    #         json_response_string = self.generate_content(Config.get_PROMPT("ASSISTANT_QA_PROMPT") + surse, intrebari_raspunsuri, "json_object")
    #         self.logger.debug("Problem Answering Asistant response: " + json_response_string)

    #         json_response = json.loads(json_response_string)
    #         # categorii = json_response["categorii"]
        
    #     raspuns = json_response["raspuns"]
    #     return categorii, raspuns
    
    def generate_content(self, system_prompt, user_prompts, response_format="text"):
        self.logger.debug("Entered into generate_content() method.")
        all_messages= [
                {"role": "system", "content": system_prompt}
            ]
        for i, user_prompt in enumerate(user_prompts):
            role = "user" if i % 2 == 0 else "assistant"
            all_messages.append({"role": role, "content": user_prompt})

        completion = self.client.chat.completions.create(
            model=self.model_name,
            seed=0,
            temperature=0.1,
            response_format={ "type": response_format },
            messages= all_messages
        )
        return completion.choices[0].message.content