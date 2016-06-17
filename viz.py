import plotly.plotly as py
import plotly.graph_objs as go
import heapq

def bestHist(weight, nametop, namebot):
    X = 5 #top how many and bottom how many
    big = heapq.nlargest(X, weight, key = weight.get)
    data = [go.Bar(x = big, y = [weight[x] for x in big])]
    py.image.save_as(data, filename = nametop + ".png")
    small = heapq.nsmallest(X, weight, key = weight.get)
    small.reverse()
    data2 = [go.Bar(x = small, y = [weight[x] for x in small])]
    py.image.save_as(data2, filename = namebot + ".png")

def histAll(weight, metric, name):
    names = [x for x in weight.keys()]
    values = [y[metric] for y in weight.values()]
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


