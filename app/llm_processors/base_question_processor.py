from abc import ABC, abstractmethod
from typing import Tuple, List
from config import Config
import logging
import ast
import json

class BaseQuestionProcessor(ABC):

    logger = logging.getLogger('BaseQuestionProcessor')

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate_content(self, system_prompt:str, user_prompts:List[str], response_format:str) -> Tuple[List[str], str]:
        pass

    def answer_question(self, intrebare):
        self.logger.debug("Entered into answer_question() method.")
        categorii_response = self.generate_content(Config.get_PROMPT("CATEG_PROMPT"), [intrebare], "text")
        categorii = ast.literal_eval(categorii_response)
        categorii_orig = categorii
        if "categorie-necunoscuta" in categorii:
            # pass mutiple categories in order to decide what to answer 
            categorii = ["administrare-abonament-si-optiuni", "portare", "alte-servicii", "activare-abonament", "aplicatia-si-contul-meu", "despre-yoxo", "facturi-plati-si-consum", "servicii-de-urgenta", "roaming", "inchidere-abonament", "esim", "detalii-pachete-optiuni"]  
        categorii, surse = self.retrieve_question_context(categorii)
        qa_response = self.generate_content(Config.get_PROMPT("QA_PROMPT") + surse, [intrebare], "text")

        return categorii_orig, qa_response

    def chat(self, intrebari_raspunsuri):
        self.logger.debug("Entered into chat("+ str(intrebari_raspunsuri) + ") method.")
        json_response_string = self.generate_content(Config.get_PROMPT("ASSISTANT_CATEG_PROMPT"), intrebari_raspunsuri, "json_object")
        self.logger.debug("Problem Understanding Asistant response: " + json_response_string)
        json_response = json.loads(json_response_string)
        # intrebari_raspunsuri.append(json_response["raspuns"])
        categorii = json_response["categorii"]
        
        if "categorie-necunoscuta" not in categorii and "transfer" not in categorii and "conversatie-inchisa" not in categorii:
            categorii, surse = self.retrieve_question_context(categorii)
            json_response_string = self.generate_content(Config.get_PROMPT("ASSISTANT_QA_PROMPT") + surse, intrebari_raspunsuri, "json_object")
            self.logger.debug("Problem Answering Asistant response: " + json_response_string)

            json_response = json.loads(json_response_string)
            categorii_pa = json_response["categorii"]
            if "transfer" in categorii_pa:
                categorii = categorii_pa
        
        raspuns = json_response["raspuns"]
        return categorii, raspuns
    
    def retrieve_question_context(self, categorii):
        self.logger.debug("Entered into retrieve_question_context() method.")

        sources = self.get_sources(categorii)

        if "esim" in categorii and "activare-abonament" not in categorii:
            categorii.append("activare-abonament")
        if ("roaming" in categorii \
            or "activare-abonament" in categorii  \
            or "administrare-abonament-si-optiuni"in categorii \
            or "portare" in categorii \
            or "alte-servicii" in categorii) and "detalii-pachete-optiuni" not in categorii:
            categorii.append("detalii-pachete-optiuni")

        for categorie in categorii:
            if categorie != "categorie-necunoscută":
                self.logger.debug(f"Loading into context: {categorie}")
                sources += self.load_category_file(categorie)
        return categorii, sources
    
    def get_sources(self, categorii):
        self.logger.debug(f"Entered into get_sources() method.")
        if "roaming" in categorii:
            return Config.get_PROMPT("ROAMING_SOURCE_START_PROMPT")
        return Config.get_PROMPT("DEFAULT_SOURCE_START_PROMPT")

    @staticmethod
    def load_category_file(categorie):
        BaseQuestionProcessor.logger.debug(f"Entered into load_category_file() method.")
        try:
            with open(f"{Config.FAQ_DOWNLOAD_FOLDER}/{categorie}.txt", 'r', encoding='utf-8') as file:
                content = file.read()
                return f"\n[{categorie}]\n{content}"
        except FileNotFoundError:
            BaseQuestionProcessor.logger.error(f"Nu am gasit fisierul pentru categoria: {categorie}")
            return ""