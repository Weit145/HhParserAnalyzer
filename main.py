import re
import requests
from bs4 import BeautifulSoup

# https://spb.hh.ru/search/vacancy?text=Кассир&ored_clusters=true&order_by=publication_time&page=0

class Parser:
    def __init__(self, select_work, mx:int = 20):
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
            try:
                soup = BeautifulSoup(html, "html.parser")
                self.find_price(soup)
            except Exception:
                break
            page += 1
        print(self.salaries)
    
    def find_price(self, soup:BeautifulSoup):
        vacancy_cards = soup.find_all("div", {"data-qa": "vacancy-serp__vacancy"})
        if not vacancy_cards:
            raise ValueError("No vacancies found")
        
        for card in vacancy_cards:
                
                if len(self.salaries) >= self.mx:
                    break

                fn=card.find(class_="magritte-text___pbpft_4-4-4 magritte-text_style-primary___AQ7MW_4-4-4 magritte-text_typography-label-1-regular___pi3R-_4-4-4")
                if fn is None:
                    continue
            
                price = self.check_valute(fn.text)
                if price is None:
                    continue

                self.salaries.append(price)

    def check_valute(self, fn:str)->int | None:
        if "₽" in fn:
            return self.check_price(fn)
        elif "$" in fn:
            return self.check_price(fn, 76)
        elif "€" in fn:
            return self.check_price(fn, 91)
        else:
            return None

    def check_price(self, price:str, x:int=1)->int | None:
        price = price.replace('\xa0', ' ').strip()
        price = price.replace('\u202f', '')
        numbers = re.findall(r'\d+', price)
        n = len(numbers)
        if n == 2:
            return ((int(numbers[0]) + int(numbers[1])) // 2)*x
        elif n == 1:
            return int(numbers[0])*x
        else:
            return None
    
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