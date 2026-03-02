import requests
import time
import re

from ..config import settings
import pandas as pd



class HHParserApi:
    
    def __init__(self, vacancia:str, path:str = "") -> None:
        self.vacancia = vacancia

        self.path = path    
        self.session = requests.Session()
        self.url = "https://api.hh.ru/vacancies"
        self.headers = {
            "Authorization": f"Bearer {settings.token_hh}",
            "HH-User-Agent": f"{settings.name_app} ({settings.email})"
        }
        self.params = {"text": self.vacancia,
                        "page": 0,
                        "per_page": 100,}

        self.st = set()
        self.pages = 0
        self.per_page = 0

        self.vacancies=[]

    def run(self):
        try:
            self.size()
            self.found_id()
            print("ID:", len(self.st))
            self.found_items()
            print("Vacancies:", len(self.vacancies))
            return pd.DataFrame(self.vacancies)
        finally:
            self.session.close()

        

    def found_items(self):
        for i, id_ in enumerate(self.st, 1):
            url = f"{self.url}/{id_}"
            for _ in range(5):
                try:
                    response = self.session.get(
                        url,
                        headers=self.headers,
                        timeout=1
                    )
                    if response.status_code == 200:
                        data = response.json()
                        row = {
                            "name": data.get("name"),
                            "area": self.area(data),
                            "employer": self.employer(data),
                            "salary": self.salary(data),
                            "experience": self.experience(data),
                            "monthly_hours": self.hours_in_month(data),
                        }
                        self.vacancies.append(row)
                        break

                    if response.status_code == 404:
                        break

                except requests.exceptions.RequestException:
                    time.sleep(1)
            if i % 50 == 0:
                print(f"processed {i}/{len(self.st)}")
            

    def experience(self,data):
        experience = data.get("experience", {})
        experience_id = experience.get("id",None)
        experience_mapping = {
            "noExperience": 0,
            "between1And3": 1,
            "between3And6": 3,
            "moreThan6": 6,
        }
        return experience_mapping.get(experience_id, None)
    
    def hours_in_month(self, data):
        working_hours = data.get("working_hours", [])
        schedule = data.get("work_schedule_by_days", [])
        mn_hour, mx_hour = self.hours(working_hours)
        mn_day, mx_day = self.days(schedule)
        if mn_hour and mx_hour and mn_day and mx_day:
            return (mn_hour*mx_day+mx_hour*mn_day)/2
        return None

    def hours(self, data):
        mx=0
        mn=25
        for item in data:
            name = item.get("name", "")
            match = re.search(r"\d+", name)
            if match:
                res = int(match.group())
                mx=max(mx,res)
                mn=min(mn,res)
        if mx!=0 and mn!=25:
            return mn, mx
        return None, None
    
    def days(self,data):
        mx=0
        mn=40
        for item in data:
            name = item.get("name","")
            match = re.search(r"(\d+)/(\d+)", name)
            if match:
                first = int(match.group(1))
                second = int(match.group(2))
                res = int(first/(first+second)*30)
                mx=max(mx,res)
                mn=min(mn,res)
        if mx!=0 and mn!=40:
            return mn, mx
        return None, None


        
    def employer(self, data):
        employer = data.get("employer",{})
        return employer.get("name", None)
    
    def area(self,data):
        area = data.get("area",{})
        return area.get("name",None)
    
    def salary(self, data):
        salary_data = data.get("salary")  
        if salary_data is None:
            return None

        salary_from = salary_data.get("from")
        salary_to = salary_data.get("to")
        salary_numeric = None

        if salary_from is not None and salary_to is not None:
            salary_numeric = (salary_from + salary_to) / 2
        elif salary_from is not None:
            salary_numeric = salary_from
        elif salary_to is not None:
            salary_numeric = salary_to

        currency = salary_data.get("currency")
        if salary_numeric is not None and currency is not None:
            salary_numeric = self.valut(salary_numeric, currency)

        return salary_numeric
        
    def valut(self, salary,valut):
        rates = {
            "RUR": 1,
            "USD": 76,
            "EUR": 90,
            "KZT": 0.15,
            "UZS": 0.00063
        }
        if valut in rates:
            return salary * rates[valut]
        else:
            return None

    def found_id(self):
        for page in range(self.pages):
            params = {
                "text": self.vacancia,
                "page": page,
                "per_page": self.per_page
            }
            response = self.session.get(
                self.url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    self.st.add(item.get("id"))

    def size(self) -> None:
        params = {
            "text": self.vacancia,
            "page": 0,
            "per_page": 100
        }
        response = self.session.get(
            self.url,
            headers=self.headers,
            params=params,
            timeout=10
        )
        data = response.json()
        self.pages = data.get("pages", 0)
        self.per_page = data.get("per_page", 0)

    def write_csv (self,df):
        output_file = f"{self.path}{self.vacancia}.csv"
        df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')



