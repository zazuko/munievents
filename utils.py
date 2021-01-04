from api_clients import Classifications
import networkx as nx


def get_municipal_data():
    df = Classifications().getMunicipalEvents()

    events = {
        ("Neue Bezirks-/Kantonszuteilung", "Neue Bezirks-/Kantonszuteilung"): None,
        ("Aufhebung Gemeinde/Bezirk", "Neugründung Gemeinde/Bezirk"): "formed",         # merge multiple to new one
        ("Aufhebung Gemeinde/Bezirk", "Gebietsänderung Gemeinde"): "merged to",         # merge to existing commune
        ("Gebietsänderung Gemeinde", "Gebietsänderung Gemeinde"): "reshaped",
        ("Namensänderung Gemeinde", "Namensänderung Gemeinde"): "renamed",
        ("Gebietsänderung Gemeinde", "Neugründung Gemeinde/Bezirk"): "splitted to"      # split out a new commune
    }

    df["event"] = df.apply(lambda x: events[(x.ab_label, x.ad_label)], axis=1)
    return df


def create_graph():

    df = get_municipal_data()

    graph = nx.DiGraph()
    graph.add_nodes_from(df["new_commune"])
    graph.add_nodes_from(df["old_commune"])
    for _, row in df.iterrows():

        graph.add_edge(row["old_commune"], row["new_commune"], date=df["eventdate"], event=df["event"])

    return graph