import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import pandas as pd
import streamlit as st
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib.namespace import NamespaceManager, RDF, RDFS
from rdflib import Graph, Namespace, URIRef
import os
import re
import base64
from itertools import islice
import difflib

sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/MIRA-KG")

def k_shortest_paths(G, source, target, cn_df, k, nr_results, weight=None):
    source_matched = difflib.get_close_matches(source,list(cn_df['source'].values)+list(cn_df['target'].values),1,cutoff=0.85)
    target_matched = difflib.get_close_matches(target,list(cn_df['source'].values)+list(cn_df['target'].values),1,cutoff=0.85)
    if (source_matched != []) & (target_matched != []):
        paths = list(
            islice(nx.all_simple_paths(G, source_matched[0], target_matched[0], k), nr_results)
        )
    else:
        paths = []

    return paths

def explore_causenet(start,end,df1,length,nr_results,paper_df,paper, paper_view=True):

    if paper_view:
        start = paper_df[paper_df['title'].isin([paper])].iloc[0]['sub']
        end = paper_df[paper_df['title'].isin([paper])].iloc[0]['obj']

    cn_df = pd.read_pickle('../MIRA-KG/mira/data/causenet/causenet_df.pkl')
    cn_df['cause'] = cn_df['cause'].str.replace('death', 'mortality', regex=True, case=False)
    cn_df['effect'] = cn_df['effect'].str.replace('death', 'mortality', regex=True, case=False)
    cn_df['cause'] = cn_df['cause'].str.replace('health', 'mortality', regex=True, case=False)
    cn_df['effect'] = cn_df['effect'].str.replace('health', 'mortality', regex=True, case=False)
    cn_df['cause'] = cn_df['cause'].str.replace('_', ' ', regex=True, case=False)
    cn_df['effect'] = cn_df['effect'].str.replace('_', ' ', regex=True, case=False)

    cn_df.columns = ['source','target']
    G = nx.from_pandas_edgelist(cn_df)

    paths = k_shortest_paths(G, start, end, cn_df, length, nr_results)

    f = nx.DiGraph()  # Initialize a new directed graph

    # Add edges to the new graph based on the paths
    for path in paths:
        edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        f.add_edges_from(edges)
        f.add_node(edges[0][0], title=edges[0][0], color='purple')
        f.add_node(edges[len(edges)-1][1],title=edges[len(edges)-1][1], color='orange')
    nt= Network(notebook=True, directed=True)
    nt.from_nx(f)
    for edge in nt.edges:
        edge['title'] = 'causes'
    nt.toggle_physics(True)
    nt.force_atlas_2based(gravity=-100)

    nt.show('causenet.html')
    return len(paths), start, end

def mira_func(physics,validation=False):

    g = Graph()
    schema = Graph()
    gSchema = Graph()
    if validation:
        file = "./output/validation_output.ttl"
    else:
        file = "./output/test_output.ttl"
    if os.path.exists(file):
        g.parse(file, format="turtle")
    schema.parse("../MIRA-KG/mira/MIRA-ontology.ttl")
    gSchema = g + schema
    EX = Namespace("http://example.org/")
    TIME = Namespace("http://www.w3.org/2006/time#")
    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
    VOCAB = Namespace("https://iisg.amsterdam/resource/country/")
    SEM = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")
    GN = Namespace("http://www.geonames.org/ontology#")
    SIO = Namespace("http://semanticscience.org/resource/")
    AUTHOR = Namespace("http://semanticscholar/author/")
    MIRA = Namespace("https://w3id.org/mira/")
    SP= Namespace("https://w3id.org/linkflows/superpattern/latest/")
    BIBO = Namespace("http://purl.org/ontology/bibo/")
    GENID = Namespace("https://rdflib.github.io/.well-known/genid/rdflib/")

    g.bind("ex", EX)
    g.bind("time",TIME)
    g.bind("skos",SKOS)
    g.bind("sem",SEM)
    g.bind("gn",GN)
    g.bind("sio",SIO)
    g.bind("author",AUTHOR)
    g.bind("mira", MIRA)
    g.bind("sp",SP)
    g.bind("bibo",BIBO)
    g.bind("genid",GENID)
    nt = Network("600px", "800px",notebook=True,directed=True)
    nt.force_atlas_2based(gravity=-100)

    for src, prop, dst in g.triples((None, None, None)):

        if prop.n3() != '<http://www.w3.org/2000/01/rdf-schema#label>':
            if prop.n3().endswith('abstract>'):
                pass
            else:
                if (src, RDF.type, SKOS.Concept) in g:
                    src_color = '#FF8000'
                else:
                    src_color = '#30ACBF'

                if (dst, RDF.type, SKOS.Concept) in g:
                    dst_color = '#FF8000'
                else:
                    dst_color = '#30ACBF'

                src_node = src.n3(g.namespace_manager)
                src_label = gSchema.value(src,RDFS.label)
                if src_label == None:
                    src_label = src_node

                prop_node = prop.n3(g.namespace_manager)
                prop_label = gSchema.value(prop,RDFS.label)
                if prop_label == None:
                    prop_label = prop_node

                dst_node = dst.n3(g.namespace_manager)
                dst_label = gSchema.value(dst,RDFS.label)
                if dst_label == None:
                    dst_label = dst_node

                if prop_label == 'rdf:type':
                    dst_color = '#BF6075'
                elif prop_label == 'sem:hasPlace':
                    dst_color = '#60BF60'
                elif prop_label == 'time:hasTime':
                    dst_color = '#F5FF00'

                nt.add_node(src, label=src_label, title=src_label, color=src_color)
                nt.add_node(dst, label=dst_label, title=dst_label, color=dst_color)
                nt.add_edge(src, dst, label=prop_label, title=prop_label)

    if physics:
        nt.show_buttons(filter_=['physics'])
    if validation:
        nt.show('mira-validate.html')

    else:
        nt.show('mira.html')
