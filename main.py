import re
import requests
from bs4 import BeautifulSoup

# https://spb.hh.ru/search/vacancy?text=Кассир&ored_clusters=true&order_by=publication_time&page=0

class Parser:
    def __init__(self, select_work, mx:int = 200):
        self.mx = mx
        
        self.work = self.validate(select_work)
        self.url = f"https://spb.hh.ru/search/vacancy?text={self.work}&ored_clusters=true&order_by=publication_time&page="
        
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; Parser/1.0)"}
        )
        
        self.salaries = []
        
    def run(self):
        page = 0
        while len(self.salaries) < self.mx:
            self.url = f"https://spb.hh.ru/search/vacancy?text={self.work}&ored_clusters=true&order_by=publication_time&page={page}"
            
            html = self.fetch()
            print(self.url)
            if html is None:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            vacancy_cards = soup.find_all("div", {"data-qa": "vacancy-serp__vacancy"})
            for card in vacancy_cards:
                spans = card.find_all('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if text =="":
                        print(self.salaries)
                        return
                    if '₽' in text and "за\xa0месяц" in text and len(self.salaries) < self.mx:
                        cleaned = text.replace('\xa0', ' ').strip()
                        cleaned = cleaned.replace('\u202f', '')
                        numbers = re.findall(r'\d+', cleaned)
                        if len(numbers)==2:
                            numbers=(int(numbers[0])+int(numbers[1]))/2
                            self.salaries.append(int(numbers))
                            continue
                        self.salaries.append(int(numbers[0]))
                        break
            page += 1
        print(self.salaries)
            
    
    def validate(self, select_work)->str:
        if select_work == "":
            raise ValueError("No work selected")
        if select_work [0] == " ":
            select_work = select_work[1:]
        if select_work [-1] == " ":
            select_work = select_work[:-1]
        return select_work.replace(" ", "+")
    
    def fetch(self) -> str | None:
        try:
            resp = self.session.get(self.url, timeout=10)
            if resp.status_code != 200:
                return None
            if "text/html" not in resp.headers.get("Content-Type", ""):
                return None
            return resp.text
        except Exception:
            return None
        
def main():
    select_work = input()
    parser = Parser(select_work)
    parser.run()
    
if __name__ == "__main__":
    main()