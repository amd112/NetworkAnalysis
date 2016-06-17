"""
author: Anne Driscoll
contact: amd112@duke.edu
date: May 26th, 2016
"""

from createNetwork import createNodes, addWork, findEdges, calcAllMetrics, removeBlanks
from sumMetrics import time, avgTime, degree, percCollab
import csv
from tkinter import *
from tkinter import filedialog


appointments = ''
pubs = ''
grants = ''

def getAppoint():
    appointments = csv.reader(filedialog.askopenfile(mode='r'))

def getGrant():
    grants = csv.reader(filedialog.askopenfile(mode='r'))

def getPubs():
    pubs = csv.reader(filedialog.askopenfile(mode='r'))

def makeNetwork():
    if not type(appointments) == str:
        createNodes(appointments)
        if not type(grants) == str and not type(pubs) == str:
            addWork(grants, pubs)
            findEdges()

def makeWindow():
    win = Tk() #so win is the main window

    uploads = Frame(win)
    uploads.grid(row = 1, column = 1)

    appoint = Button(uploads, text = 'Upload Appointment File', command = getAppoint)
    grant = Button(uploads, text = '    Upload Grants File    ', command = getGrant)
    publications = Button(uploads, text = 'Upload Publications File', command = getPubs)
    lab = Label(uploads, text = 'Make sure to remove headers and comments from files before upload')

    appoint.grid(row = 1, column = 1)
    grant.grid(row = 2, column = 1)
    publications.grid(row = 3, column = 1)
    lab.grid(row =2 , column = 3)

    actions = Frame(win)
    actions.grid(row = 4, column = 1)

    create = Button(actions, text = 'Create Network from Uploads', command = makeNetwork)
    blanks = Button(actions, text = 'Remove Nodes w/ no connections from Network', command = removeBlanks)
    metrics = dict()
    weights = Button(actions, text = 'Calculate weights for all nodes', command = lambda: calcAllMetrics(metrics))
    dispchoice = StringVar(actions)
    display = OptionMenu(actions, dispchoice, 'Histogram of all nodes', 'Histogram of top 10 nodes')
    metchoice = StringVar(actions)
    metric = OptionMenu(actions, metchoice, 'degree', 'betweenness centrality', 'percentage collaborative', 'average collaboration time')

    create.grid(row=2, column=1)
    blanks.grid(row=2, column=2)
    weights.grid(row=2, column=3)
    display.grid(row = 4, column = 1)
    metric.grid(row = 4, column = 3)

    return win

win = makeWindow()
win.mainloop()