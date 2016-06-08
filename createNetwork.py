"""
author: Anne Driscoll
contact: amd112@duke.edu
date: May 2016
"""

import csv
import time
import networkx as nx
import itertools
import matplotlib.pyplot as plt #needed for plotting
import plotly.plotly as py
import plotly.graph_objs as go
import urllib
from tkinter import *
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import heapq
import requests
py.sign_in('amd112', '0eso7gihvt')

net = nx.Graph()
fieldnet = nx.Graph()

'''
Create a storage system for publications and grants
'''
class Work:
    def __init__(self, id, name, type, year):
        self.id = id
        self.name = name
        self.type = type
        self.year = year
        self.citations = 0

'''
Loops through position info to create Nodes with id, name, field, school, position type info.
'''
def createNodes(people):
    net.clear()
    for line in people:
        #specifically meant to loop through format we've been given. No wiggle room
        id = line[0][re.search('per', line[0]).end():len(line[0])]
        name = line[1]
        field = line[5]
        school = line[7]
        position = line[2][re.search('#', line[2]).end():len(line[2])]
        net.add_node(id, name = name, field = field, school = school, position = position, work = [])

def trying(author, paper):
    base = "https://scholar.google.com/scholar?q="
    nauthor = author.replace(" ", "+")
    npaper = paper.replace(" ", "+")
    url = base + nauthor + "+" + npaper
    html = requests.get(url)

'''
Get citation data FUCK I THINK IT WORKS HOLY SHITTTT
'''
def getCite(author, paper):
    base = "https://scholar.google.com/scholar?q="
    nauthor = author.replace(" ", "+")
    npaper = paper.replace(" ", "+")
    url = base + nauthor + "+" + npaper
    #get = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    #html = urllib.request.urlopen(get).read()
    html = requests.get(url)
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
    number = titles.index(title)
    allCites = soup.findAll(lambda tag: tag.name == 'div' and
                                   tag.get('class') == ['gs_fl']) #fixed it god damn finally jeez
    citations = []
    for b in allCites:
        cited = b.find('a').get_text()
        try:
            citenum = int(re.search(r'\d+', cited).group())
            print(cited)
        except AttributeError:
            return 0
        citations.append(citenum)
    return citations[number]

'''
Loops through grant and publication data to add the correct data to the correct people and create map of who
worked on what publication
solve publication type
'''
def addWork(grant, publication, mapWork):
    grantinfo = [grant, 'gra', 'val-s']
    pubinfo = [publication, 'pub', 'Value']

    for x in [grantinfo, pubinfo]:
        for line in x[0]:
            id = line[0][re.search('per', line[0]).end():len(line[0])]
            name = line[2]
            workid = line[1][re.search(x[1], line[1]).end():len(line[1])]
            year = line[3][re.search(x[2], line[3]).end():re.search(x[2], line[3]).end() + 4]
            try:
                type = line[4][re.search('extension#', line[4]).end():len(line[4])] #type has different formats
            except AttributeError:
                try:
                    type = line[4][re.search('bibo/', line[4]).end():len(line[4])]
                except AttributeError:
                    type = line[4][re.search('core#', line[4]).end():len(line[4])]
            curr = Work(workid, name, type, year)
            net.node[id]['work'].append(curr)
            #time.sleep(1)

            if mapWork.__contains__(workid):  # creating a dict {grant id: [authors]} to loop through later
                if not mapWork[workid].__contains__(id):
                    mapWork[workid].append(id)
            else:
                mapWork[workid] = [id]

'''
Loops through map created in addWork and creates edges.
'''
def findEdges(mapWork):
    for pid, ids in mapWork.items(): #for every key in the map
        for i, j in itertools.combinations(ids, 2): #go through every combo of values
            if i != j:
                field1 = net.node[i]['field']
                field2 = net.node[j]['field']
                if net.has_edge(i, j): #if they are already connected
                    net[i][j]['work'].append(pid)  #add the grant to their edge
                    if (field1 is not field2): #if different fields add to field net to count how many collabs
                        if fieldnet.has_edge(field1, field2):
                            fieldnet[field1][field2]['weight'] += 1
                        else: #if the fields aren't already connected, connect them
                            fieldnet.add_edge(field1, field2, weight = 1)
                else: #if there is no edge between them
                    field = (field1 == field2)
                    school = (net.node[i]['school'] == net.node[j]['school'])
                    net.add_edge(i, j, work = [], samefield = field, sameschool = school)
                    if (field1 is not field2):
                        if fieldnet.has_edge(field1, field2):
                            fieldnet[field1][field2]['weight'] += 1
                        else:
                            fieldnet.add_edge(field1, field2, weight = 1)


'''
Clears lists for export to graphml.
'''
def export():
    for this in net.nodes():
        net.node[this]['work'] = len(net.node[this]['work']) #make publications just be # of pubs
    for this, that in net.edges():
        net.edge[this][that]['work'] = len(net.edge[this][that]['work'])
    nx.write_graphml(net, "hospital.graphml") #export`

