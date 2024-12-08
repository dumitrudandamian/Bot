from llm_processors.base_question_processor import BaseQuestionProcessor

class InteractiveMode:
    def __init__(self, question_processor: BaseQuestionProcessor):
        self.question_processor = question_processor
    
    def run(self):
        while True:
            intrebare = input("Enter your question: ")
            categorii, raspuns = self.question_processor.answer_question(intrebare)
            print(f"Categorii: {categorii}\nRaspuns: \n{raspuns}")