import requests
import time
import re
from statistics import mean
from ..config import settings
import pandas as pd



class HHParserApi:
    
    def __init__(self, vacancia:str) -> None:
        self.vacancia = vacancia

        
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

            for attempt in range(5):
                try:
                    response = self.session.get(
                        url,
                        headers=self.headers,
                        timeout=5
                    )

                    if response.status_code == 200:
                        data = response.json()

                        row = {
                            "name": data.get("name"),
                            "area": self.area(data),
                            "employer": self.employer(data),
                            "salary": self.salary(data),
                            "experience": self.experience(data),
                            "monthly_hours": self.monthly_hours(data),
                        }

                        self.vacancies.append(row)
                        break

                    if response.status_code == 404:
                        break

                except requests.exceptions.RequestException:
                    time.sleep(1)

            if i % 50 == 0:
                print(f"processed {i}/{len(self.st)}")

            time.sleep(0.05)

    def experience(self,data):
        experience = data.get("experience", {})
        experience_id = experience.get("id")
        experience_mapping = {
            "noExperience": 0,
            "between1And3": 1,
            "between3And6": 3,
            "moreThan6": 6,
        }
        return experience_mapping.get(experience_id, None)
    
    def monthly_hours(self, data):
        working_hours = data.get("working_hours", [])
        schedule = data.get("work_schedule_by_days", [])

        daily_hours = self.parse_daily_hours(working_hours)

        if daily_hours is not None:
            days = self.days_from_schedule(schedule)
            if days is None:
                days = 22
            return daily_hours * days

        days = self.days_from_schedule(schedule)
        if days is not None:
            return 8 * days

        return None
    
    def days_from_schedule(self, schedule_list):
        if not schedule_list:
            return None

        mapping = {
            "FIVE_ON_TWO_OFF": 22,
            "SIX_ON_ONE_OFF": 26,
            "TWO_ON_TWO_OFF": 15,
            "THREE_ON_THREE_OFF": 15,
            "FOUR_ON_FOUR_OFF": 15,
            "FOUR_ON_TWO_OFF": 20,
            "THREE_ON_TWO_OFF": 20,
        }

        days = []

        for item in schedule_list:
            sid = item.get("id")
            if sid in mapping:
                days.append(mapping[sid])

        if not days:
            return None

        return mean(days)

    def monthly_hours_from_daily(self, daily_hours, work_days_per_month=22):
        if daily_hours is None:
            return None
        return daily_hours * work_days_per_month


    def parse_daily_hours(self, working_hours_list):
        if not working_hours_list:
            return None
        
        hours = []
        
        for item in working_hours_list:
            name = item.get("name", "")
            match = re.search(r"\d+", name)
            if match:
                hours.append(int(match.group()))
        
        if not hours:
            return None
        
        if len(hours) == 1:
            return hours[0]
        
        return mean(hours)
        
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
        output_file = f"{self.vacancia}.csv"
        df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')



