import urllib
import requests
from bs4 import BeautifulSoup
import os
import time

def secrets():
    '''Returns a dict with keys canvas_user and canvas_pass with the corrosponding string as value
    '''
    secrets = dict()
    with open(r'C:\Users\<user>\secrets.txt') as file:
        lines = file.readlines()
    for i in lines:
        i = i.strip()
        s = i.split(': ')
        secrets[s[0]] = secrets.get(s[0], s[1])
    return secrets

class Registration:
    def __init__(self, term):
        self.secrets = secrets()
        self.s = requests.Session()
        self.r = self.s.get('https://myportal.fhda.edu/')
        self.term = term

    
    def login(self):
        self.r = self.s.post(self.r.url, data={'j_username': self.secrets['canvas_user'],'j_password': self.secrets['canvas_pass'], '_eventId_proceed':''})
        if self.r.status_code != 200:
            print('error logging in')

    def drop_and_register(self, add, drop=None):
        #SAML SSO
        params = {'relayState' : '%2Fc%2Fauth%2FSSB%3Fpkg%3Dhttps%3A%2F%2Fssb-prod.ec.fhda.edu%2FPROD%2Ffhda_uportal.P_DeepLink_Post%3Fp_page%3Dbwskfreg.P_AltPin%26p_payload%3De30%3D'}
        self.r = self.s.get('https://ssb-prod.ec.fhda.edu/ssomanager/saml/login', params=params)

        if 'https://ssoshib.fhda.edu/idp/profile/SAML2/Redirect/SSO' in self.r.url:
            self.login()
        
        self.parse_nojs()
        self.parse_nojs_slash()
        #self.parse_deeplink()

        self.r = self.s.post('https://ssb-prod.ec.fhda.edu/PROD/bwskfreg.P_AltPin', data={'term_in': self.term})
        if self.r.status_code != 200:
            print('error getting the registration page')
        
        payload = self.class_payload()
        payload = self.add_classes([add], payload)
        if drop:
            payload = self.drop_class(drop, payload)

        self.r = self.s.post('https://ssb-prod.ec.fhda.edu/PROD/bwckcoms.P_Regs', data=payload)

    def drop_class(self, crn, payload):
        for i, j in enumerate(payload): #payload has (key, value) tuples
            k, l = j
            if k == 'CRN_IN' and l == crn:
                payload[i-2] = ('RSTS_IN', 'DW') #dw for drop web
        return payload

    def parse_nojs(self): #no js for these links
        soup = BeautifulSoup(self.r.text, 'html.parser')

        url = soup.find('form').get('action')
        payload = dict()
        data = zip([i.get('name') for i in soup.find_all('input', type='hidden')], [i.get('value') for i in soup.find_all('input', type='hidden')])
        for i, j in data:
            payload[i] = j
        self.r = self.s.post(url, data=payload)
        if self.r.status_code != 200:
            print('error in parse_nojs')
    
    def parse_nojs_slash(self): #has to parse to utf 8 for url to work
        soup = BeautifulSoup(self.r.text, 'html.parser')

        url = soup.find('form').get('action')
        payload = dict()
        data = zip([i.get('name') for i in soup.find_all('input', type='hidden')], [i.get('value') for i in soup.find_all('input', type='hidden')])
        for i, j in data:
            payload[i] = j
        self.r = self.s.post(url, data=payload, allow_redirects=False)
        self.r = self.s.post(urllib.parse.unquote(self.r.headers['Location']), allow_redirects=False)
        
        if self.r.status_code != 302: #response for redirect
            print('error in parse_nojs_slash')
    
    def parse_deeplink(self):
        self.r = self.s.post(self.r.url)
        soup = BeautifulSoup(self.r.text, 'html.parser')
        soup = soup.find('form', {'id':'deeplink'})['action']
        
        url = urllib.parse.urljoin('https://ssb-prod.ec.fhda.edu/PROD/', soup)
        self.r = self.s.post(url)
    
    def class_payload(self):
        soup = BeautifulSoup(self.r.text, 'html.parser')
        return [(i.get('name'), i.get('value')) for i in soup.find_all('input', type='hidden')] #take the filler values that we need to post

    def add_classes(self, crns, payload): #append the 10 crn add values
        soup = BeautifulSoup(self.r.text, 'html.parser')
        input = list()
        for i in range(10):
            if i < len(crns):
                input.append(('CRN_IN', crns[i]))
            else:
                input.append(('CRN_IN', None))
        payload += input

        payload += [(i.get('name'), i.get('value')) for i in soup.find_all('input', type='submit', value="Submit Changes")]
        return payload

    def document(self, filename='registration'):
        html = self.r.text
        soup = BeautifulSoup(html, 'html.parser')
        files = os.listdir()
        count = 0
        for i in files:
            if filename in i:
                count += 1
        with open(f'{filename}{count}.html', 'w') as f:
            f.write(soup.prettify())

def parse_term(year, quarter, school='deanza'): #turn term into term code
    school = 1 if school.lower() == 'foothill' else 2
    if len(quarter) > 1:
        quarter = {'winter':3, 'spring':4, 'summer':11, 'fall':12}[quarter.lower()]
    else:
        quarter = {'w':3, 's':4, 'm':11, 'f':12}[quarter.lower()]
    year = int(year)
    return year * 100 + quarter * 10 + school

class colors:
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"
    reset = '\033[0m'