'''
Remove nodes that have no edges at all.
'''
def removeBlanks():
    deg = net.degree()
    to_remove = [n for n in deg if deg[n] == 0]
    net.remove_nodes_from(to_remove)

'''
Calculate the collaboration coefficient of each node and saves in map (name: number)
NEED TO FILL IN CALCULATION STILL
'''
def calcCollab(map):
    for node in net.nodes():
        curr = net.node[node]
        '''
        tot = 0
        for neighbor in net[node]:
            neigh = net.node[neighbor]
            num = 0
            for paper in net.edge[node][neighbor]['work']:
                num += 1
            fieldweight = fieldnet[neigh['field']][curr['field']]['weight']
            num = (num * time(node, neighbor))
            tot += num
        '''
        map[curr['name']] = percCollab(node) * departments(node)
        net.node[node]['weight'] = percCollab(node) * departments(node) #also save in the network (for graphing)

def departments(node): #returns number of fields the person has collaborated with
    deps = []
    for neighbor in net[node]:
        field = net.node[neighbor]['field']
        if not deps.__contains__(field):
            deps.append(field)
    return len(deps)

def percCollab(node): #returns percentage of publications that are collaborative
    collabPapers = []
    for neighbor in net[node]:
        for work in net.edge[node][neighbor]['work']:
           if not collabPapers.__contains__(work):
               collabPapers.append(work) #can't just sum lengths because may work on same paper w/ multiple people
    return len(collabPapers)/len(net.node[node]['work'])

def time(node, neighbor): #returns number of years working together, 0 if no work, 1 if 1 year or less
    years = []
    edge = net.edge[node][neighbor]['work']
    if len(edge) == 0:
        return 0
    if len(edge) == 1:
        return 1
    for work in net.edge[node][neighbor]['work']:
        ids = [x.id for x in net.node[node]['work']]
        index = ids.index(work)
        years.append(int(net.node[node]['work'][index].year)) #not saved as work type, just an id number
    if len(years) <= 1:
        return 1
    lapsed = max(years) - min(years)
    if lapsed == 0:
        return 1
    else:
        return lapsed

'''
Outputs list of most successful people and saves barchart
'''
def bestHist(weight, nametop, namebot):
    X = 5 #top how many and bottom how many
    py.sign_in('amd112', '0eso7gihvt')
    big = heapq.nlargest(X, weight, key = weight.get)
    data = [go.Bar(x = big, y = [weight[x] for x in big])]
    py.image.save_as(data, filename = nametop + ".png")
    small = heapq.nsmallest(X, weight, key = weight.get)
    small.reverse()
    data2 = [go.Bar(x = small, y = [weight[x] for x in small])]
    py.image.save_as(data2, filename = namebot + ".png")

'''

'''
def scatterAll(collab, productive, name):
    data = [go.Scatter(x = [collab[x] for x in collab], y = [productive[x] for x in productive], mode = 'markers')]
    py.image.save_as(data, name)

'''
Adjusts the fieldnet network to behave as an index where low numbers are better
'''
def networkSep():
    yo = 2

'''
Calculate productivity of each person (just returns h-index)
'''
def calcH(map):
    for node in net.nodes():
        nodecite = [x.citations for x in net.node[node]['work']]
        nodecite.sort(reverse = True)
        for x in nodecite:
            if x < nodecite.index(x) + 1:
                map[net.node[node]['name']] = nodecite.index(x)
                break

def calci10(map):
    for node in net.nodes():
        nodecite = [x.citations for x in net.node[node]['work']]
        num = 0
        for x in nodecite:
            if x > 10:
                num += 1
        map[net.node[node]['name']] = num

def calcG(map):
    for node in net.nodes():
        nodecite = [x.citations for x in net.node[node]['work']]
        nodecite.sort(reverse=True)
        tot = 0
        for x in nodecite:
            tot += x
            if tot < ((nodecite.index(x) + 1) ** 2):
                map[net.node[node]['name']] = nodecite.index(x)
                break

def calcHi(map, mapWork):
    for node in net.nodes():
        nodecite = [x.citations for x in net.node[node]['work']]
        nodework = [x.id for x in net.node[node]['work']]
        nodecite.sort(reverse=True)
        h = 0
        nums = []
        for x in nodecite:
            if x < nodecite.index(x) + 1:
                h = nodecite.index(x)
                break
        for x in nodework:
            nums.append(len(mapWork[id]))
        authors = sum(nums) / float(len(nums))
        map[net.node[node]['name']] = h/authors




'''
MAIN
'''
peoplef = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
grantf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
publicationf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))
mapWork = dict()
weights = dict()
productive = dict()

createNodes(peoplef)
addWork(grantf, publicationf, mapWork)
findEdges(mapWork)
removeBlanks()
calcCollab(weights)
calcH(productive)
bestHist(weights,'top', 'bottom')
#scatterAll(weights, productive, 'scatter')