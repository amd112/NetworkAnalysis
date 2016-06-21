"""
author: Anne Driscoll
contact: amd112@duke.edu
date: June 2016
"""

from createNetwork import createNodes, addWork, findEdges, calcAllMetrics, removeBlanks, mapPeople, mapWork
import csv
from tkinter import *
from tkinter import filedialog
import plotly.plotly as py
import plotly.graph_objs as go
from heapq import nlargest
py.sign_in('amd112', '0eso7gihvt')
appointments = ''
pubs = ''
grants = ''
metrics = dict()

def makeWindow():
    win = Tk() #so win is the main window

    uploads = Frame(win)
    uploads.grid(row = 1, column = 1)

    appoint = Button(uploads, text = 'Upload Appointment File', command = lambda: getAppoint(appoint))
    grant = Button(uploads, text = '    Upload Grants File    ', command = lambda: getGrant(grant))
    publications = Button(uploads, text = 'Upload Publications File', command = lambda: getPubs(publications))
    global lab
    lab = Label(uploads, text = 'Make sure to remove headers and comments from files before upload')

    appoint.grid(row = 1, column = 1)
    grant.grid(row = 2, column = 1)
    publications.grid(row = 3, column = 1)
    lab.grid(row =2 , column = 3)

    actions = Frame(win)
    actions.grid(row = 4, column = 1)

    create = Button(actions, text = 'Create Network from Uploads', command = lambda: makeNetwork(create))
    global dispchoice
    dispchoice = StringVar(actions)
    dispchoice.set('Histogram of all nodes')
    display = OptionMenu(actions, dispchoice, 'Histogram of all nodes', 'Histogram of top 10 nodes')
    global metchoice
    metchoice = StringVar(actions)
    metchoice.set('degree')
    metric = OptionMenu(actions, metchoice, 'degree', 'betweenness centrality', 'percentage collaborative', 'average collaboration time')
    showViz = Button(actions, text = 'Show rankings', command = show)
    global viz
    viz = Canvas(win, width = 500, height = 400)

    create.grid(row=2, column=1)
    display.grid(row = 3, column = 1)
    metric.grid(row = 3, column = 2)
    showViz.grid(row=4, column =1)
    viz.grid(row = 5, column = 1)

    return win

def getAppoint(button):
    global appointments
    appointments = csv.reader(filedialog.askopenfile(mode='r'))
    button.grid_forget()

def getGrant(button):
    global grants
    grants = csv.reader(filedialog.askopenfile(mode='r'))
    button.grid_forget()

def getPubs(button):
    global pubs
    pubs = csv.reader(filedialog.askopenfile(mode='r'))
    button.grid_forget()
    lab.config(text = 'Create a Network now!')

def makeNetwork(button):
    if not type(appointments) == str:
        createNodes(appointments)
        if not type(grants) == str and not type(pubs) == str:
            addWork(grants, pubs)
            findEdges()
            calcAllMetrics()
            removeBlanks()
            lab.config(text="Network created!")
            button.grid_forget()

def show():
    string = metchoice.get()
    type = dispchoice.get()
    viz.delete(ALL)
    if type == 'Histogram of all nodes': histAll(string, 'file')
    elif type == 'Histogram of top 10 nodes': bestHist(string, 'file')
    else: lab.config(text="Please choose an item in each of the drop downs", fg="red")
    img = PhotoImage(file = 'file.png')
    viz.create_image(0, 0, image = img, anchor = NW)
    viz.image = img

def bestHist(metric, file):
    X = 5 #top how many and bottom how many
    metrics = ['degree', 'betweenness centrality', 'percentage collaborative', 'average collaboration time']
    values = []
    if metric == 'degree': values = [val.degree for val in mapPeople.values()]
    elif metric == 'betweenness centrality': values = [val.centrality for val in mapPeople.values()]
    elif metric == 'average collaboration time': values = [val.avgCollabTime for val in mapPeople.values()]
    elif metric == 'percentage collaborative': values = [val.percCollab for val in mapPeople.values()]
    names = [val.name for val in mapPeople.values()]
    try:
        tog = zip(values, names)
        tog = sorted(tog, key=lambda x: x[0], reverse=True)
        val, named = zip(*tog)
        data = [go.Bar(x=named[0:X], y=val[0:X])]
        py.image.save_as(data, filename=file + ".png", height = 400, width = 500)
    except ValueError:
        lab.config(text="Can't find the Network, did you make sure to upload the files and create the network?",
                   fg="red")

def histAll(metric, file):
    metrics = ['degree', 'betweenness centrality', 'percentage collaborative', 'average collaboration time']
    values = []
    print(metric)
    if metric not in metrics:
        lab.config(text="Not a valid metric input", fg="red")
        return
    if metric == 'degree': values = [val.degree for val in mapPeople.values()]
    elif metric == 'betweenness centrality': values = [val.centrality for val in mapPeople.values()]
    elif metric == 'average collaboration time': values = [val.avgCollabTime for val in mapPeople.values()]
    elif metric == 'percentage collaborative': values = [val.percCollab for val in mapPeople.values()]
    names = [val.name for val in mapPeople.values()]
    try:
        tog = zip(values, names)
        tog = sorted(tog, key = lambda x: x[0], reverse = True)
        val, named = zip(*tog)
        data = [go.Bar(x=named, y=val)]
        py.image.save_as(data, filename = file + ".png", width = 500, height = 400)
    except ValueError:
        lab.config(text="Can't find the Network, did you make sure to upload the files and create the network?", fg="red")

win = makeWindow()
win.mainloop()

