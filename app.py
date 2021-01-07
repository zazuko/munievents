import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output


from utils import get_communes, COLORMAP, create_graph, get_subgraph, networkx2cytoscape

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

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

    return html.Div(children=legend)

def generate_commune_selector():

    communes = get_communes()
    options = []
    for commune_id, commune_name in sorted(communes.items()):
        options.append({
            "label": commune_name,
            "value": commune_id
        })

    dropdown = html.Label(dcc.Dropdown(
    id='dropdown',
    options=options,
    placeholder="Select a commune"))

    return dropdown

graphy_data = create_graph()
cyto.load_extra_layouts()

app = dash.Dash(__name__)


legend = generate_legend(COLORMAP)
dropdown = generate_commune_selector()
graph = cyto.Cytoscape(
    id='cytoscape',
    layout={
        'name': 'klay',
        'animate': False},
        style={'width': '{}px'.format(SCREEN_WIDTH), 'height': '{}px'.format(SCREEN_HEIGHT)}
        )

app.layout = html.Div(children=[legend, dropdown, graph])


default_stylesheet = [
    {"selector": "edge",
    "style": {
        'target-arrow-color': 'data(color)',
        'target-arrow-shape': 'triangle',
        "curve-style": "bezier",
        "line-color": "data(color)",
        "target-arrow-color": 'data(color)',
        "target-arrow-shape": 'triangle',
        "curve-style": "bezier",
        'z-index': 9999
    }},
    {"selector": "node",
    "style": {
        "background-color": "grey",
        "label": "data(label)",
        "width": "20px",
        "height": "20px"
    }
    }]

@app.callback(
    dash.dependencies.Output('cytoscape', 'elements'),
    [dash.dependencies.Input('dropdown', 'value')])
def generate_graph_view(value):

    if not value:
        return []

    subgraph = get_subgraph(graphy_data, value)
    items = networkx2cytoscape(subgraph)

    return items


@app.callback(Output('cytoscape', 'stylesheet'),
             [Input('cytoscape', 'tapNode')])
def generate_stylesheet(node):

    if not node:
       return default_stylesheet

    stylesheet = [
        {
            "selector": "node",
            "style": {
                "background-color": "grey",
                "label": "data(label)",
                "width": "20px",
                "height": "20px"
            }
        },
        {
            "selector": 'node[id = "{}"]'.format(node['data']['id']),
            'style': {
                'background-color': 'yellow',
                'z-index': 9999}
        },
        {
            "selector": 'edge',
            "style": {
                'target-arrow-color': 'data(color)',
                'target-arrow-shape': 'triangle',
                "curve-style": "bezier",
                "line-color": "data(color)",
                "target-arrow-color": 'data(color)',
                "target-arrow-shape": 'triangle',
                "curve-style": "bezier",
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