"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

import csv
import time
import networkx as nx
import itertools
import plotly.plotly as py
import plotly.graph_objs as go
import urllib
from tkinter import *
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import heapq
import random
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

def getAllCites(grant, publication, mapCite):
    for x in [grant, publication]:
        y = 0
        for line in x:
            id = line[0][re.search('per', line[0]).end():len(line[0])]
            title = line[2]
            person = net.node[id]['name']
            num = getCite(person, title)
            workid = line[1][re.search(x[1], line[1]).end():len(line[1])]
            mapCite[workid] = num
            wait = [.5, 1, 2, 2.1, .9, 1.5, 3, 2.6, 3.4, .7, 5]
            time.sleep(random.choice(wait))
            if x % 50 == 0:
                time.sleep(5)
            elif x % 100 == 0:
                time.sleep(15)
    writer = csv.writer(open('citations.csv', 'wb'))
    for key, value in mapCite.items():
        writer.writerow([key, value])


'''
Loops through grant and publication data to add the correct data to the correct people and create map of who
worked on what publication
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
Remove nodes that have no edges at all.
'''
def removeBlanks():
    deg = net.degree()
    to_remove = [n for n in deg if deg[n] == 0]
    net.remove_nodes_from(to_remove)


'''
Calculate the collaboration coefficient of each node and saves in map (name: number), various helper functions
'''
def calcAllMetrics(dict):
    for node in net.nodes():
        collabPapers = []
        curr = net.node[node]
        deps = []
        times = []
        for neighbor in net[curr]:
            years = []
            edgework = net.edge[curr][neighbor]['work']
            ids = [x.id for x in net.node[node]['work']]
            field = net.node[neighbor]['field']
            if not deps.__contains__(field):
                deps.append(field)
            for work in edgework:
                index = ids.index(work)
                years.append(int(net.node[node]['work'][index].year))
                if not collabPapers.__contains__(work):
                    collabPapers.append(work)
            if len(years) <= 1:
                timeWorked = 1
            else:
                timeWorked = max(years) - min(years)
            times.append(timeWorked)
        perc = len(collabPapers) / len(net.node[curr]['work'])
        numDeps = len(deps)
        avgTime = sum(times) / len(times)

        #now doing calculations for productivity rankings
        nodecite = [x.citations for x in net.node[node]['work']]
        nodecite.sort(reverse=True)
        i10 = 0
        for x in nodecite:
            if x > 10:
                i10 += 1
            if x < nodecite.index(x) + 1:
                hIndex = nodecite.index(x)
                break
        dict[net.node[node]['name']] = {'percCollab': perc, 'numDepartments': numDeps, 'avgCollabTime': avgTime,
                                        'hIndex': hIndex, 'i10Index': i10}
        
'''
4 visualization options.
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

def histAll(weight, name):
    names = [x for x in weight.keys()]
    values = [y for y in weight.values()]
    tog = zip(values, names)
    tog = sorted(tog, key = lambda x: x[0], reverse = True)
    val, named = zip(*tog)
    data = [go.Bar(x = named, y = val)]
    py.image.save_as(data, filename = name + ".png")

def scatterAll(collab, productive, name):
    data = [go.Scatter(x = [collab[x] for x in collab], y = [productive[x] for x in productive], mode = 'markers')]
    py.image.save_as(data, name + ".png")

def stackedHist(weight, weight2, weight3, name):
    names = [x for x in weight.keys()]
    values = [y for y in weight.values()]
    names2 = [x for x in weight2.keys()]
    values2 = [y for y in weight2.values()]
    names3 = [x for x in weight3.keys()]
    values3 = [y for y in weight3.values()]
    tog = zip(values, names, values2, names2, values3, names3)
    tog = sorted(tog, key=lambda x: x[0], reverse=True)
    val, nam, val2, nam2, val3, nam3 = zip(*tog)
    data = go.Bar(x = nam, y = val)
    data2 = go.Bar(x = nam2, y = val2)
    data3 = go.Bar(x = nam3, y = val3)
    trace = [data, data2, data3]
    layout = go.Layout(barmode='group')
    fig = go.Figure(data=trace, layout=layout)
    py.image.save_as(fig, filename = name + ".png")


'''
Calculate productivity of each person. Next four functions are all options
'''

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
Clears lists for export to graphml.
'''
def export():
    for this in net.nodes():
        net.node[this]['work'] = len(net.node[this]['work']) #make publications just be # of pubs
    for this, that in net.edges():
        net.edge[this][that]['work'] = len(net.edge[this][that]['work'])
    nx.write_graphml(net, "hospital.graphml") #export`



'''
MAIN
'''
peoplef = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
grantf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
publicationf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))
mapWork = dict()
weights = dict()
productive = dict()
mapCite = dict()

createNodes(peoplef)
getAllCites(grantf, publicationf, mapCite)
