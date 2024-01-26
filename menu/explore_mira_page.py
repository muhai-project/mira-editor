import pandas as pd
import streamlit as st
from rdflib import Graph
import networkx as nx
import got
import semantify
import validate
from semanticscholar import SemanticScholar
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC
import streamlit.components.v1 as components
import os
import numpy as np


paper_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
PREFIX dcterms: <http://purl.org/dc/terms/>
prefix sio: <http://semanticscience.org/resource/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT distinct ?title ?sub ?obj ?med ?mod where {
    ?paper dcterms:title ?title .
    ?paper sio:SIO_000008/sio:SIO_000008 ?exp .
    ?paper sio:SIO_000008/sio:SIO_000008 ?int .
    ?exp mira:hasSubject ?s .
    ?s qb:concept/rdfs:label ?sub .
    ?exp mira:hasObject ?o .
    ?o qb:concept/rdfs:label ?obj .
    OPTIONAL {?exp mira:hasMediator ?m . ?m qb:concept/rdfs:label ?med .}
    OPTIONAL {?int mira:hasObject ?exp.
              ?int mira:hasSubject/qb:concept/rdfs:label ?mod}
 }
"""

concept_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
SELECT distinct ?concept ?label where {
 ?var qb:concept ?concept .
 ?concept rdfs:label ?label .
 }
"""
sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/MIR-KG")

@st.cache_data()
def retrieve_papers():
    sparql.setQuery(paper_query)
    sparql.method = 'GET'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    df = pd.DataFrame(results['results']['bindings'])

    def extract_value(x):
        if isinstance(x, dict) and 'value' in x:
            return x['value']
        else:
            return x

            # Apply the function to all elements in the DataFrame
    df = df.applymap(extract_value)

    #st.dataframe(df)
    #df = df.applymap(lambda x: x['value'])
    return df

@st.cache_data()
def df_multiselect():
    sparql.setQuery(concept_query)
    sparql.method = 'GET'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    df = pd.DataFrame(results['results']['bindings'])
    df = df.applymap(lambda x: x['value'])
    concepts = df['concept'].tolist()
    return df

def main():
    show_stats = st.container()
    selector_container = st.empty()

    with selector_container.container():
        if 'start_node' not in st.session_state:
            st.session_state.start_node = 'Poverty'
            #'http://purl.bioontology.org/ontology/MESH/D011203'
        if 'end_node' not in st.session_state:
            st.session_state.end_node = 'Mortality'
        if 'length' not in st.session_state:
            st.session_state.length = 4
        if 'results' not in st.session_state:
            st.session_state.results = 10
        if 'start_term' not in st.session_state:
            st.session_state.start_term = 'Poverty'
        if 'start_term' not in st.session_state:
            st.session_state.end_term = 'Mortality'

        col2, col3, col4, col5, col6 = st.columns(5)
        df1 = df_multiselect()
        # st.write(df1[df1['concept'].isin(['http://purl.bioontology.org/ontology/MESH/D011203'])])
        # st.write(df1[df1['concept'].isin(['http://purl.bioontology.org/ontology/MESH/D006262'])])

        paper_df = retrieve_papers()
        #st.dataframe(paper_df)
        selected_paper = st.selectbox('Select paper',
                    np.unique(paper_df['title'].tolist()),
                    index=1,
                    key='paper')


        with col2:
            selected_med = st.selectbox('start node',
                        df1['label'].tolist(),
                        # format_func=lambda x: df1[df1['concept'].isin([x])]['label'].values[0],
                        index=3,
                        key='start_node')
        with col3:
            selected_med = st.selectbox('end node',
                            df1['label'].tolist(),
                            # format_func=lambda x: df1[df1['concept'].isin([x])]['label'].values[0],
                            index=17,
                            key='end_node')
        with col4:
            slider_select = st.slider('Path length', 0, 20, 4, key='length')
        with col5:
            slider_select = st.slider("NR results",
                value=15,
                step = 1,
                min_value=1, max_value=30,
                key='results')

        with col6:
            on = st.toggle('Explain paper')
            if on:
                paper_view = True
            else:
                paper_view = False

        st.session_state.nr_paths, st.session_state.start_term, st.session_state.end_term = plot_network.explore_causenet(st.session_state.start_node,
                            st.session_state.end_node,
                            df1,st.session_state.length,
                            st.session_state.results,
                            paper_df,selected_paper,
                            paper_view)
        HtmlFile = open("causenet.html", 'r', encoding='utf-8')
        source_code = HtmlFile.read()
        components.html(source_code, height = 610)

        st.markdown(r'''

*Causal relations come from CauseNet: a large-scale knowledge base of _claimed_ causal relations between causal concepts

Heindorf, S., Scholten, Y., Wachsmuth, H., Ngonga Ngomo, A. C., & Potthast, M. (2020, October).
Causenet: Towards a causality graph extracted from the web. In Proceedings of the 29th ACM international
conference on information & knowledge management (pp. 3023-3030).


''')

    with show_stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown('**MIRA-KG**')
        col1.markdown('*:violet[Causenet* Causal mechanisms]* ')
        col2.metric("$\#$ Paths", st.session_state.nr_paths)
        col3.metric("Variable 1 :violet[(Cause)]", st.session_state.start_term)
        col4.metric("Variable 2 :orange[(Effect)]", st.session_state.end_term)

    #HtmlFile = open("mira.html", 'r', encoding='utf-8')
    #source_code = HtmlFile.read()
    #components.html(source_code, height = 610)

if __name__ == '__main__':
    main()
