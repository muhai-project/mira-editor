import pandas as pd
import streamlit as st
from rdflib import Graph
import networkx as nx
import got
import semantify
from menu import semantify_paper_page, query_mira_page, explore_mira_page, explain_mira_page, about, statistics_page
import validate
from semanticscholar import SemanticScholar
import streamlit.components.v1 as components
import os

sch = SemanticScholar()

PAGES = [
    'About',
    'Co-occurrence Network',
    'Population Samples',
    'Semantify Paper',
    'Explore Causal Mechanisms'
]


def run_UI():
    st.set_page_config(
        page_title="MIRA-KG explorer",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': """

        """
        }
    )
    logo_url = './figures/logo.png'
    st.sidebar.image(logo_url)

    st.sidebar.title('MIRA-KG explorer')
    if st.session_state.page:
        page=st.sidebar.radio('Navigation', PAGES, index=st.session_state.page)
    else:
        page=st.sidebar.radio('Navigation', PAGES, index=0)

    st.experimental_set_query_params(page=page)

    if page == 'Semantify Paper':
        semantify_paper_page.main()

    if page == 'Population Samples':
        query_mira_page.main()
    # #
    if page == 'Explore Causal Mechanisms':
        explore_mira_page.main()

    if page == 'Co-occurrence Network':
        statistics_page.main()

    if page == 'About':
        about.main()


if __name__ == '__main__':

    url_params = st.experimental_get_query_params()
    if 'loaded' not in st.session_state:
        if len(url_params.keys()) == 0:
            st.experimental_set_query_params(page='About')
            url_params = st.experimental_get_query_params()

        st.session_state.page = PAGES.index(url_params['page'][0])
        st.session_state['loaded'] = False

    run_UI()
