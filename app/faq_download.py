import httpx
from bs4 import BeautifulSoup
from config import Config
import os
import logging

class CategoryDownloader:
    def __init__(self, base_url, download_folder):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = base_url
        self.download_folder = download_folder
        # Ensuring the download directory exists
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

    def download_category(self, category, link):
        self.logger.debug(f"Entered into download_category({category}, {link}) method.")

        response = httpx.get(link, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
        question_links = soup.find_all('a', class_='question-link')

        with open(f"{self.download_folder}/{category}.txt", "w", encoding="utf-8") as file:
            for link in question_links:
                
                response = httpx.get(link.get('href'), verify=False)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')

                sections = soup.find_all('section', class_='yoxo-section_question')
                for section in sections:
                    # Replace 'aici' with 'la adresa' followed by the actual link
                    for a in section.find_all('a', text='aici'):
                        a.replace_with(f"la adresa {a['href']}")
                    text_to_write = section.get_text(separator=' ', strip=True)
                    text_to_write = text_to_write.replace('Descarcă aplicația pe telefonul tău mobil Descarcă aplicația Download', '')
                    text_to_write = text_to_write.replace('\xa0', ' ')
                    file.write(text_to_write + "\n\n")

    def fetch_and_save_category_content(self):
        self.logger.info(f"About to download all FAQs from URL: { self.base_url} ")
        
        response = httpx.get(self.base_url, verify=False)
        response.raise_for_status()
        response.encoding = 'utf-8'
        category_dict = {"detalii-pachete-optiuni": "https://www.yoxo.ro/abonament/"}
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
            help_links = soup.find_all('a', attrs={'data-track-action': 'Help'})
            self.logger.info("Found the following FAQ categories: " + str(help_links))
            
            for link in help_links:
                part_after_last_help = link.get('href')[::-1].split("/pleh/", 1)[0]
                cleaned_part = part_after_last_help[::-1].strip("/")
                category_dict[cleaned_part] = link.get('href')
                self.download_category(category=cleaned_part, link=link.get('href'))
            self.logger.info("The following FAQ categories: " + str(category_dict))

        else:
            self.logger.error(f"Failed to fetch the category page. Status code: {response.status_code}")
        
        return category_dict
