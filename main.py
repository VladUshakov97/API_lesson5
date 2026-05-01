import os
import time
import requests
from terminaltables import AsciiTable

HH_URL = 'https://api.hh.ru/vacancies'
HH_MOSCOW_AREA = 1
HH_SEARCH_PERIOD_DAYS = 30
HH_REQUESTS_BEFORE_SLEEP = 30
HH_SLEEP_SECONDS = 3

SJ_URL = 'https://api.superjob.ru/2.0/vacancies/'
SJ_MOSCOW_TOWN = 4
SJ_PAGE_SIZE = 100
SJ_REQUESTS_BEFORE_SLEEP = 20
SJ_SLEEP_SECONDS = 1

SALARY_FROM_FACTOR = 1.2
SALARY_TO_FACTOR = 0.8

HH_HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

SJ_HEADERS = {
    'X-Api-App-Id': os.getenv('SJ_API_KEY')
}

def predict_salary(salary_from, salary_to):
    if salary_from is not None and salary_to is not None:
        return (salary_from + salary_to) / 2
    if salary_from is not None:
        return salary_from * SALARY_FROM_FACTOR
    if salary_to is not None:
        return salary_to * SALARY_TO_FACTOR
    return None

def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary.get('currency') != 'RUR':
        return None
    return predict_salary(
        salary.get('from'),
        salary.get('to')
    )

def predict_rub_salary_sj(vacancy):
    if vacancy.get('currency') != 'rub':
        return None
    return predict_salary(
        vacancy.get('payment_from'),
        vacancy.get('payment_to')
    )

def get_hh_statistics(languages):
    statistics = {}
    request_count = 0

    for language in languages:
        salaries = []
        vacancies_found = 0
        page = 0

        while True:
            params = {
                'text': language,
                'area': HH_MOSCOW_AREA,
                'period': HH_SEARCH_PERIOD_DAYS,
                'page': page
            }

            response = requests.get(HH_URL, headers=HH_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

            request_count += 1
            if request_count % HH_REQUESTS_BEFORE_SLEEP == 0:
                time.sleep(HH_SLEEP_SECONDS)

            if page == 0:
                vacancies_found = data['found']
                pages = data['pages']

            for vacancy in data['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    salaries.append(salary)

            page += 1
            if page >= pages:
                break

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': len(salaries),
            'average_salary': int(sum(salaries) / len(salaries)) if salaries else 0
        }

    return statistics

def get_sj_statistics(languages):
    statistics = {}
    request_count = 0

    for language in languages:
        salaries = []
        vacancies_found = 0
        page = 0

        while True:
            params = {
                'keywords': language,
                'town': SJ_MOSCOW_TOWN,
                'count': SJ_PAGE_SIZE,
                'page': page
            }

            response = requests.get(SJ_URL, headers=SJ_HEADERS, params=params)
            response.raise_for_status()
            data = response.json()

            request_count += 1
            if request_count % SJ_REQUESTS_BEFORE_SLEEP == 0:
                time.sleep(SJ_SLEEP_SECONDS)

            if page == 0:
                vacancies_found = data['total']

            for vacancy in data['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    salaries.append(salary)

            if not data['more']:
                break

            page += 1

        statistics[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': len(salaries),
            'average_salary': int(sum(salaries) / len(salaries)) if salaries else 0
        }

    return statistics

def print_table(statistics, title):
    table_data = [
        ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    ]

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
    languages = ['Python', 'Java', 'Ruby', 'PHP', 'C++', 'CSS', 'C#', '1C', 'C']

    hh_stats = get_hh_statistics(languages)
    sj_stats = get_sj_statistics(languages)

    print_table(hh_stats, 'HH.ru')
    print()
    print_table(sj_stats, 'SuperJob')