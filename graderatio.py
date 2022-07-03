#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from os.path import exists
import argparse
from datadownload import attemptdownload

def run(args):
    college = args.college

    if exists(f'data{college[0]}.csv'):
        df = pd.read_csv(f'data{college[0]}.csv', index_col='Unnamed: 0')
    else:
        attemptdownload(college)
        df = pd.read_csv(f'data{college[0]}.csv', index_col='Unnamed: 0')

    sub = args.subject.upper()
    code = args.class_code.upper()
    year = args.year
    if len(year) < 3:
        year = '20' + year
    quarter = args.quarter.lower()
    if len(quarter) > 1:
        quarter = {'winter':'W', 'spring':'S', 'summer':'M', 'fall':'F'}[quarter]
    else:
        quarter = quarter.upper()
    quarter += year

    def group_function(x, indexer=['A','B','C','D','F','W']):
        d = dict()
        d['YEAR'] = x['YEAR'].values
        
        for i in indexer:
            d[i] = x[i].sum()
        return pd.Series(d)

    tmp = df[df['SUBJECT']==sub]
    if not args.search_department:
        tmp = df[df['NUMBER']==code]
    indexes = ['A','B','C','D','F','W']
    if args.drop_W:
        indexes.remove('W')
    tmp = tmp.groupby(['INSTRUCTOR']).apply(group_function, indexer=indexes)

    if tmp.shape[0] == 0:
        print('No data for instructors, try searching department')
        return
    tmp['T'] = tmp[indexes].sum(axis=1)
    tmp['R'] = tmp['A']/tmp['T']
    tmp['R'] = tmp['R'].fillna(0)

    if args.history:
        tmp = tmp.sort_values(by='R', ascending=False)
        print(tmp)
        return


    r = requests.get(f'https://www.deanza.edu/schedule/listings.html?dept={sub}&t={quarter}')

    soup = BeautifulSoup(r.text, 'html.parser')
    soup = soup.find('table')
    soup = soup.find_all('tr')
    def determine(x, course):
        for i in x.find_all('td'):
            if i.text.lower() == course.lower():
                return True
        return False
    shortcode = code[1:].lstrip('0')
    shortcode = f'{sub} {shortcode}'
    print(shortcode)
    soup = [i for i in soup if determine(i, shortcode)]
    teach_list = [i.find_all('td')[7].text.lower() for i in soup if i.find_all('td')[3].text == 'Open' or i.find_all('td')[3].text == 'Full' or i.find_all('td')[3].text == 'WL']


    teachers = set(map(lambda x: ', '.join(reversed(x.split(' '))) if not ', ' in x else x, teach_list))

    print('Active Teachers:')
    for i in teachers:
        print(i)


    x = lambda x : x in teachers or ', '.join(reversed(x.split(', '))) in teachers
    frame = tmp[list(map(x, map(str.lower, tmp.index)))]
    frame = frame.sort_values(by='R', ascending=False)
    print(frame)

    os.makedirs('ratios', exist_ok=True)
    frame.to_csv(path_or_buf=os.path.join(os.getcwd(), 'ratios', f'{shortcode}.csv'))


if __name__ == '__main__':
    print('''                                 ,----,                                                                                 
                               ,/   .`|                                                                                 
    ,---,.                   ,`   .'  :                                                                                 
  ,'  .' |                 ;    ;     /                                                     .--.,                       
,---.'   |        ,----, .'___,/    ,'    __  ,-.                     ,---,               ,--.'  \              __  ,-. 
|   |   .'      .'   .`| |    :     |   ,' ,'/ /|                 ,-+-. /  |   .--.--.    |  | /\/            ,' ,'/ /| 
:   :  |-,   .'   .'  .' ;    |.';  ;   '  | |' |    ,--.--.     ,--.'|'   |  /  /    '   :  : :      ,---.   '  | |' | 
:   |  ;/| ,---, '   ./  `----'  |  |   |  |   ,'   /       \   |   |  ,"' | |  :  /`./   :  | |-,   /     \  |  |   ,' 
|   :   .' ;   | .'  /       '   :  ;   '  :  /    .--.  .-. |  |   | /  | | |  :  ;_     |  : :/|  /    /  | '  :  /   
|   |  |-, `---' /  ;--,     |   |  '   |  | '      \__\/: . .  |   | |  | |  \  \    `.  |  |  .' .    ' / | |  | '    
'   :  ;/|   /  /  / .`|     '   :  |   ;  : |      ," .--.; |  |   | |  |/    `----.   \ '  : '   '   ;   /| ;  : |    
|   |    \ ./__;     .'      ;   |.'    |  , ;     /  /  ,.  |  |   | |--'    /  /`--'  / |  | |   '   |  / | |  , ;    
|   :   .' ;   |  .'         '---'       ---'     ;  :   .'   \ |   |/       '--'.     /  |  : \   |   :    |  ---'     
|   | ,'   `---'                                  |  ,     .-./ '---'          `--'---'   |  |,'    \   \  /            
`----'                                             `--`---'                               `--'       `----'             
                                                                                                                        ''')
    parser = argparse.ArgumentParser(description='Calculates the ratio of A\'s to other grades given.')
    parser.add_argument('college', type=str, help='deanza or foothill')
    parser.add_argument('subject', type=str, help='i.e phys')
    parser.add_argument('class_code', type=str, help='i.e d004a')
    parser.add_argument('year', type=str, help='school year')
    parser.add_argument('quarter', type=str, help='w,s,m,f : winter, spring, summer, fall')
    parser.add_argument('-dw', '--drop_W', action='store_true', default=False, help='Don\'t count withdrawals')
    parser.add_argument('-sd', '--search_department', action='store_true', default=False, help='search the whole department for more data')
    parser.add_argument('-hist', '--history', action='store_true', default=False, help='Shows a history of the department while ignoring the active teachers')
    args = parser.parse_args()
    args.college = args.college.lower()
    assert args.college == 'deanza' or args.college == 'foothill', 'please put the right college'
    assert args.year.isnumeric(), 'year is a number'

    run(args)
