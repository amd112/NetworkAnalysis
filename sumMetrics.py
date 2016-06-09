"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

import csv
import networkx as nx
import plotly.plotly as py
import itertools
import plotly.graph_objs as go
from tkinter import *
py.sign_in('amd112', '0eso7gihvt')

net = nx.Graph()

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
                else: #if there is no edge between them
                    field = (field1 == field2)
                    school = (net.node[i]['school'] == net.node[j]['school'])
                    net.add_edge(i, j, work = [], samefield = field, sameschool = school)

'''
Remove nodes that have no edges at all.
'''
def removeBlanks():
    deg = net.degree()
    to_remove = [n for n in deg if deg[n] == 0]
    net.remove_nodes_from(to_remove)

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

def avgTime(person):
    times = []
    for neigh in net[person]:
        times.append(time(person, neigh))
    return sum(times) / len(times)

def percCollab(person): #returns percentage of publications that are collaborative
    collabPapers = []
    for neighbor in net[person]:
        for work in net.edge[person][neighbor]['work']:
            if not collabPapers.__contains__(work):
               collabPapers.append(work) #can't just sum lengths because may work on same paper w/ multiple people
    perc = len(collabPapers)/len(net.node[person]['work'])
    return (perc * 100)

def createBlock(person, dev):
    it = [x/dev for x in range(0, dev)]
    perc = percCollab(person)
    time = avgTime(person)
    matrix = []
    for x in it:
        row = []
        for y in it:
            row.append((x * perc) + (y * time))
        matrix.append(row)
    return matrix



'''
MAIN
'''

peoplef = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
grantf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
publicationf = csv.reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))
mapWork = dict()
createNodes(peoplef)
addWork(grantf, publicationf, mapWork)
findEdges(mapWork)
removeBlanks()
matrix = createBlock('1004042', 100)

data = [go.Heatmap(z = matrix)]
fig = go.Figure(data = data)
py.image.save_as(fig, filename = "heat.png")
