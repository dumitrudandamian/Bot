import csv
import xlsxwriter
import time
from llm_processors.base_question_processor import BaseQuestionProcessor
from signal_handler import SignalHandler
import logging

class BatchProcessor:
    def __init__(self, question_processor: BaseQuestionProcessor):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.question_processor = question_processor
    
    def process(self, fisier_intrebari, fisier_intrebari_raspunsuri):
        self.logger.debug(f"Entered into process() method. Before open: {fisier_intrebari}")
        try:
            with open(fisier_intrebari, mode='r', encoding='utf-8') as fisier:
                cititor_csv = csv.reader(fisier)
                workbook, worksheet = self.create_workbook(fisier_intrebari_raspunsuri)
                self.write_header(workbook, worksheet)
                self.logger.info(f"Start processing: {fisier_intrebari}")
                for i, rand in enumerate(cititor_csv, start=1):
                    if len(rand) >= 3:
                        no_intrebare, intrebare = rand[1], rand[2]
                        categorii, raspuns = self.question_processor.answer_question(intrebare)
                        self.write_row(worksheet, i, no_intrebare, intrebare, categorii, raspuns)

                workbook.close()
                self.logger.info(f"End processing!")
        except FileNotFoundError:
            self.logger.error(f"File not found: {fisier_intrebari}")
        except IOError as e:
            self.logger.error(f"IOError: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def create_workbook(self, name):
        self.logger.debug(f"Entered into create_workbook({name}) method.")
        workbook = xlsxwriter.Workbook(name)
        worksheet = workbook.add_worksheet()
        return workbook, worksheet

    def write_header(self, workbook, worksheet):
        self.logger.debug(f"Entered into write_header() method.")
        bold = workbook.add_format({'bold': True})
        headers = ['ID', 'Intrebare', 'Categorii intrebare', 'Raspuns intrebare']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

    def write_row(self, worksheet, index, no_intrebare, intrebare, categorii, raspuns):
        worksheet.write(index, 0, no_intrebare)
        worksheet.write(index, 1, intrebare)
        worksheet.write(index, 2, str(categorii))
        worksheet.write(index, 3, raspuns)
        self.logger.info({"intrebare":intrebare, "categories": categorii, "answer": raspuns})