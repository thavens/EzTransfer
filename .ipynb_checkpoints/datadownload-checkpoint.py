import requests
from bs4 import BeautifulSoup
import pandas
import os
from tqdm import tqdm as tq

def attemptdownload(college):
    soup = None
    save_file = None
    if college == 'deanza':
        r = requests.get('https://transfercamp.com/de-anza-college-grade-distribution-2/')
        soup = BeautifulSoup(r.text, 'html.parser')
        soup = soup.find('section', {'class':'elementor-section elementor-top-section elementor-element elementor-element-b1284a8 elementor-section-boxed elementor-section-height-default elementor-section-height-default'})
        save_file = 'datad.csv'
    elif college == 'foothill':
        r = requests.get('https://transfercamp.com/foothill-college-grade-distribution/')
        soup = BeautifulSoup(r.text, 'html.parser')
        soup = soup.find('section', {'class':'elementor-section elementor-top-section elementor-element elementor-element-574ba14 elementor-section-boxed elementor-section-height-default elementor-section-height-default'})
        save_file = 'dataf.csv'

    soup = soup.find_all('a')
    links_by_year = [i['href'] for i in soup]
    

    rs = [requests.get(i) for i in tq(links_by_year)]

    years = [i[i.rindex('-', 0, i.rindex('-'))+1:-1] for i in links_by_year]
    print('Data years retreived:')
    for i in years:
        print(i)
    print()

    arrays = list()
    for html in rs:
        soup = BeautifulSoup(html.text, 'html.parser')
        soup = soup.find('table')
        head = soup.find('thead')
        col_names = [i.text for i in head.find_all('th')]
        body = soup.find('tbody')
        rows = body.find_all('tr')
        arrays.append([[j.text for j in i.find_all('td')] for i in rows])
    array = list()
    for i in arrays:
        array += i

    df = pandas.DataFrame(array, columns=col_names)
    df = df.replace('', '0')
    df.name = 'data'

    df.to_csv(path_or_buf=os.path.join(os.getcwd(), save_file))








