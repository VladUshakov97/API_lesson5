import requests
import time
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8
    
    return None

def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    
    if not salary:
        return None
    elif salary.get('currency') != 'RUR':
        return None
    
    salary_from = salary.get('from')
    salary_to = salary.get('to')

    return predict_salary(salary_from, salary_to)

def get_hh_statistics(languages_list):
    hh_url = 'https://api.hh.ru/vacancies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    statistics = {}
    request_count = 0

    for language in languages_list:
        salaries = []
        vacancies_found = 0
        page = 0

        while True:
            params = {'text': language, 'area': '1', 'period': '30', 'page': page}
    
            response = requests.get(hh_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            

            request_count += 1

            if request_count % 30 == 0:
                time.sleep(3)
        
            if page == 0:
                vacancies_found = data['found']
                pages = data['pages']
    
            for vacancy in data['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary is not None:
                    salaries.append(salary)

            page += 1

            if page >= pages:
                break

        vacancies_processed = len(salaries)

        if salaries:
            average_salary = int(sum(salaries) / len(salaries))
        else:
            average_salary = 0

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }

    return statistics
    
def predict_rub_salary_sj(vacancy):
    if vacancy.get('currency') != 'rub':
        return None

    return predict_salary(
        vacancy.get('payment_from'),
        vacancy.get('payment_to')
    )    

def get_sj_statistics(languages_list):
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': 'v3.r.139766299.22b40a6d45e97a5bfcbd7c61e3620504f166135e.13800b3bbe25ae6b9842bacc8d64cbe37bf4ba74'}
    statistics = {}
    request_count = 0
    
    for language in languages_list:
        salaries = []
        vacancies_found = 0
        page = 0

        while True:
            params = {'keywords': language, 'town': 4, 'count': 100, 'page': page}

            response = requests.get(sj_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            request_count += 1
            if request_count % 20 == 0:
                time.sleep(1)

            if page == 0:
                vacancies_found = data['total']

            for vacancy in data['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if salary is not None:
                    salaries.append(salary)

            if not data['more']:
                break

            page += 1

        vacancies_processed = len(salaries)

        if salaries:
            average_salary = int(sum(salaries) / len(salaries))
        else:
            average_salary = 0

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed,
            'average_salary': average_salary
        }

    return statistics

def print_table(statistics, title):
    table_data = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    
    for language, stats in statistics.items():
        table_data.append([
            language,
            stats['vacancies_found'],
            stats['vacancies_processed'],
            stats['average_salary']
        ])

    table = AsciiTable(table_data, title)
    print(table.table)

if __name__ == "__main__":
    languages = ['Python', 'Java', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', '1c', 'c']

    hh_stats = get_hh_statistics(languages)
    sj_stats = get_sj_statistics(languages)

    print_table(hh_stats, 'HH.ru')
    print()
    print_table(sj_stats, 'SuperJob')