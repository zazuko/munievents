import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
from api_clients import SparqlClient
import networkx as nx
import json

import networkx as nx
import matplotlib.pyplot as plt

from utils import get_municipal_data

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000

colormap = {
    "renamed": "black",
    "reshaped": "blue",
    "formed": "green",
    "merged to": "orange",
    "splitted to": "violet"
}

def generate_municipal_relation():

    df = get_municipal_data()
    df = df[0:50]

    elements = []

    for source, target, event, date in zip(df["new_commune"], df["old_commune"], df["event"], df["eventdate"]):
        items = [
            {"data": {"id": source, "label": source}, "class": "commune"},
            {"data": {"id": target, "label": target}, "class": "commune"}
        ]

        if event :
            items += {"data": {"source": source, "target": target, "label": event, "color": colormap[event], "date": date.year}},

        elements += items
    return elements


cyto.load_extra_layouts()

elements = generate_municipal_relation()

app = dash.Dash(__name__)



def generate_legend(colormap):

    line_style = {
        "flexGrow": "1",
        "height": "3px",
        "maxWidth": "40px",
        "marginLeft": "10px",
        "marginRight": "10px",
        "marginTop": "5px",
        "marginBottom": "5px"
    }

    legend = []
    for key, value in colormap.items():
        item = html.Div([
            html.P(style={**line_style, **{"backgroundColor": value}}),
            html.P(key, style={"marginTop": "0px", "marginBottom": "0px"}),],
            style={"display": "flex", "flexDirection": "row", "alignItems": "center"})

        legend.append(item)

    return legend

legend = generate_legend(colormap)
graph = [cyto.Cytoscape(
    id='cytoscape',
    elements=elements,
    layout={
        'name': 'dagre',
        'animate': False},
        style={'width': '{}px'.format(SCREEN_WIDTH), 'height': '{}px'.format(SCREEN_HEIGHT)}
        )]

app.layout = html.Div(legend+graph)



default_stylesheet = [
    {"selector": "edge",
    "style": {
        'target-arrow-color': 'data(color)',
        'target-arrow-shape': 'triangle',
        "line-color": "data(color)"
    }}]

@app.callback(Output('cytoscape', 'stylesheet'),
             [Input('cytoscape', 'tapNode')])

def generate_stylesheet(node):

    if not node:
       return default_stylesheet

    stylesheet = [
        {
            "selector": 'node[id = "{}"]'.format(node['data']['id']),
            'style': {
                'background-color': 'green',
                'label': 'data(label)',
                'z-index': 9999}
        },
        {
            "selector": 'edge',
            "style": {
                "line-color": "data(color)",
                "target-arrow-color": 'data(color)',
                "target-arrow-shape": 'triangle',
                'z-index': 9999
            }
        },
        {
            "selector": "edge[source = '{}'].".format(node["data"]["id"]),
            "style": {
                "label": "data(date)"
            }
        },{
            "selector": "edge[target = '{}'].".format(node["data"]["id"]),
            "style": {
                "label": "data(date)"
            }
        }]

    return stylesheet


app.run_server(debug=True)