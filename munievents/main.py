import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output

from munievents.utils import (
    get_communes,
    COLORMAP,
    create_graph,
    get_subgraph,
    networkx2cytoscape,
)
from munievents.styles import edge_default, node_default, edge_selected, node_selected


def generate_legend(colormap):

    line_style = {
        "flexGrow": "1",
        "height": "3px",
        "maxWidth": "40px",
        "marginLeft": "10px",
        "marginRight": "10px",
        "marginTop": "5px",
        "marginBottom": "5px",
    }

    legend = []
    for key, value in colormap.items():
        item = html.Div(
            [
                html.P(style={**line_style, **{"backgroundColor": value}}),
                html.P(key, style={"marginTop": "0px", "marginBottom": "0px"}),
            ],
            style={"display": "flex", "flexDirection": "row", "alignItems": "center"},
        )

        legend.append(item)

    return html.Div(children=legend)


def generate_commune_selector():

    communes = get_communes()

    options = []
    shown = set()
    for identifier, name in sorted(communes.items()):
        if name not in shown:
            options.append({"label": name, "value": identifier})
            shown.add(name)

    dropdown = html.Form(
        autoComplete="off",
        children=[
            dcc.Dropdown(id="dropdown", options=options, placeholder="Select a commune")
        ],
    )

    return dropdown


graphy_data = create_graph()
cyto.load_extra_layouts()

app = dash.Dash(__name__)

legend = generate_legend(COLORMAP)
dropdown = generate_commune_selector()
graph = cyto.Cytoscape(
    id="cytoscape",
    layout={"name": "klay", "animate": False},
    style={"width": "95vw", "height": "80vh"},
    maxZoom=6,
)

app.layout = html.Div(children=[dropdown, graph, legend])


@app.callback(
    dash.dependencies.Output("cytoscape", "elements"),
    [dash.dependencies.Input("dropdown", "value")],
)
def generate_graph_view(value):

    if not value:
        return []

    subgraph = get_subgraph(graphy_data, value)
    items = networkx2cytoscape(subgraph)

    return items


@app.callback(Output("cytoscape", "stylesheet"), [Input("cytoscape", "tapNode")])
def generate_stylesheet(node):

    if not node:

        default_stylesheet = [
            {"selector": "edge", "style": edge_default},
            {"selector": "node", "style": node_default},
        ]
        return default_stylesheet

    stylesheet = [
        {"selector": "node", "style": node_default},
        {
            "selector": 'node[id = "{}"]'.format(node["data"]["id"]),
            "style": node_selected,
        },
        {"selector": "edge", "style": edge_default},
        {
            "selector": "edge[source = '{}'].".format(node["data"]["id"]),
            "style": edge_selected,
        },
        {
            "selector": "edge[target = '{}'].".format(node["data"]["id"]),
            "style": edge_selected,
        },
    ]

    return stylesheet


app.run_server(debug=True)
