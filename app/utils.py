import re

class Util:
    @staticmethod
    def extract_json(markdown_text):
        json_pattern = r'json\s+({.*?})\s+'
        match = re.search(json_pattern, markdown_text, re.DOTALL)
        return match.group(1).strip() if match else markdown_text