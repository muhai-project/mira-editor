import streamlit as st
import streamlit.components.v1 as components
import seaborn as sns
from rdflib import Graph
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC
import pandas as pd
from pyvis.network import Network
import datetime

def show_network():

    with st.session_state.plot_container.container():

        # Create an empty graph
        G = nx.Graph()

        # Create a pyvis network
        pyvis_graph = Network(notebook=True, directed=True, select_menu=True,filter_menu=True,cdn_resources='remote')

        #Add node sizes based on incoming edges
        for _, row in st.session_state.count_df.iterrows():
            if (int(row['count']) >= 1):#st.session_state.weight[0]
                df = st.session_state.df
                dois = np.unique(df[(df['source'].isin([row.source])) & (df['target'].isin([row.target]))]['doi'].values)
                #st.write(dois)
                pyvis_graph.add_node(row['source'], label=row['source'], title=row['source'], font={'size': 20})  # Source nodes in blue
                pyvis_graph.add_node(row['target'], label=row['target'], title=row['target'], font={'size': 20})  # Source nodes in blue
                title = "Papers:\n" + "\n".join(dois)
                #str(row['count'])+" p
                pyvis_graph.add_edge(row['source'], row['target'], title=title)

        neighbor_map = pyvis_graph.get_adj_list()

        for node in pyvis_graph.nodes:
            node["value"] = len(neighbor_map[node["id"]])

        # Example: Getting the number of nodes and edges
        st.session_state.nodes = len(pyvis_graph.nodes)
        st.session_state.edges = len(pyvis_graph.edges)

        # Set the barnesHut solver
        pyvis_graph.set_options('''{
            "physics": {
                "solver": "barnesHut",
                "maxVelocity": 10
            }
        }''')

        # Show the graph
        pyvis_graph.show('co-occurrences.html')
        st.markdown("*Co-occurrence network of study variables*.")
        HtmlFile = open("co-occurrences.html", 'r', encoding='utf-8')
        source_code = HtmlFile.read()
        components.html(source_code, height = 800)

def main():

    sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/MIRA-KG")

    query = """
    PREFIX mira: <https://w3id.org/mira/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX prisms: <http://prismstandard.org/namespaces/1.2/basic/>
    SELECT ?doi ?source ?target WHERE {
        ?paper prisms:doi ?doi .
        ?paper sio:SIO_000008/sio:SIO_000008 ?s .
     	?s mira:hasSubject ?subj .
        ?subj qb:concept ?subjConcept.
        ?s mira:hasObject ?obj .
        ?obj qb:concept ?objConcept.
        ?subjConcept rdfs:label ?source .
        ?objConcept rdfs:label ?target .
     }
    """

    sparql.setQuery(query)
    sparql.method = 'GET'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    df = pd.DataFrame(results['results']['bindings'])
    df = df.applymap(lambda x: x['value'])
    nodes = list(df['source'].values) + list(df['target'].values)
    count_df = pd.DataFrame({'count' : df.groupby(['source', 'target']).size()}).reset_index()

    if "nodes" not in st.session_state:
        st.session_state.nodes = len(np.unique(np.array(nodes)))
    if "edges" not in st.session_state:
        st.session_state.edges = len(count_df)
    if "weight" not in st.session_state:
        st.session_state.weight = (1,30)
    if "df" not in st.session_state:
        st.session_state.df = df
    if "count_df" not in st.session_state:
        st.session_state.count_df = count_df

    show_stats = st.container()
    select_param = st.container()
    if "plot_container" not in st.session_state:
        st.session_state.plot_container = st.empty()

    show_network()

    with show_stats:
        col4, col1, col2 = st.columns(3)
        col4.markdown('**MIRA-KG**')
        col4.markdown('*:violet[Co-occurrences]* ')
        col1.metric("$\#$ Nodes", st.session_state.nodes)
        col2.metric("$\#$ Edges", st.session_state.edges)


if __name__ == '__main__':
    main()
