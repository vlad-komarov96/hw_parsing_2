from bs4 import BeautifulSoup as bs
import requests
import json
import re
import pandas as pd
from google.colab import files
from pprint import pprint
from pprint import pprint
import time

"""## задаем headers"""

headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}

"""## функция для сбора"""

def hh(main_link, search_str, n_str):
    #n_str - кол-во просматриваемых страниц
    html = requests.get(main_link+'/search/vacancy?clusters=true&enable_snippets=true&text='+search_str+'&showClusters=true',headers=headers).text
    parsed_html = bs(html,'lxml')

    jobs = []
    for i in range(n_str):
        jobs_block = parsed_html.find('div',{'class':'vacancy-serp'})
        jobs_list = jobs_block.findChildren(recursive=False)
        for job in jobs_list:
            job_data={}
            req=job.find('span',{'class':'g-user-content'})
            if req!=None:
                main_info = req.findChild()
                job_name = main_info.getText()
                job_link = main_info['href']
                salary = job.find('div',{'class':'vacancy-serp-item__compensation'})
                if not salary:
                    salary_min=0
                    salary_max=0
                else:
                    salary=salary.getText().replace(u'\xa0', u' ')
                    salaries=salary.split('-')
                    salary_min=salaries[0]
                    if len(salaries)>1:
                        salary_max=salaries[1]
                    else:
                        salary_max=''
                job_data['name'] = job_name
                job_data['salary_min'] = salary_min
                job_data['salary_max'] = salary_max
                job_data['link'] = job_link
                job_data['site'] = main_link
                jobs.append(job_data)
        time.sleep(1)
        next_btn_block=parsed_html.find('a',{'class':'bloko-button HH-Pager-Controls-Next HH-Pager-Control'})
        next_btn_link=next_btn_block['href']
        html = requests.get(main_link+next_btn_link,headers=headers).text
        parsed_html = bs(html,'lxml')
    #раскоментить если хотим еще увидеть что нашли
    #pprint(jobs)
    return jobs

"""# HH.RU"""

hunt=hh('https://hh.ru','Python',4)

"""## Преобразуем dataFrame и просмтариваем"""

with open('hunter.json','w') as ht:
  json.dump(hunt,ht)
pd.read_json('hunter.json')

"""## superjob.ru
"""

def parser_superjob(vacancy):
    vacancy_date = []
    
    params = {
        'keywords': vacancy, 
        'profession_only': '1',
        'geo[c][0]': '15', 
        'geo[c][1]': '1', 
        'geo[c][2]': '9', 
        'page': ''
    }
    
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    
    link = 'https://www.superjob.ru/vacancy/search/'
       
    html = requests.get(link, params=params, headers=headers)
    
    if html.ok:
        parsed_html = bs(html.text,'lxml')
    
        page_block = parsed_html.find('a', {'class': 'f-test-button-1'})
    if not page_block:
        last_page = 1
    else:
        page_block = page_block.findParent()
        last_page = int(page_block.find_all('a')[-2].getText())
    
    for page in range(0, last_page + 1):
        params['page'] = page
        html = requests.get(link, params=params, headers=headers)
        
        if html.ok:
            parsed_html = bs(html.text,'html.parser')
            vacancy_items = parsed_html.find_all('div', {'class': 'f-test-vacancy-item'})
                        
            for item in vacancy_items:
                vacancy_date.append(parser_item_superjob(item))
                
    return vacancy_date

def parser_item_superjob(item):

    vacancy_date = {}
    
    # vacancy_name
    vacancy_name = item.find_all('a')
    if len(vacancy_name) > 1:
        vacancy_name = vacancy_name[-2].getText()
    else:
        vacancy_name = vacancy_name[0].getText()
    vacancy_date['vacancy_name'] = vacancy_name
    
      
    #salary
    salary = item.find('span', {'class': 'f-test-text-company-item-salary'}).findChildren()
    if not salary:
        salary_min = None
        salary_max = None
        salary_currency = None
    else:
        salary_currency = salary[-1].getText()
        is_check_sarary = item.find('span', {'class': 'f-test-text-company-item-salary'}).getText().replace(u'\xa0', u' ').split(' ', 1)[0]
        if is_check_sarary == 'до' or len(salary) == 2:
            salary_min = None
            salary_max = int(salary[0].getText().replace(u'\xa0', u''))
        elif is_check_sarary == 'от':
            salary_min = int(salary[0].getText().replace(u'\xa0', u''))
            salary_max = None
        else:
            salary_min = int(salary[0].getText().replace(u'\xa0', u''))
            salary_max = int(salary[2].getText().replace(u'\xa0', u''))           
        
    vacancy_date['salary_min'] = salary_min
    vacancy_date['salary_max'] = salary_max
    vacancy_date['salary_currency'] = salary_currency
    
    
    # link
    vacancy_link = item.find_all('a')
    
    if len(vacancy_link) > 1:
        vacancy_link = vacancy_link[-2]['href']
    else:
        vacancy_link = vacancy_link[0]['href']
    
    vacancy_date['vacancy_link'] = f'https://www.superjob.ru{vacancy_link }'
    
    # site
    vacancy_date['site'] = 'www.superjob.ru'
    return vacancy_date

"""## Преобразуем dataFrame и просмтариваем"""

vacancy = 'Python'
df = parser_superjob(vacancy)
with open('jobs.json','w') as t:
  json.dump(df,t)
pd.read_json('jobs.json')
