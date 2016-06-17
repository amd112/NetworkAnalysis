"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

import networkx as nx

net = nx.Graph()


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

def degree(person):
    return len(net[person])

