"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

from csv import reader
import networkx as nx
from itertools import combinations
from tkinter import re
from time import time
from math import acos, sqrt, degrees

net = nx.Graph()
fieldnet = nx.Graph()
mapWork = dict()
mapPeople = dict()

'''
Create a storage system for publications and grants
'''
class Work:
    def __init__(self, id, name, type, year):
        self.id = id
        self.name = name
        self.type = type
        self.year = year
        self.pi = ""
        self.citations = 0
        self.authors = []

class Person:
    def __init__(self, name, field, school, position):
        self.name = name
        self.school = school
        self.field = field
        self.position = position
        self.work = []


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
        per = Person(name, field, school, position)
        mapPeople[id] = per
        net.add_node(id),

'''
Loops through grant and publication data to add the correct data to the correct people and create map of who
worked on what publication
'''
def addWork(grant, publication):
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
            try:
                position = line[5][re.search('core#', line[5]).end():len(line[5])]
            except IndexError:
                position = ''
            mapPeople[id].work.append(workid)

            if mapWork.__contains__(workid):
                if not mapWork[workid].authors.__contains__(id):
                    mapWork[workid].authors.append(id)
            else:
                mapWork[workid] = Work(workid, name, type, year)
                mapWork[workid].authors = [id]
            if position == 'PrincipalInvestigatorRole':
                mapWork[workid].pi = id

'''
Loops through map created in addWork and creates edges.
'''
def findEdges():
    for pid, ids in mapWork.items(): #for every key in the map
        people = ids.authors
        for i, j in combinations(people, 2): #go through every combo of values
            if i != j:
                field1 = mapPeople[i].field
                field2 = mapPeople[j].field
                if net.has_edge(i, j): #if they are already connected
                    net[i][j]['work'].append(pid)  #add the grant to their edge
                    if (field1 is not field2): #if different fields add to field net to count how many collabs
                        if fieldnet.has_edge(field1, field2):
                            if not fieldnet[field1][field2]['work'].__contains__(pid):
                                fieldnet[field1][field2]['work'].append(pid)
                        else: #if the fields aren't already connected, connect them
                            fieldnet.add_edge(field1, field2, work = [pid])
                else: #if there is no edge between them
                    field = (field1 == field2)
                    school = (mapPeople[i].school == mapPeople[j].school)
                    net.add_edge(i, j, work = [pid], samefield = field, sameschool = school)
                    if (field1 is not field2):
                        if fieldnet.has_edge(field1, field2):
                            if not fieldnet[field1][field2]['work'].__contains__(pid):
                                fieldnet[field1][field2]['work'].append(pid)
                        else:
                            fieldnet.add_edge(field1, field2, work = [pid])

'''
Remove nodes that have no edges at all.
'''
def removeBlanks():
    deg = net.degree()
    to_remove = [n for n in deg if deg[n] == 0]
    net.remove_nodes_from(to_remove)
    for n in to_remove:
        del mapPeople[n]

'''
Various functions that create additional data on people
'''
def calcAllMetrics():
    bw = nx.betweenness_centrality(net, normalized = False)
    for node in net.nodes():
        collabPapers = []
        deps = []
        times = []
        degree = len(net[node])
        centrality = bw[node]
        for neighbor in net[node]:
            years = []
            edgework = net.edge[node][neighbor]['work']
            field = mapPeople[neighbor].field
            if not deps.__contains__(field):
                deps.append(field)
            for work in edgework:
                years.append(int(mapWork[work].year))
                if not collabPapers.__contains__(work):
                    collabPapers.append(work)
            if len(years) <= 1:
                timeWorked = 1
            else:
                timeWorked = max(years) - min(years)
            times.append(timeWorked)
        if len(mapPeople[node].work) != 0: perc = len(collabPapers) / len(mapPeople[node].work)
        else: perc = 0
        numDeps = len(deps)
        if len(times) != 0: avgTime = sum(times) / len(times)
        else: avgTime = 0

        #now doing calculations for productivity rankings
        nodecite = [mapWork[x].citations for x in mapPeople[node].work]
        nodecite.sort(reverse=True)
        i10 = 0
        hdex = 0
        for x in nodecite:
            if x > 10:
                i10 += 1
            if x < nodecite.index(x) + 1:
                hdex = nodecite.index(x)
                break

        mapPeople[node].centrality = centrality
        mapPeople[node].degree = degree
        mapPeople[node].percCollab = perc
        mapPeople[node].numDepartments = numDeps
        mapPeople[node].avgCollabTime = avgTime
        mapPeople[node].hIndex = hdex
        mapPeople[node].i10Index = i10

def findDiff():
    for edge in net.edges():
        p1 = mapPeople[edge[0]]
        p2 = mapPeople[edge[1]]
        list = [p1.percCollab, p1.numDepartments, p1.avgCollabTime]
        list2 = [p2.percCollab, p2.numDepartments, p2.avgCollabTime]
        dot = 0
        one = 0
        two = 0
        comb = zip(list, list2)
        for x in comb:
            dot += x[0] * x[1]
            one += x[0] * x[0]
            two += x[1] * x[1]
        one = sqrt(one)
        two = sqrt(two)
        inv = dot / (one * two)
        angle = degrees(acos(inv))
        net[edge[0]][edge[1]]['diff'] = angle

'''
Fills nodes from dict() and exports
'''
def export():
    for node in net.nodes():
        curr = net.node[node]
        curr['pubs'] = len(mapPeople[node].work)
        curr['field'] = mapPeople[node].field
        curr['name'] = mapPeople[node].name
    for edge in net.edges():
        net.edge[edge[0]][edge[1]]['work'] = len(net.edge[edge[0]][edge[1]]['work'])
    nx.write_graphml(net, "hospital.graphml") #export`

'''/
MAIN
'''

start = time()
peoplef = reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/appointments_neurobiology & ophthalmology.csv'))
grantf = reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/grants_neurobiology & ophthalmology.csv'))
publicationf = reader(open('/Users/Anne/Documents/Duke/Duke Spring 2016/Data+/publications_neurobiology & ophthalmology.csv'))

createNodes(peoplef)
addWork(grantf, publicationf)
findEdges()
removeBlanks()
calcAllMetrics()
findDiff()
export()