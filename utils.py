from api_clients import Classifications
import networkx as nx


LAST_YEAR = 2020
COLORMAP = {
    "renamed": "black",
    "reshaped": "blue",
    "formed": "green",
    "merged to": "orange",
    "splitted to": "violet",
    "changed district/kanton": "grey"
}


def get_municipal_data():


    df = Classifications().getMunicipalEvents()

    events = {
        ("Neue Bezirks-/Kantonszuteilung", "Neue Bezirks-/Kantonszuteilung"): "changed district/kanton",
        ("Aufhebung Gemeinde/Bezirk", "Neugründung Gemeinde/Bezirk"): "formed",         # merge multiple to new one
        ("Aufhebung Gemeinde/Bezirk", "Gebietsänderung Gemeinde"): "merged to",         # merge to existing commune
        ("Gebietsänderung Gemeinde", "Gebietsänderung Gemeinde"): "reshaped",
        ("Namensänderung Gemeinde", "Namensänderung Gemeinde"): "renamed",
        ("Gebietsänderung Gemeinde", "Neugründung Gemeinde/Bezirk"): "splitted to"      # split out a new commune
    }

    df["event"] = df.apply(lambda x: events[(x.ab_label, x.ad_label)], axis=1)
    df.child_abolition.fillna(value=LAST_YEAR, inplace=True)
    df.child_abolition = df.child_abolition.astype(int)

    df["parent"] = df["parent_name"] + " (" + df["parent_admission"].astype(str) + "-" + df["parent_abolition"].astype(str) + ")"
    df["child"] = df["child_name"] + " (" + df["child_admission"].astype(str) + "-" + df["child_abolition"].astype(str) + ")"
    #df["child"] = df.apply(lambda x: x.child_name + x.child_dates if x.child_dates else x.child_name, axis=1)

    return df

def get_communes():

    df = get_municipal_data()
    names = df[df["child_abolition"] == LAST_YEAR]["child_name"]
    ids = df[df["child_abolition"] == LAST_YEAR]["child"]

    return dict(zip(ids, names))

def create_graph():

    start = 1960
    x_len = LAST_YEAR-start

    df = get_municipal_data()
    graph = nx.DiGraph()

    for row in df.itertuples():

        graph.add_node(row.parent, label=row.parent_name)
        graph.add_node(row.child, label=row.child_name)

        if row.event :
            graph.add_edge(row.parent, row.child, date=row.eventdate.year, event=row.event, color=COLORMAP[row.event])

    return graph


def get_subgraph(graph: nx.Graph, node: str):

    relevant_nodes = nx.algorithms.components.node_connected_component(graph.to_undirected(), node)
    subgraph = graph.subgraph(relevant_nodes)

    return subgraph

def networkx2cytoscape(graph: nx.Graph):

    items = []
    for node in graph.nodes:

        node_properties = graph.nodes[node]
        items.append({
            "data": {"id": node, **node_properties}
        })

    for source, target in graph.edges:

        edge_properties = graph.get_edge_data(source, target)
        items.append({
            "data": {"source": source, "target": target, **edge_properties}
        })

    return items


if __name__ == "__main__":

    graph = create_graph()
    node = "Marly (1970-1976)"
    subgraph = get_subgraph(graph, node)
    print(networkx2cytoscape(subgraph))

