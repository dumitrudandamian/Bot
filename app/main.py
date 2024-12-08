import sys
import argparse
from llm_processors.gemini_question_processor import GeminiQuestionProcessor
from llm_processors.gpt_question_processor import GPTQuestionProcessor
from batch_processor import BatchProcessor
from interactive_mode import InteractiveMode
from rest_api import RestAPI
from app.faq_download import CategoryDownloader
import logging
import logging.config
import sys
import yaml
from config import Config
import os
import shutil
import requests
import time

def setup_logging(config_path = Config.CONFIG_FOLDER + "/logging_config.yaml", default_level=logging.INFO):
    logging.basicConfig(
        level=default_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    with open(config_path, 'rt') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

def get_processor(processor_type: str):
    processors = {
        "gemini": GeminiQuestionProcessor(Config.GEMINI_MODEL),
        "gpt": GPTQuestionProcessor(Config.GPT_MODEL)
    }
    return processors.get(processor_type.lower(), None)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(description="Process some modes.")
    parser.add_argument('--mode', default='rest', choices=['batch', 'it', 'rest', 'init', 'update_faq', 'reset'],
                        help="Specify the mode of operation: 'batch', 'it' (interactive), or 'rest'. Defaults to 'it'.")
    parser.add_argument('--input', help="Specify the CSV input file")
    parser.add_argument('--output', help="Specify the XLS output file")
    parser.add_argument('--processor', default=Config.LLM_MODEL, choices=['gemini', 'gpt'],
                        help="Specify which processor to use: 'gemini' or 'gpt'. Defaults to 'gemini'.")

    args = parser.parse_args()
    question_processor = get_processor(args.processor)

    if not question_processor:
        logger.error(f"Unsupported processor type {args.processor}")
        sys.exit(1)

    if args.mode == 'batch':
        logger.info("Starting in batch mode...")
        if not args.input or not args.output:
            parser.error("--input and --output arguments are required in batch mode.")
            sys.exit(1)
        batch_processor = BatchProcessor(question_processor)
        batch_processor.process(fisier_intrebari=args.input, fisier_intrebari_raspunsuri=args.output)
    elif args.mode == 'rest': 
        logger.info("Starting in REST mode...")
        rest_api = RestAPI(question_processor)
        rest_api.run()
    elif args.mode == 'init':
        
        logger.info("Initialize the app to run in K8S. Check if shared folder exists and not empty")
        if not os.path.exists(Config.FAQ_DOWNLOAD_FOLDER) or not os.listdir(Config.FAQ_DOWNLOAD_FOLDER):
            logger.info("Initialize the faq folder with the data from the image")
            shutil.copytree('/yoxo/faq', Config.FAQ_DOWNLOAD_FOLDER, dirs_exist_ok=True)

        source_folder = '/yoxo/prompts'
        target_folder = Config.PROMPTS_FOLDER
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            logger.info("Created the target prompts folder")

        for item in os.listdir(source_folder):
            source_path = os.path.join(source_folder, item)
            target_path = os.path.join(target_folder, item)
            
            if os.path.isfile(source_path) and not os.path.exists(target_path):
                shutil.copy2(source_path, target_path)
                logger.info(f"Copied {item} to {target_folder}")

    elif args.mode == 'reset':
        logger.info("Initialize the faq folder with the data from the image")
        shutil.copytree('/yoxo/faq', Config.FAQ_DOWNLOAD_FOLDER, dirs_exist_ok=True)
        logger.info("Initialize the prompts folder with the data from the image")
        shutil.copytree('/yoxo/prompts', Config.PROMPTS_FOLDER, dirs_exist_ok=True)

    elif args.mode == 'update_faq':
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            url = f"http://{Config.K8S_SERVICE_NAME}:{Config.REST_PORT}{Config.FAQ_DOWNLOAD_METHOD}"
            response = requests.post(url, headers=headers)
            logger.info(f"POST HTTP RESULT CODE: {response.status_code}")
            logger.info(response.json())

        except Exception as e:
            logger.error(f"Update FAQ failed: {e}")

        logger.info("Sleep for 1 min before exit to allow investigation...")
        time.sleep(60)
        logger.info("Done. Exit job!")
        sys.exit(0)    

    else:  # Default to interactive mode
        logger.info("Starting in interractive command line mode...")
        interactive_mode = InteractiveMode(question_processor)
        interactive_mode.run()

def create_rest_app():
    setup_logging()
    logger = logging.getLogger(__name__)   
    question_processor = get_processor(Config.LLM_MODEL) 
    if not question_processor:
        logger.error(f"Unsupported processor type {Config.LLM_MODEL}")
        sys.exit(1)
    logger.info("Starting in REST mode...")
    rest_api = RestAPI(question_processor)
    return rest_api.app

if __name__ == "__main__":
    main()