"""
author: Anne Driscoll
contact: amd112@duke.edu
date: May 2016
"""

import csv
import networkx as nx
import itertools
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
import urllib
from tkinter import *
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import heapq
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
        self.citations = int
        self.pi = ""

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

'''
Get citation data
MAKE SURE IT WORKS/ DEAL WITH LATER
getCite('Grayson', "Microbiology")
'''
def getCite(author, paper):
    base = "https://scholar.google.com/scholar?q="
    nauthor = author.replace(" ", "+")
    npaper = paper.replace(" ", "+")
    url = base + nauthor + "+" + npaper
    print(url)
    get = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(get).read()
    soup = BeautifulSoup(html, 'lxml')
    allTitles = soup.findAll('h3', 'gs_rt')
    titles = []
    for b in allTitles:
        titles.append(b.find('a').get_text())
    title = process.extract(paper, titles, limit = 1)[0][0]
    print(titles)
    print(title)
    number = titles.index(title)
    print(number)

    #---------------------------
    allCites = soup.findAll(class_= 'gs_fl')
    citations = []
    for b in allCites:
        print(b)
        citenum = b.find('a').get_text()
        citations.append(citenum)
        print(citenum)
    #return citations[number]

'''
Loops through grant and publication data to add the correct data to the correct people and create map of who
worked on what publication
NEED TO SOLVE DOUBLE COUNTING PUBS AND GRANTS PROBLEM, PROBLEM WITH PUBLICATION TYPE
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
            if x == grantinfo:
                type = line[4][re.search('extension#', line[4]).end():len(line[4])]
            else:
                type = 'publication'

            curr = Work(workid, name, type, year)
            net.node[id]['work'].append(curr)

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
        tot = 0
        for neighbor in net[node]:
            neigh = net.node[neighbor]
            num = 0
            for paper in net.edge[node][neighbor]['work']:
                num += 1
            fieldweight = fieldnet[neigh['field']][curr['field']]['weight']
            num = (num * time(node, neighbor))
            tot += num
        map[curr['name']] = [tot * percCollab(node)]
        net.node[node]['weight'] = tot * percCollab(node) #also save in the network (for graphing)

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
def best(map):
    X = 5 #top how many and bottom how many
    big = heapq.nlargest(X, map, key = map.get)
    data = [go.Bar(x = big, y = [map[x] for x in big])]
    py.image.save_as(data, 'my_plot.png')
    small = heapq.nsmallest(X, map, key = map.get)
    small.reverse()
    data2 = [go.Bar(x = small, y = [map[x] for x in small])]
    py.image.save_as(data2, 'my_plot2.png')

'''
Adjusts the fieldnet network to behave as an index where low numbers are better
'''
def networkSep():
    yo = 2

'''
Calculate productivity of each person (just returns h-index)
'''
def calcProductivity(map):
    for node in net.nodes():
        nodecite = [x.citations for x in net.node[node]['work']]
        nodecite.sort(reverse = True)
        for x in nodecite:
            if x < nodecite.index(x) + 1:
                map[net.node[node]['name']].append(nodecite.index(x))
                break




'''
MAIN
'''
peoplef = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
grantf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
publicationf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))
mapWork = dict()
weights = dict()

createNodes(peoplef)
addWork(grantf, publicationf, mapWork)
findEdges(mapWork)
removeBlanks()
calcCollab(weights)
best(weights)
