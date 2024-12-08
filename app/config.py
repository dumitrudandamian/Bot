from vertexai.generative_models import HarmCategory, HarmBlockThreshold
import logging
import os

class Config:
    logger = logging.getLogger('BaseQuestionProcessor')

    SAFETY_SETTINGS={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
    
    PROXIES = {
        'http://':'http://kirk.crm.orange.intra:3128',
        'https://':'http://kirk.crm.orange.intra:3128'
    }

  
    # to be fetched from k8s env
    PROJECT = os.getenv("PROJECT","oro-test-gen-338-dev")
    LOCATION = os.getenv("LOCATION","europe-west3")

    # DATA_BASE_FOLDER = os.getenv("DATA_BASE_FOLDER","/yoxo_shared_files")
    DATA_BASE_FOLDER = os.getenv("DATA_BASE_FOLDER","/")
    UPLOAD_FOLDER = os.path.join(DATA_BASE_FOLDER, os.getenv("UPLOAD_FOLDER","yoxo/upload/"))
    FAQ_DOWNLOAD_FOLDER = os.path.join(DATA_BASE_FOLDER, os.getenv("FAQ_DOWNLOAD_FOLDER", "yoxo/faq"))
    ASK_QUESTION_HTML_FILE = os.getenv("ASK_QUESTION_HTML_FILE","ask_question.html")
    CONFIG_FOLDER = os.getenv("CONFIG_FOLDER","/yoxo/cfg/")
    PROMPTS_FOLDER = os.path.join(DATA_BASE_FOLDER, os.getenv("PROMPTS_FOLDER","yoxo/prompts/"))
    YOXO_FAQ_BASE_URL = os.getenv("YOXO_FAQ_BASE_URL","https://www.yoxo.ro/help/")

    REST_PORT = os.getenv("REST_PORT", "3008")
    PROMETHEUS_PORT = os.getenv("PROMETHEUS_PORT", 5000)
    DEFAULT_LIMIT_PER_DAY = os.getenv("DEFAULT_LIMIT_PER_DAY", "20 per day")
    DEFAULT_LIMIT_PER_HOUR = os.getenv("DEFAULT_LIMIT_PER_HOUR", "3 per hour")
    ASK_LIMIT_PER_HOUR = os.getenv("ASK_LIMIT_PER_HOUR", "20 per hour")
    LLM_MODEL = os.getenv("LLM_MODEL","gemini")
    GPT_MODEL = os.getenv("GPT_MODEL","gpt-4o-2024-08-06")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL","gemini-1.5-pro-002")
    FAQ_DOWNLOAD_METHOD = os.getenv("FAQ_UPLOAD_METHOD","/yoxofaqbot/api/private/update-all")
    K8S_SERVICE_NAME = os.getenv("K8S_SERVICE_NAME","yoxofaqbot")

    # To be fetched from Vault
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", CONFIG_FOLDER + "/auth_dan.json")
    OPENAI_KEY = os.getenv("OPENAI_KEY","")
    CATEGORIES_DICT = {
        'detalii-pachete-optiuni': 'https://www.yoxo.ro/abonament/', 
        'despre-yoxo': 'https://www.yoxo.ro/help/despre-yoxo/', 
        'alte-servicii': 'https://www.yoxo.ro/help/alte-servicii/', 
        'roaming': 'https://www.yoxo.ro/help/roaming/', 
        'facturi-plati-si-consum': 'https://www.yoxo.ro/help/facturi-plati-si-consum/', 
        'inchidere-abonament': 'https://www.yoxo.ro/help/inchidere-abonament/', 
        'portare': 'https://www.yoxo.ro/help/portare/', 
        'esim': 'https://www.yoxo.ro/help/esim/', 
        'magazin': 'https://www.yoxo.ro/help/magazin/', 
        'aplicatia-si-contul-meu': 'https://www.yoxo.ro/help/aplicatia-si-contul-meu/', 
        'activare-abonament': 'https://www.yoxo.ro/help/activare-abonament/', 
        'administrare-abonament-si-optiuni': 'https://www.yoxo.ro/help/administrare-abonament-si-optiuni/', 
        'servicii-de-urgenta': 'https://www.yoxo.ro/help/servicii-de-urgenta/'
        }

    @staticmethod
    def load_prompt(file_path):
        Config.logger.debug(f"Entered into method load_prompt({file_path})")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            Config.logger.error(f"File not found - {file_path}")
            return ""
    
    @staticmethod
    def get_PROMPT(prompt_type):
        Config.logger.debug(f"Entered into method get_PROMPT({prompt_type})")
        if prompt_type == "CATEG_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "categ_prompt.txt")
        elif prompt_type == "QA_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "qa_prompt.txt")
        elif prompt_type == "ROAMING_SOURCE_START_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "roaming_source_start_prompt.txt")
        elif prompt_type == "DEFAULT_SOURCE_START_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "default_source_start_prompt.txt")
        elif prompt_type == "ASSISTANT_CATEG_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "assistant_categ_prompt.txt")
        elif prompt_type == "ASSISTANT_QA_PROMPT":
            return Config.load_prompt(Config.PROMPTS_FOLDER + "assistant_qa_prompt.txt")