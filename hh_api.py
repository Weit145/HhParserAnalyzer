import requests
import re
from statistics import mean
from config import settings
import pandas as pd



class HHParserApi:
    
    def __init__(self, vacancia:str) -> None:
        self.vacancia = vacancia

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
        self.size()
        self.found_id()
        self.found_items()
        return pd.DataFrame(self.vacancies)

        

    def found_items(self):
        for id in self.st:
            url = f"{self.url}/{id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                experience = self.experience(data)
                monthly_hours = self.monthly_hours(data)
                employer = self.employer(data)
                area = self.area(data)
                salary = self.salary(data)
                name = data.get("name",None)
                self.vacancies.append({
                    'name': name,
                    'salary': salary,
                    'experience': experience,
                    'company': employer,
                    'region': area,
                    'monthly_hours': monthly_hours,
                })
            else:
                continue

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
        daily_hours = self.parse_daily_hours(working_hours)
        monthly_hours = self.monthly_hours_from_daily(daily_hours)
        return monthly_hours

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
            self.params = {"text": self.vacancia,
                        "page": page,}
            response = requests.get(self.url, headers=self.headers, params=self.params)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    self.st.add(item.get("id"))
            else:
                continue

    def size(self)->None:
        self.params = {"text": self.vacancia,
                        "page": 0,
                        "per_page": 100,}
        response = requests.get(self.url, headers=self.headers, params=self.params)
        data = response.json()
        self.pages = data.get("pages",0)
        self.per_page = data.get("per_page",0)

    def write_csv (self,df):
        output_file = f"{self.vacancia}.csv"
        df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')



# def test():
#     url = "https://api.hh.ru/vacancies"
#     headers = {
#             "Authorization": f"Bearer {settings.token_hh}",
#             "HH-User-Agent": f"{settings.name_app} ({settings.email})"
#         }
#     params = {
#         "text": "Python",
#         "per_page": 50,
#         "page": 0
#     }

#     st = set()
    
#     response = requests.get(url, headers=headers, params=params)
#     if response.status_code != 200:
#         print(f"Ошибка: {response.status_code}")
#         return
    
#     data = response.json()
#     items = data.get("items", [])
    
#     for item in items:
#         vacancy_id = item.get("id")
#         st.add(vacancy_id)
    
#     for vacancy_id in st:
#         vacancy_url = f"{url}/{vacancy_id}"
#         vacancy_response = requests.get(vacancy_url, headers=headers)
        
#         if vacancy_response.status_code == 200:
#             vacancy_data = vacancy_response.json()
            
#             working_hours = vacancy_data.get("working_hours", [])
            
#             daily_hours = parse_daily_hours(working_hours)
#             monthly_hours = monthly_hours_from_daily(daily_hours)
            
#             print("daily:", daily_hours, "monthly:", monthly_hours)
        
#         else:
#             print(f"Ошибка при получении вакансии {vacancy_id}: {vacancy_response.status_code}")


# def monthly_hours_from_daily(daily_hours, work_days_per_month=22):
#     if daily_hours is None:
#         return None
#     return daily_hours * work_days_per_month


# def parse_daily_hours(working_hours_list):
#     """
#     working_hours_list: [{'id': 'HOURS_8', 'name': '8\xa0часов'}, ...]
#     return: float | None  (часы в день)
#     """
#     if not working_hours_list:
#         return None
    
#     hours = []
    
#     for item in working_hours_list:
#         name = item.get("name", "")
#         match = re.search(r"\d+", name)
#         if match:
#             hours.append(int(match.group()))
    
#     if not hours:
#         return None
    
#     if len(hours) == 1:
#         return hours[0]
    
#     return mean(hours)