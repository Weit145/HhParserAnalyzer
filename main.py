import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
class Parser:
    def __init__(self, select_work, mx:int = 10):
        self.mx = mx
        self.work = self.validate(select_work)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7",
        })
        self.vacancies = []

    def run(self):
        page = 0
        while len(self.vacancies) < self.mx:
            url = f"https://spb.hh.ru/search/vacancy?text={self.work}&page={page}"
            html = self.fetch(url)
            if not html:
                break
            
            soup = BeautifulSoup(html, "html.parser")
            
            script_tag = soup.find("template", {"id": "HH-Lux-InitialState"})
            if not script_tag:
                break
            
            try:
                data = json.loads(script_tag.text)
                vacancies_on_page = data.get("vacancySearchResult", {}).get("vacancies", [])
            except (json.JSONDecodeError, AttributeError):
                break

            if not vacancies_on_page:
                break

            for vacancy_json in vacancies_on_page:
                if len(self.vacancies) >= self.mx:
                    break
                
                salary = vacancy_json.get('compensation')
                salary_numeric = None
                if salary:
                    salary_from = salary.get('from')
                    salary_to = salary.get('to')
                    if salary_from and salary_to:
                        salary_numeric = (salary_from + salary_to) / 2
                    elif salary_from:
                        salary_numeric = salary_from
                    elif salary_to:
                        salary_numeric = salary_to


                experience_mapping = {
                    "noExperience": 0,
                    "between1And3": 1,
                    "between3And6": 3,
                    "moreThan6": 6,
                }
                experience_raw = vacancy_json.get('workExperience')
                experience = experience_mapping.get(experience_raw, experience_raw)

                company = vacancy_json.get('company', {}).get('name')
                region = vacancy_json.get('area', {}).get('name')
                vacancy_name = vacancy_json.get('name')
                
                responses_count = vacancy_json.get('responsesCount')
                
                self.vacancies.append({
                    'name': vacancy_name,
                    'salary': salary_numeric,
                    'experience': experience,
                    'company': company,
                    'region': region,
                    'responses': responses_count,
                })

            page += 1

        df = pd.DataFrame(self.vacancies)
        return df



    def validate(self, select_work)->str:
        if select_work == "":
            raise ValueError("No work selected")
        select_work = select_work.rstrip().replace(" ", "+")
        if "+" in select_work:
            select_work = select_work.replace("+", "%2B")
        return select_work

    def fetch(self, url) -> str | None:
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return None
        
def main():
    select_work = input("Enter the job title to search for: ")
    mx =  int(input("Enter the maximum number of vacancies to fetch: "))
    parser = Parser(select_work, mx)
    results_df = parser.run()
    print(results_df)
    
    output_file = "vacancies.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(results_df.to_string(index=False))


if __name__ == "__main__":
    main()