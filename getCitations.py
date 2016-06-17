"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

import urllib
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import random
import time
import re
import csv
import urllib.request


'''
Get citation data DED SO SAD :'(
'''
def getCite(author, paper):
    base = "https://scholar.google.com/scholar?q="
    nauthor = author.replace(" ", "+")
    npaper = paper.replace(" ", "+")
    url = base + nauthor + "+" + npaper
    get = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(get).read()
    soup = BeautifulSoup(html, 'lxml')
    allTitles = soup.findAll('h3', 'gs_rt')
    if len(allTitles) == 0:
        return 0
    titles = []
    for b in allTitles:
        try:
            titles.append(b.find('a').get_text())
        except AttributeError:
            return 0
    title = process.extract(paper, titles, limit = 1)[0][0]
    print(paper)
    print(title)
    number = titles.index(title)
    allCites = soup.findAll(lambda tag: tag.name == 'div' and
                                   tag.get('class') == ['gs_fl']) #fixed it god damn finally jeez
    citations = []
    for b in allCites:
        cited = b.find('a').get_text()
        try:
            citenum = int(re.search(r'\d+', cited).group())
        except AttributeError:
            return 0
        citations.append(citenum)
    return citations[number]

def init():
    peoplef = csv.reader(
        open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
    grantf = csv.reader(
        open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
    publicationf = csv.reader(
        open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))
    auth = dict()
    people = dict()
    grantinfo = [grantf, 'gra', 'val-s']
    pubinfo = [publicationf, 'pub', 'Value']
    for x in [grantinfo, pubinfo]:
        for line in x[0]:
            if line[2] not in auth:
                #line2 is work title
                personid = line[0][re.search('per', line[0]).end():len(line[0])]
                workid = line[1][re.search(x[1], line[1]).end():len(line[1])]
                auth[line[2]] = [personid, workid]
                #formatted auth[title] = [id, grant id]
    for x in peoplef:
        personid = x[0][re.search('per', x[0]).end():len(x[0])]
        people[personid] = x[1]
        #dictionary people --- person id: person name
    for (key, val) in auth.items():
        auth[key] = people[val[0]]
    return auth

def getAllCites(auth):
    y = 0
    citations = dict()
    for (title, person) in auth.items():
        try:
            name = person[0]
            grantid = person[1]
            num = getCite(name, title)
            citations[grantid] = num
            print(num)
            wait = [.5, 1, 2, 2.1, .9, 1.5, 3, 2.6, 3.4, .7, 5]
            if y % 50 == 0:
                time.sleep(5)
            elif y % 100 == 0:
                time.sleep(15)
            else:
                time.sleep(random.choice(wait))
            y += 1
        except urllib.error.HTTPError:
            writer = csv.writer(open('citations.csv', 'w'))
            for key, value in citations.items():
                writer.writerow([key, value])

auth = init()
getAllCites(auth)