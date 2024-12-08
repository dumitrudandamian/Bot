from flask import Flask, request, jsonify, render_template, send_file, after_this_request
from prometheus_client import Counter, Histogram, generate_latest, start_http_server
from flasgger import Swagger, swag_from
from llm_processors.base_question_processor import BaseQuestionProcessor
from config import Config
from aq_download import CategoryDownloader
from batch_processor import BatchProcessor
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import json
import logging
import time

class RestAPI:
    def __init__(self, question_processor: BaseQuestionProcessor):
        self.app = Flask(__name__)
        CORS(self.app)
        CORS(self.app, resources={r"/ask": {"origins": ["https://yoxo.ro", "https://orange.ro"]}})

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Started prometheus client on: {Config.PROMETHEUS_PORT}")

        start_http_server(Config.PROMETHEUS_PORT)
        self.ask_request_counter = Counter('ask_requests_served_total', 'Total number of API requests served')
        self.ask_response_time_histogram = Histogram('ask_response_time_seconds', 'API response time in seconds')
        self.ask_limit_counter = Counter('ask_requests_limited_total', 'Total number of API requests limited')

        # Create the Limiter instance
        self.limiter = Limiter(
            key_func = self.get_ip_from_header,
            app=self.app,
            #default_limits=[Config.DEFAULT_LIMIT_PER_DAY, Config.DEFAULT_LIMIT_PER_HOUR],
            on_breach=self.rate_limit_exceeded 
        )

        self.swagger = Swagger(self.app, template={
            "swagger": "2.0",
            "info": {
                "title": "YoxoFaqBot API",
                "description": "REST API documentation",
                "version": "1.0.0"
            },
            "basePath": "/faqbot/api/",
            "definitions": {
                "AskResponse": {
                    "type": "object",
                    "properties": {
                        "categories": {
                            "type": "array",
                            "items": {
                                        "type": "object",
                                        "properties": {
                                            "category_name": {
                                                "type": "string"
                                            },
                                            "category_link": {
                                                "type": "string"
                                            }
                                        }
                                    }
                        },
                        "answer": {
                            "type": "string"
                        }
                    }
                },
                "ChatResponse": {
                    "type": "object",
                    "properties": {
                        "categories": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "answer": {
                            "type": "string"
                        }
                    }
                }                
            }
        })

        self.question_processor = question_processor
        self.ensure_upload_folder_exists()
        
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.lock = Lock()
        self.is_processing = False
        self.output_file_name = ""
        self.input_file_name = ""

        self.app.add_url_rule('/faqbot/api/public/ask', 'ask', self.limited_ask, methods=['POST'])
        self.app.add_url_rule('/faqbot/api/private/chat', 'chat', self.limited_chat, methods=['POST'])
        self.app.add_url_rule('/faqbot/api/private/upload', 'upload', self.upload, methods=['POST'])
        self.app.add_url_rule('/faqbot/api/private/batch_process_status', 'batch_process_status', self.batch_process_status, methods=['GET'])
        self.app.add_url_rule('/faqbot/web', 'web', self.web, methods=['GET'])
        self.app.add_url_rule('/faqbot/api/private/config/<file_name>', 'get_config', self.get_config, methods=['GET'])
        self.app.add_url_rule('/faqbot/api/private/config/<file_name>', 'save_config', self.save_config, methods=['POST'])
        self.app.add_url_rule('/faqbot/api/private/download/<file_name>', 'get_download', self.get_download, methods=['GET'])
        self.app.add_url_rule('/faqbot/api/private/download/<file_name>', 'save_download', self.save_download, methods=['POST'])
        self.app.add_url_rule('/aqbot/api/private/download', 'list_download_files', self.list_download_files, methods=['GET'])
        self.app.add_url_rule('/faqbot/api/private/update-all', 'update_all_files', self.update_all_files, methods=['POST'])
        self.app.add_url_rule('/faqbot/api/private/download-answers', 'get_download_answers', self.get_download_answers, methods=['GET'])
        self.app.add_url_rule('/health', 'health', self.health, methods=['GET'])
        self.app.add_url_rule('/faqbot/api/private/model_name', 'model_name', self.get_model_name, methods=['GET'])

    def rate_limit_exceeded(self, f):
        self.logger.warn(f"Rate limit exceeded for client address: {self.get_ip_from_header}")
        self.ask_limit_counter.inc() # increment Prometheus counter
        response = jsonify({
            "status": 429,
            "error": "Rate limit exceeded",
            "categories":["RateLimitException"],
            "answer": "You have exceeded your rate limit. Please try again later."
        })
        response.status_code = 429
        return response
    
    def get_ip_from_header(self):
        # Assuming the IP is passed in the 'X-Forwarded-For' header
        if 'X-Forwarded-For' in request.headers:
            # The header can contain multiple IPs, we take the first one
            remote_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
            self.logger.debug(f"Remote client address identified from Header: {remote_ip}")
            return remote_ip
        self.logger.debug(f"Remote client address identified from IP: {request.remote_addr}")
        return request.remote_addr
    
    def batch_process_status(self):
        self.logger.debug("Entered into batch_process_status() method.")
        with self.lock:
            return jsonify(is_processing=self.is_processing, output_file_name=os.path.basename(self.output_file_name)), 200
        
    def batch_processor_callback(self, future):
        self.logger.debug("Entered into batch_processor_callback() method.")
        with self.lock:
            self.is_processing = False
            os.remove(self.input_file_name)
            self.logger.info(f"Finalized the batch file answer job for the file: {self.input_file_name}")

    def async_process(self, file_path, output_file_name):
        self.logger.debug("Entered into async_process() method.")
        self.logger.info(f"INFO: Start batch processor on file: {file_path}. Output file is: {output_file_name}")
        batch_processor = BatchProcessor(self.question_processor)
        batch_processor.process(fisier_intrebari=file_path, fisier_intrebari_raspunsuri=output_file_name)
    
    @swag_from({
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string"
                        }
                    }
                },
                "required": ["question"]
            }
        ],
        "responses": {
            "200": {
                "description": "The answer to the question.",
                "schema": {
                    "$ref": "#/definitions/AskResponse"
                }
            }
        }
    })
    def limited_ask(self):
        self.logger.debug("Entered into limited_ask() method.")
        @self.limiter.limit(Config.ASK_LIMIT_PER_HOUR)
        def ask_inner():
            self.ask_request_counter.inc() # increment Prometheus counters 
            start_time = time.time()

            intrebare = request.json.get('question', '')
            categorii, raspuns = self.question_processor.answer_question(intrebare)

            cleaned_raspuns = raspuns.replace('\n', '')
            categories_with_links = [{"category_name": category, "category_link": Config.CATEGORIES_DICT.get(category, '')}
                                        for category in categorii
                                        if category != "categorie-necunoscuta"
                                    ]

            self.logger.info({"intrebare":intrebare, "categories": categories_with_links, "answer": cleaned_raspuns})
            response_time = time.time() - start_time
            self.ask_response_time_histogram.observe(response_time)  # Measure the response time
            return jsonify({"categories": categories_with_links, "answer": cleaned_raspuns})
        return ask_inner()

    @swag_from({
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "schema": {
                    "type": "object",
                    "properties": {
                        "chatHistory": {
                            "type": "array",
                             "items": {
                                "type": "string"
                            }                        
                        },
                        "conversationId": {
                            "type": "string"     
                        }
                    }
                },
                "required": ["chatHistory", "conversationId"]
            }
        ],
        "responses": {
            "200": {
                "description": "The answer to the question.",
                "schema": {
                    "$ref": "#/definitions/ChatResponse"
                }
            }
        }
    })
    def limited_chat(self):
        self.logger.info("Entered into limited_chat() method." + str(request.json))
        @self.limiter.limit(Config.ASK_LIMIT_PER_HOUR)
        def ask_inner():
            self.ask_request_counter.inc() # increment Prometheus counters 
            start_time = time.time()

            intrebari = request.json.get('chatHistory', '')
            conversationId = request.json.get('conversationId', 'empty')
            self.logger.debug(str(conversationId) + ": Intrebari din chatHistory:" + str(intrebari))

            categorii, raspuns = self.question_processor.chat(intrebari)
            
            response_time = time.time() - start_time
            self.ask_response_time_histogram.observe(response_time)  # Measure the response time
            self.logger.info("{\"conversationId\": " + str(conversationId) +", \"categories\": " + str(categorii) +", \"answer\":\"" + raspuns + "\"}")
            return jsonify({"categories": categorii, "answer": raspuns})
        return ask_inner()
    
    def ensure_upload_folder_exists(self):
        self.logger.debug("Entered into ensure_upload_folder_exists")
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            self.logger.info(f"Upload folder {Config.UPLOAD_FOLDER} does not exist and it was created.")

    def upload(self):
        self.logger.debug("Entered into upload() method.")
        with self.lock:
            if self.is_processing:
                self.logger.warning("An upload of anothet batch of questions was triggered while still processing a previous one.")
                return jsonify(success=False, message='A file is already being processed - ', output_file_name=os.path.basename(self.output_file_name)), 409
            else: 
                if 'file' not in request.files:
                    return 'No file part', 400
                file = request.files['file']
                if file.filename == '':
                    return 'No selected file', 400
                if file:
                    self.input_file_name = os.path.join(Config.UPLOAD_FOLDER, file.filename)
                    file.save(self.input_file_name)
                    self.output_file_name = os.path.join(Config.UPLOAD_FOLDER, os.path.splitext(os.path.basename(file.filename))[0]+ '-Answers.xlsx')
                    self.is_processing = True
                    future = self.executor.submit(self.async_process, os.path.join(Config.UPLOAD_FOLDER, file.filename), self.output_file_name)
                    future.add_done_callback(self.batch_processor_callback)
                    return jsonify(success=True, message='The file is being being processed...', output_file_name=os.path.basename(self.output_file_name)), 200

    def get_config(self, file_name):
        self.logger.debug(f"Entered into get_config({file_name}) method. Load from folder: " + Config.PROMPTS_FOLDER)
        try:
            with open(os.path.join(Config.PROMPTS_FOLDER, file_name), 'r') as file:
                content = file.read()
            return jsonify({"content": content}), 200
        except FileNotFoundError:
            return jsonify({"message": "Configuration file not found"}), 404

    def get_model_name(self):
        content = "GPT-4o" if Config.LLM_MODEL == "gpt" else "Gemini 1.5 Pro" if Config.LLM_MODEL == "gemini" else "NO_MODEL"
        
        self.logger.debug(f"Entered into get_model_name() method. Returned: {content}")
        return jsonify({"content": content}), 200
        
    def save_config(self, file_name):
        self.logger.debug(f"Entered into save_config({file_name}) method.")
        content = request.json.get('content', '')
        with open(os.path.join(Config.PROMPTS_FOLDER, file_name), 'w') as file:
            file.write(content)
        return jsonify({"message": "Configuration file saved successfully"}), 200

    def get_download(self, file_name):
        self.logger.debug(f"Entered into get_download({file_name}) method. Load from folder: " + Config.FAQ_DOWNLOAD_FOLDER)
        try:
            with open(os.path.join(Config.FAQ_DOWNLOAD_FOLDER, file_name), 'r') as file:
                content = file.read()
            return jsonify({"content": content}), 200
        except FileNotFoundError:
            return jsonify({"message": "File not found"}), 404

    def get_download_answers(self):
        self.logger.debug("Entered into get_download_answers() method.")
        try:
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(self.output_file_name)
                except Exception as e:
                    self.logger.error(f"Error removing file: {e}")
                return response
            return send_file(
                self.output_file_name,
                as_attachment=True,
                download_name=os.path.basename(self.output_file_name)  # Provides the exact name of the file
            )
        except FileNotFoundError:
            return jsonify({"message": "File not found"}), 404
        
    def save_download(self, file_name):
        self.logger.debug(f"Entered into save_download({file_name}) method.")
        content = request.json.get('content', '')
        with open(os.path.join(Config.FAQ_DOWNLOAD_FOLDER, file_name), 'w') as file:
            file.write(content)
        return jsonify({"message": "File saved successfully"}), 200

    def list_download_files(self):
        self.logger.debug("Entered into list_download_files() method.")
        try:
            files = os.listdir(Config.FAQ_DOWNLOAD_FOLDER)
            return jsonify({"files": files}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500

    def update_all_files(self):
        self.logger.debug("Entered into update_all_files() method.")
        try:
            self.logger.info("Triggered update of FAQ from the web site.")
            downloader = CategoryDownloader(Config.FAQ_BASE_URL, Config.FAQ_DOWNLOAD_FOLDER, Config.PROXIES)
            Config.CATEGORIES_DICT = downloader.fetch_and_save_category_content()
            return jsonify({"message": "All files updated successfully"}), 200
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return jsonify({"message": str(e)}), 500

    def web(self):
        self.logger.debug("Entered into web() method.")
        return render_template(Config.ASK_QUESTION_HTML_FILE)
    
    def health(self):
        return jsonify(status="UP"), 200
    
    def run(self):
        self.app.run(debug=False, host='0.0.0.0', port=Config.REST_PORT)