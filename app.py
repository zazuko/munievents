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


def generate_municipal_relation():

    df = get_municipal_data()
    df = df[0:50]

    elements = []

    for source, target, event in zip(df["new_commune"], df["old_commune"], df["event"]):
        items = [
            {"data": {"id": source, "label": source}, "class": "commune"},
            {"data": {"id": target, "label": target}, "class": "commune"}
        ]

        if event :
            items += {"data": {"source": source, "target": target}, "label": event},

        elements += items
    return elements

default_stylesheet = [
    {
        'selector': '.commune',
        'style': {
            'background-color': 'yellow',
            "label": "data(label)"}
    }
]


cyto.load_extra_layouts()

elements = generate_municipal_relation()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=elements,
        layout={
            'name': 'dagre',
            'animate': False}, #cose, klay, cola
        style={'width': '{}px'.format(SCREEN_WIDTH), 'height': '{}px'.format(SCREEN_HEIGHT)},
    )
])

@app.callback(Output('cytoscape', 'stylesheet'),
             [Input('cytoscape', 'tapNode')])

def generate_stylesheet(node):

    if not node:
       return default_stylesheet

    stylesheet = [
        {
            'selector': '.commune',
            'style': {
                'background-color': 'yellow'}
        },{
            "selector": 'node[id = "{}"]'.format(node['data']['id']),
            'style': {
                'background-color': 'green',
                'label': 'data(label)',
                'z-index': 9999}
        }]

    return stylesheet


app.run_server(debug=True)