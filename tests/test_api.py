import requests
import re
import json
from statistics import mean
from src.hh_parser.config import settings

def test():
    url = "https://api.hh.ru/vacancies"
    headers = {
            "Authorization": f"Bearer {settings.token_hh}",
            "HH-User-Agent": f"{settings.name_app} ({settings.email})"
        }
    params = {
        "text": "Python",
        "per_page": 20,
        "page": 0
    }

    st = set()
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        return
    
    data = response.json()
    items = data.get("items", [])
    
    for item in items:
        vacancy_id = item.get("id")
        st.add(vacancy_id)
    all_results = []

    for vacancy_id in st:
        vacancy_url = f"{url}/{vacancy_id}"
        vacancy_response = requests.get(vacancy_url, headers=headers)
        
        if vacancy_response.status_code == 200:
            vacancy_data = vacancy_response.json()
            result = {}
            # print(vacancy_data)
            work_schedule_by_days = vacancy_data.get("work_schedule_by_days",{})
            wh = vacancy_data.get("working_hours",{})
            result["work_schedule_by_days"]= work_schedule_by_days
            result["wh"] = wh
            if result not in all_results:
                all_results.append(result)
            
            working_hours = vacancy_data.get("working_hours", [])
            
            daily_hours = parse_daily_hours(working_hours)
            monthly_hours = monthly_hours_from_daily(daily_hours)
            
            print("daily:", daily_hours, "monthly:", monthly_hours)
        
        else:
            print(f"Ошибка при получении вакансии {vacancy_id}: {vacancy_response.status_code}")
    with open('vacancies.json', 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=4)
            

def monthly_hours_from_daily(daily_hours, work_days_per_month=22):
    if daily_hours is None:
        return None
    return daily_hours * work_days_per_month


def parse_daily_hours(working_hours_list):
    """
    working_hours_list: [{'id': 'HOURS_8', 'name': '8\xa0часов'}, ...]
    return: float | None  (часы в день)
    """
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













# def monthly_hours(self, data):
#         working_hours = data.get("working_hours", [])
#         schedule = data.get("work_schedule_by_days", [])
#         if schedule:
#             for item in schedule:
#                 name = item.get("name")
#                 if name:
#                     self.unique_schedule.add(name)
#         if working_hours:
#             for item in working_hours:
#                 name = item.get("name")
#                 if name:
#                     self.unique_wh.add(name)

#         daily_hours = self.parse_daily_hours(working_hours)

#         if daily_hours is not None:
#             days = self.days_from_schedule(schedule)
#             if days is None:
#                 days = 22
#             return daily_hours * days

#         days = self.days_from_schedule(schedule)
#         if days is not None:
#             return 8 * days

#         return None
    
#     def days_from_schedule(self, schedule_list):
#         if not schedule_list:
#             return None

#         mapping = {
#             "FIVE_ON_TWO_OFF": 22,
#             "SIX_ON_ONE_OFF": 26,
#             "TWO_ON_TWO_OFF": 15,
#             "THREE_ON_THREE_OFF": 15,
#             "FOUR_ON_FOUR_OFF": 15,
#             "FOUR_ON_TWO_OFF": 20,
#             "THREE_ON_TWO_OFF": 20,
#         }

#         days = []

#         for item in schedule_list:
#             sid = item.get("id")
#             if sid in mapping:
#                 days.append(mapping[sid])

#         if not days:
#             return None

#         return mean(days)

#     def monthly_hours_from_daily(self, daily_hours, work_days_per_month=22):
#         if daily_hours is None:
#             return None
#         return daily_hours * work_days_per_month


#     def parse_daily_hours(self, working_hours_list):
#         if not working_hours_list:
#             return None
        
#         hours = []
        
#         for item in working_hours_list:
#             name = item.get("name", "")
#             match = re.search(r"\d+", name)
#             if match:
#                 hours.append(int(match.group()))
        
#         if not hours:
#             return None
        
#         if len(hours) == 1:
#             return hours[0]
        
#         return mean(hours)