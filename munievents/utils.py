# -*- coding: utf-8 -*-
import datetime
from typing import Dict, List, TypedDict, Union

import networkx as nx
import pandas as pd

from munievents.api_clients import Classifications

EVENTS = {
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
COLORS = [
    "rgb(12,51,131)",
    "rgb(10,136,186)",
    "rgb(242,211,56)",
    "rgb(242,143,56)",
    "rgb(217,30,30)",
]
labels = [event for event in EVENTS.values() if event]
COLORMAP = dict(zip(labels, COLORS))


last_year = datetime.datetime.now().year


def get_municipal_data() -> pd.DataFrame:
    """Get all municipal events, except for changing kanton/bezirk.
    Events covered are:
        - formed
        - merged to
        - reshaped
        - renamed
        - splitted to
    Args:
        None:

    Returns:
        pd.DataFrame:   municipal events. Includes columns:
                        - parent_name,
                        - parent_admission (yyyy),
                        - parent_abolition (yyyy),
                        - child_name,
                        - child_admission (yyyy),
                        - child_abolition (yyyy),
                        - eventdate (yyyy-mm-dd),
                        - ab_label,
                        - ad_label,
                        - event,
                        - parent
                        - child
    """

    df = Classifications().getMunicipalEvents()

    df["event"] = df.apply(lambda x: EVENTS[(x.ab_label, x.ad_label)], axis=1)
    df.child_abolition.fillna(value=last_year, inplace=True)
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


def get_communes() -> Dict[str, str]:
    """Get all swiss communes at all their configurations.
    Args:
        None:

    Returns:
        Dict[str, str]:     mapping from commune id to commune name.
                            Commune ID refers to commune between year A and B, where events happend at points A and B, but not in between.
                            The commune name refers to its official name, that may remain unchanged after the event.
    """

    df = get_municipal_data()
    names = df[df["child_abolition"] == last_year]["child_name"]
    ids = df[df["child_abolition"] == last_year]["child"]

    return dict(zip(ids, names))


def create_graph() -> nx.DiGraph:
    """Create graph representing municipal events.
    Args:
        None:

    Returns:
        Dict[str, str]:     graph representing municipal events.
                            Each node represents a commune at certain time interval, where no events happened. Nodes have properties:
                             -label
                            Each edge represents an event, changing either commune name, or shape. The edges have properties:
                            - date
                            - event
                            - color
    """

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
    """Get part of the graph containing certain node. All parts of the original graph that
    are not connected to the node are discared.
    Args:
        graph:          full graph, consisting of many unconnected subgraphs
        node:           node of interest

    Returns:
        nx.Graph:       part of the graph containing node, and all elements connected to the node.
                        Both direct and indirect connections are included.
    """

    relevant_nodes = nx.algorithms.components.node_connected_component(
        graph.to_undirected(), node
    )
    subgraph = graph.subgraph(relevant_nodes)

    return subgraph


class CytoscapeNode(TypedDict):
    id: str


class CytoscapeEdge(TypedDict):
    source: str
    target: str


class CytoscapeElement(TypedDict):

    data: Union[CytoscapeNode, CytoscapeEdge]


def networkx2cytoscape(graph: nx.Graph) -> List[CytoscapeElement]:
    """Transform networkx graph to cytoscape object.
    Args:
        graph:                      a networkx graph

    Returns:
        List[CytoscapeElement]:     a cytoscape graph. Format as per: https://dash.plotly.com/cytoscape/elements
    """

    items = []
    for node in graph.nodes:

        node_properties = graph.nodes[node]
        items.append({"data": {"id": node, **node_properties}})

    for source, target in graph.edges:

        edge_properties = graph.get_edge_data(source, target)
        items.append({"data": {"source": source, "target": target, **edge_properties}})

    return items
