# -*- coding: utf-8 -*-
from typing import Dict, List

import networkx as nx

from munievents.api_clients import Classifications

colors = [
    "rgb(12,51,131)",
    "rgb(10,136,186)",
    "rgb(242,211,56)",
    "rgb(242,143,56)",
    "rgb(217,30,30)",
]
labels = ["renamed", "reshaped", "formed", "merged to", "splitted to"]
COLORMAP = dict(zip(labels, colors))

LAST_YEAR = 2020


def get_municipal_data():

    df = Classifications().getMunicipalEvents()

    events = {
        ("Neue Bezirks-/Kantonszuteilung", "Neue Bezirks-/Kantonszuteilung"): None,
        (
            "Aufhebung Gemeinde/Bezirk",
            "Neugründung Gemeinde/Bezirk",
        ): "formed",  # merge multiple to new one
        (
            "Aufhebung Gemeinde/Bezirk",
            "Gebietsänderung Gemeinde",
        ): "merged to",  # merge to existing commune
        ("Gebietsänderung Gemeinde", "Gebietsänderung Gemeinde"): "reshaped",
        ("Namensänderung Gemeinde", "Namensänderung Gemeinde"): "renamed",
        (
            "Gebietsänderung Gemeinde",
            "Neugründung Gemeinde/Bezirk",
        ): "splitted to",  # split out a new commune
    }

    df["event"] = df.apply(lambda x: events[(x.ab_label, x.ad_label)], axis=1)
    df.child_abolition.fillna(value=LAST_YEAR, inplace=True)
    df.child_abolition = df.child_abolition.astype(int)

    df["parent"] = (
        df["parent_name"]
        + df["parent_admission"].astype(str)
        + "-"
        + df["parent_abolition"].astype(str)
    )
    df["child"] = (
        df["child_name"]
        + df["child_admission"].astype(str)
        + "-"
        + df["child_abolition"].astype(str)
    )

    # Remove data on kanton change
    is_irrelevant_data = df["event"].isnull()
    for row in df[is_irrelevant_data].itertuples():
        is_parent = df["child"] == row.parent
        df.loc[is_parent, ["child_abolition"]] = row.child_abolition

        is_child = df["parent"] == row.child
        df.loc[is_child, ["parent_admission"]] = row.parent_admission

    df = df[~is_irrelevant_data]
    df["parent"] = (
        df["parent_name"]
        + df["parent_admission"].astype(str)
        + "-"
        + df["parent_abolition"].astype(str)
    )
    df["child"] = (
        df["child_name"]
        + df["child_admission"].astype(str)
        + "-"
        + df["child_abolition"].astype(str)
    )

    return df


def get_communes():

    df = get_municipal_data()
    names = df[df["child_abolition"] == LAST_YEAR]["child_name"]
    ids = df[df["child_abolition"] == LAST_YEAR]["child"]

    return dict(zip(ids, names))


def create_graph():

    df = get_municipal_data()
    graph = nx.DiGraph()

    for row in df.itertuples():

        graph.add_node(row.parent, label=row.parent_name)
        graph.add_node(row.child, label=row.child_name)

        if row.event:
            graph.add_edge(
                row.parent,
                row.child,
                date=row.eventdate.year,
                event=row.event,
                color=COLORMAP[row.event],
            )

    return graph


def get_subgraph(graph: nx.Graph, node: str) -> nx.Graph:

    relevant_nodes = nx.algorithms.components.node_connected_component(
        graph.to_undirected(), node
    )
    subgraph = graph.subgraph(relevant_nodes)

    return subgraph


def networkx2cytoscape(graph: nx.Graph) -> List[Dict]:

    items = []
    for node in graph.nodes:

        node_properties = graph.nodes[node]
        items.append({"data": {"id": node, **node_properties}})

    for source, target in graph.edges:

        edge_properties = graph.get_edge_data(source, target)
        items.append({"data": {"source": source, "target": target, **edge_properties}})

    return items
