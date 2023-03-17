import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from utils import Registration
from utils import colors

print(f'''{colors.yellow}                                 ,----,                                                                                 
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
                                                                                                                        {colors.reset}''')














def termnum(year, quarter, school='deanza'):
    school = 1 if school.lower() == 'foothill' else 2
    if len(quarter) > 1:
        quarter = {'winter':3, 'spring':4, 'summer':11, 'fall':12}[quarter.lower()]
    else:
        quarter = {'w':3, 's':4, 'm':11, 'f':12}[quarter.lower()]
    year = int(year)
    return year * 100 + quarter * 10 + school

term_code = termnum(input('year: '), input('quarter: '))
crn_count = int(input('How many crns would you like to add: '))
crns = list()
for i in range(crn_count):
    crns.append((input('department: ').strip(), input('crn to add: ').strip(), input('crn to drop: ').strip()))


data = {'termcode': term_code}
count = 0
print('Beginning waitlist bot...')
print('Iteration:')
while True:
    count += 1
    print(count, end='\r')
    r = requests.post('https://ssb-prod.ec.fhda.edu/PROD/fhda_opencourses.P_GetCourseList', data=data)

    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.findAll('table')
    headers = tables[0].findAll('tr')[1] #find row 1, row 0 is useless
    headers = [i.text for i in headers] #get text from td items
    while '\n' in headers:
        headers.remove('\n') #remove extra headers
    for i, j in enumerate(headers): #remove extra notes from headers
        if '(' in j:
            idx = j.index('(')
            headers[i] = j[:idx]

    depts = [i['dept'] for i in tables] #get all the departments
    d = dict() #add departments to dict for table access
    for j, i in enumerate(depts):
        d[i] = j

    temp_crns = list() #used to ignore the ones with open spots after
    for pack in crns:
        dept, crn, crn_to_drop = pack
        table = tables[d[dept.upper()]] #select table by dept
        rows = table.findAll('tr', {'class':'CourseRow'}) #process table rows
        frame = [[td.text for td in row.findAll('td')] for row in rows] #get td from each row in rows
        frame = pd.DataFrame(frame,columns=headers)

        try:
            temp = frame[frame['CRN'] == crn].iloc[0]
        except:
            print('no such crn')

        if int(temp['Waitlist SlotsAvailable']) > 0 or int(temp['Seats Available']) > 0:
            print(f'{colors.red}{crn} HAS SPACE. REGESTERING FOR THIS SPACE. DROPPING {crn_to_drop}{colors.reset}')
            account = Registration(term_code)
            account.login()
            account.drop_and_register(crn, crn_to_drop if crn_to_drop else None)
            account.document('waitlist')
            account.drop_and_register(crn_to_drop) #panic add. if adding the wait list class fails, join back!
            account.document('failsafe')
        else:
            temp_crns.append(pack)
    crns = temp_crns
    if len(crns) == 0:
        break
            
        
    time.sleep(5)
