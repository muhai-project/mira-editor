import pandas as pd
import streamlit as st
from rdflib import Graph
import networkx as nx
import plot_network
import semantify
import validate
from semanticscholar import SemanticScholar
import streamlit.components.v1 as components
import os
from streamlit_folium import folium_static
import folium
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC
import requests
import json
import datetime
import numpy as np
sparql = SPARQLWrapper("http://127.0.0.1:7200/repositories/MIRA-KG")

total_studies_query = """
SELECT distinct (count(?study) as ?total_studies) where {
 ?study a <http://semanticscience.org/resource/SIO_000976>
 }
 """
sub_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
SELECT distinct ?concept ?label where {
 ?exp mira:hasSubject/qb:concept ?concept .
 ?concept rdfs:label ?label .
 }
"""

obj_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
SELECT distinct ?concept ?label where {
 ?exp mira:hasObject/qb:concept ?concept .
 ?concept rdfs:label ?label .
 }
"""
med_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
SELECT distinct ?concept ?label where {
 ?exp mira:hasMediator/qb:concept ?concept .
 ?concept rdfs:label ?label .
 }
"""

mod_query = """
prefix mira: <https://w3id.org/mira/ontology/>
prefix qb: <http://purl.org/linked-data/cube#>
SELECT distinct ?concept ?label where {
?exp rdf:type mira:InteractionEffect .
?exp mira:hasSubject/qb:concept ?concept .
?concept rdfs:label ?label .
}
"""

@st.cache_data
def get_df(sub,obj,med,mod,range):
        countQuery = """
        prefix mira: <https://w3id.org/mira/ontology/>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        prefix sio: <http://semanticscience.org/resource/>
        prefix qb: <http://purl.org/linked-data/cube#>
        prefix owl: <http://www.w3.org/2002/07/owl#>
        PREFIX wgs84_pos: <http://www.w3.org/2003/01/geo/wgs84_pos#>
        prefix mesh: <http://purl.bioontology.org/ontology/MESH/>
        prefix ex: <http://example.org/>
        PREFIX gn: <http://www.geonames.org/ontology#>
        prefix time: <http://www.w3.org/2006/time#>
        prefix skos: <http://www.w3.org/2004/02/skos/core#>
        prefix bibo: <http://purl.org/ontology/bibo/>
        PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT distinct ?code (sum(?count) as ?sum) WHERE {{
         {{
        SELECT distinct ?code ?count WHERE {{
         {{
        SELECT DISTINCT ?geonamesId (COUNT(?sample) as ?count) WHERE {{
         {{
        SELECT DISTINCT ?geonamesId ?sample WHERE {{
                {sub}
                {obj}
                {med}
                {mod}
                    OPTIONAL {{ ?int mira:hasSubject ?mod .
                              ?int mira:hasObject ?exp}} .
                    ?study sio:SIO_000008 ?exp .
                    ?exp mira:hasSubject/qb:concept ?sub .
                    ?exp mira:hasObject/qb:concept ?obj .
                    OPTIONAL {{ ?exp mira:hasMediator/qb:concept ?med }}
                    ?exp mira:hasContext ?con .
                    ?con sio:SIO_000205 ?sample .
                    ?sample sem:hasPlace ?region .
                    ?sample time:hasTime/time:hasBeginning/time:inXSDDate ?begin ;
                                            time:hasTime/time:hasEnd/time:inXSDDate ?end .
                    FILTER (?begin > "{begin}"^^xsd:date) .
                    FILTER (?end < "{end}"^^xsd:date) .
                    ?region gn:locatedIn ?geonamesId .
                }}
            }}
            }} GROUP BY ?geonamesId
            }}
              SERVICE <http://factforge.net/repositories/ff-news> {{
                # ?geonamesId (
                #   <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasLocation>/gn:officialName
                # )|gn:officialName ?code .
                    ?geonamesId a <http://dbpedia.org/ontology/Country> .
                    ?geonamesId gn:officialName ?code
                FILTER (lang(?code) = 'en')
              }}
         }}
         }}
        }} groupby ?code
        """
        sub_vars = 'VALUES ?sub {'+" ".join(['<'+var+'>' for var in sub])+'}' if sub != [] else ""
        obj_vars = 'VALUES ?obj {'+" ".join(['<'+var+'>' for var in obj])+'}' if obj != [] else ""
        med_vars = 'VALUES ?med {'+" ".join(['<'+var+'>' for var in med])+'}' if med != [] else ""
        mod_vars = 'VALUES ?mod {'+" ".join(['<'+var+'>' for var in mod])+'}' if mod != [] else ""
        countQuery = countQuery.format(sub=sub_vars, obj=obj_vars, med=med_vars, mod=mod_vars, begin=range[0], end=range[1])
        # st.code(countQuery, language='SPARQL')
        sparql.setQuery(countQuery)
        sparql.method = 'GET'
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        plot_df = pd.DataFrame(results['results']['bindings'])
        plot_df = plot_df.applymap(lambda x: x['value'])
        if plot_df.empty:
            plot_df = pd.DataFrame(columns=['code', 'sum'])
        else:
            plot_df["code"]=plot_df["code"].values.astype(str)
            plot_df["sum"]=plot_df["sum"].values.astype(int)

        return plot_df

def display_map():

    paper_query = """
    PREFIX sem: <http://semanticweb.cs.vu.nl/2009/11/sem/>
    PREFIX mira: <https://w3id.org/mira/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sio: <http://semanticscience.org/resource/>
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX prisms: <http://prismstandard.org/namespaces/1.2/basic/>
    PREFIX time: <http://www.w3.org/2006/time#>
    PREFIX gn: <http://www.geonames.org/ontology#>

    SELECT distinct ?doi ?name ?begin ?end WHERE {{
        {sub}
        {obj}
        ?paper prisms:doi ?doi .
        ?paper sio:SIO_000008/sio:SIO_000008 ?exp .
        ?exp mira:hasSubject/qb:concept ?sub .
        ?exp mira:hasObject/qb:concept ?obj .
        ?exp mira:hasContext ?con .
        ?con sio:SIO_000205 ?sample .
        ?sample sem:hasPlace ?region .
        ?sample time:hasTime/time:hasBeginning/time:inXSDDate ?begin ;
                                time:hasTime/time:hasEnd/time:inXSDDate ?end .
        ?region gn:locatedIn ?geonamesId .
        ?geonamesId gn:name ?name .
     }}
    """

    with st.session_state.map_container.container():
        plot_df = get_df(st.session_state.sub,
                        st.session_state.obj,
                        st.session_state.med,
                        st.session_state.mod,
                        st.session_state.range)
        # st.session_state.studies = plot_df["sum"].sum()
        #st.dataframe(plot_df)
        map = folium.Map(tiles='CartoDB positron',zoom_start=3)

        url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
        country_shapes = f'{url}/world-countries.json'

        choropleth = folium.Choropleth(
            geo_data = country_shapes,
            data=plot_df,
            fill_color='YlOrRd',
            columns=['code','sum'],
            key_on='feature.properties.name',
            fill_opacity=0.7,
            line_opacity=0.2,
            highLight=True,
            legend_name='Legend',
            nan_fill_color='transparent',
            nan_fill_opacity=0,
            bins=100
        ).add_to(map)

        for feature in choropleth.geojson.data['features']:
            name = feature['properties']['name']
            feature['properties']['sum'] = 1
            feature['properties']['sum'] = str(plot_df[plot_df['code'].isin([name])]['sum'].values[0] if name in list(plot_df['code'].tolist()) else '0')

        choropleth.geojson.add_child(
            folium.features.GeoJsonTooltip(['name','sum'],labels=False)
        )
        st_map = folium_static(map, width=1200, height=500)
        # if st.button('Show academic articles:'):
        sub_vars = 'VALUES ?sub {'+" ".join(['<'+var+'>' for var in st.session_state.sub])+'}' if st.session_state.sub != [] else ""
        obj_vars = 'VALUES ?obj {'+" ".join(['<'+var+'>' for var in st.session_state.obj])+'}' if st.session_state.obj != [] else ""

        paper_query = paper_query.format(sub=sub_vars, obj=obj_vars)
        sparql.setQuery(paper_query)
        sparql.method = 'GET'
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        paper_df = pd.DataFrame(results['results']['bindings'])
        paper_df = paper_df.applymap(lambda x: x['value'])
        #st.code(paper_query, language='SPARQL')
        st.session_state.studies = len(np.unique(paper_df['doi'].values))
        st.dataframe(paper_df, use_container_width=True)
            # except:
            #     st.error('Please select two variables...')

@st.cache_data()
def df_multiselect(query):
    sparql.setQuery(query)
    sparql.method = 'GET'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    df = pd.DataFrame(results['results']['bindings'])
    df = df.applymap(lambda x: x['value'])
    concepts = df['concept'].tolist()
    return df


def main():

    st.sidebar.write("""
        ## About
        Here you can query the graph through predefined SPARQL queries.
    """)

    sparql.setQuery(total_studies_query)
    sparql.method = 'GET'
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    total_studies = pd.DataFrame(results['results']['bindings'])
    total_studies = total_studies.applymap(lambda x: x['value'])

    if 'sub' not in st.session_state:
        st.session_state.sub = []
    if 'obj' not in st.session_state:
        st.session_state.obj = []
    if 'med' not in st.session_state:
        st.session_state.med = []
    if 'mod' not in st.session_state:
        st.session_state.mod = []
    if "range" not in st.session_state:
        st.session_state.range = (datetime.date(1900, 1, 1), datetime.date(2024, 1, 1))
    if "studies" not in st.session_state:
        st.session_state.studies = int(total_studies['total_studies'].values[0])
    if "total_studies" not in st.session_state:
        st.session_state.total_studies = int(total_studies['total_studies'].values[0])

    show_stats = st.container()
    slider_container = st.empty()
    selector_container = st.empty()
    if "map_container" not in st.session_state:
        st.session_state.map_container = st.empty()

    display_map()

    with show_stats:
        col1, col2, col3 = st.columns(3)
        col1.markdown('**MIRA-KG**')
        col1.markdown('*:violet[Study samples]* ')
        col2.metric("$\#$ population samples", st.session_state.studies)
        col3.metric("$\#$ total studies", st.session_state.total_studies)

    with slider_container.container():
        slider_select = st.slider("Period beginning",
            value=(datetime.date(1900, 1, 1), datetime.date(2024, 1, 1)),
            step = datetime.timedelta(days=30),
            format="MM/DD/YYYY", key='range')

    with selector_container.container():
        col1, col2 = st.columns(2)
#, col3, col4
        with col1:
            df1 = df_multiselect(sub_query)
            selected_sub = st.multiselect('independent variables',
                            df1['concept'].tolist(),
                            format_func=lambda x: df1[df1['concept'].isin([x])]['label'].values[0],
                            # on_change=display_map,
                            placeholder="select",
                            key='sub')
        with col2:
            df2 = df_multiselect(obj_query)
            selected_obj = st.multiselect('dependent variables',
                            df2['concept'].tolist(),
                            format_func=lambda x: df2[df2['concept'].isin([x])]['label'].values[0],
                            # on_change=display_map,
                            placeholder="select",
                            key='obj')
        # with col3:
        #     df3 = df_multiselect(med_query)
        #     selected_med = st.multiselect('mediator variables',
        #                     df3['concept'].tolist(),
        #                     format_func=lambda x: df3[df3['concept'].isin([x])]['label'].values[0],
        #                     # on_change=display_map,
        #                     placeholder="select",
        #                     key='med')
        # with col4:
        #     df4 = df_multiselect(mod_query)
        #     selected_mod = st.multiselect('moderator variables',
        #                     df4['concept'].tolist(),
        #                     format_func=lambda x: df4[df4['concept'].isin([x])]['label'].values[0],
        #                     # on_change=display_map,
        #                     placeholder="select",
        #                     key='mod')

if __name__ == '__main__':
    main()
