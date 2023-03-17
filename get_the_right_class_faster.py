import requests
from bs4 import BeautifulSoup
import urllib
from datetime import datetime
import time
from tqdm.auto import tqdm

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

secrets = dict()
with open(r'C:\Users\micha\secrets.txt') as file:
    lines = file.readlines()
for i in lines:
    i = i.strip()
    s = i.split(': ')
    secrets[s[0]] = secrets.get(s[0], s[1])

def termnum(year, quarter, school='deanza'):
    school = 1 if school.lower() == 'foothill' else 2
    if len(quarter) > 1:
        quarter = {'winter':3, 'spring':4, 'summer':11, 'fall':12}[quarter.lower()]
    else:
        quarter = {'w':3, 's':4, 'm':11, 'f':12}[quarter.lower()]
    year = int(year)
    return year * 100 + quarter * 10 + school

term = termnum(input('year: '), input('quarter: '))
datetime_object = datetime.strptime(input('Paste registration date mm/dd/yyyy hr:min(pm/am):'), '%m/%d/%Y %I:%M%p')
crns = list()
_ = int(input('how many crns are you putting: '))
if 10 < _:
    print('program doesn\'t support using more crns than selection boxes (10)')
for i in range(_):
    crns.append(input(f'crn {i+1}: '))
 
# # 10 second timer
# authenticate 10 seconds before class selection.

leeway = 10
total = (datetime_object - datetime.now()).total_seconds() - leeway
remain = total
print('waiting for login')
with tqdm(total=100) as pbar:
    while(remain > 0):
        time.sleep(2)
        remain = (datetime_object - datetime.now()).total_seconds() - leeway
        pbar.n = round((1-remain/total)*100, 3)
        pbar.refresh()
        pbar.set_postfix({'time remaining': f'{remain}s'})
 
# # Authenticate User

s = requests.Session()
r = s.get('https://myportal.fhda.edu/')
r = s.post(r.url, data={'j_username': secrets['canvas_user'],'j_password': secrets['canvas_pass'], '_eventId_proceed':''})

params = {'relayState' : '%2Fc%2Fauth%2FSSB%3Fpkg%3Dhttps%3A%2F%2Fssb-prod.ec.fhda.edu%2FPROD%2Ffhda_uportal.P_DeepLink_Post%3Fp_page%3Dbwskfreg.P_AltPin%26p_payload%3De30%3D'}
r = s.get('https://ssb-prod.ec.fhda.edu/ssomanager/saml/login', params=params)

if 'https://ssoshib.fhda.edu/idp/profile/SAML2/Redirect/SSO' in r.url:
    r = s.post(r.url, data={'j_username': secrets['canvas_user'],'j_password': secrets['canvas_pass'], '_eventId_proceed':''})


soup = BeautifulSoup(r.text, 'html.parser')

url = soup.find('form').get('action')
payload = dict()
data = zip([i.get('name') for i in soup.find_all('input', type='hidden')], [i.get('value') for i in soup.find_all('input', type='hidden')])
for i, j in data:
    payload[i] = j
r = s.post(url, data=payload)

soup = BeautifulSoup(r.text, 'html.parser')

url = soup.find('form').get('action')
payload = dict()
data = zip([i.get('name') for i in soup.find_all('input', type='hidden')], [i.get('value') for i in soup.find_all('input', type='hidden')])
for i, j in data:
    payload[i] = j
r = s.post(url, data=payload, allow_redirects=False)
r = s.post(urllib.parse.unquote(r.headers['Location']), allow_redirects=False)
 
# # Wait Remaining
# Wait until exact class selection time.

total = (datetime_object - datetime.now()).total_seconds()
remain = total
print('waiting for registration')
with tqdm(total=100) as pbar:
    while(remain > 0):
        time.sleep(0.03)
        remain = (datetime_object - datetime.now()).total_seconds()
        pbar.n = round((1-remain/total)*100, 3)
        pbar.refresh()
        pbar.set_postfix({'time remaining': f'{remain}s'})
#wait an extra 50 ms to make sure server can update
time.sleep(0.05)
 
# # Register

r = s.post('https://ssb-prod.ec.fhda.edu/PROD/bwskfreg.P_AltPin', data={'term_in': term})

soup = BeautifulSoup(r.text, 'html.parser')
payload = [(i.get('name'), i.get('value')) for i in soup.find_all('input', type='hidden')]

input = list()
for i in range(10):
    if i < len(crns):
        input.append(('CRN_IN', crns[i]))
    else:
        input.append(('CRN_IN', None))
payload += input

payload += [(i.get('name'), i.get('value')) for i in soup.find_all('input', type='submit', value="Submit Changes")]

r = s.post('https://ssb-prod.ec.fhda.edu/PROD/bwckcoms.P_Regs', data=payload)

soup = BeautifulSoup(r.text, 'html.parser')
with open('test.html', "w") as a:
    a.write(soup.prettify())
#import subprocess
#subprocess.Popen('test.html')

 
# # Contingency Using Selenium
# Once program has tried to enter the CRN's using requests it will try again ASAP using selenium to make sure.

d = webdriver.Chrome('chromedriver.exe')
d.get('https://myportal.fhda.edu/')
e = d.find_element(By.XPATH, '//*[@id="j_username"]')
e.send_keys(secrets['canvas_user'])
e = d.find_element(By.XPATH, '//*[@id="j_password"]')
e.send_keys(secrets['canvas_pass'])
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="btn-eventId-proceed"]')))
e.click()
#e = d.find_element(By.XPATH, '//*[@id="btn-eventId-proceed"]')
#e.click()

#e = d.find_element(By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[1]/ul/li[3]')
#e.click()
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[1]/ul/li[3]')))
e.click()
#e = d.find_element(By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[2]/div[2]/div/div[3]/div[3]/div/div/div[27]/div[1]')
#e.click()
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[2]/div[2]/div/div[3]/div[3]/div/div/div[27]/div[1]')))
e.click()
#e = d.find_element(By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div[3]/a')
#e.click()
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="react-portal-root"]/div/div[1]/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div[3]/a')))
e.click()
d.switch_to.window(d.window_handles[1])
e = d.find_element(By.XPATH, '//*[@id="j_username"]')
e.send_keys(secrets['canvas_user'])
e = d.find_element(By.XPATH, '//*[@id="j_password"]')
e.send_keys(secrets['canvas_pass'])
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="btn-eventId-proceed"]')))
e.click()
#e = d.find_element(By.XPATH, '//*[@id="term_id"]')
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="term_id"]')))
e.click()
c = None
s = Select(e)
s.select_by_value(f'{term}')

e = d.find_element(By.XPATH, '/html/body/div[3]/form/input')
e.click()
boxes = ['//*[@id="crn_id1"]'] * 10
for idx in range(1,len(boxes)+1):
    boxes[idx-1] = boxes[idx-1][:-3] + str(idx) + '"]'
e = WebDriverWait(d, 30).until(EC.presence_of_element_located((By.XPATH, boxes[0])))
for box, crn in zip(boxes, crns):
    e = d.find_element(By.XPATH, box)
    e.send_keys(crn)
e = d.find_element(By.XPATH, '/html/body/div[3]/form/input[19]')
e.click()




