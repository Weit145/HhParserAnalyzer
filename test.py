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