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


def main():
    st.sidebar.write("""
        ## About
        Using the semantify functionality, researchers can add new
        claims to the MIRA-KG by extracting them from research papers.
    """)

    if "paper_nodes" not in st.session_state:
        st.session_state.paper_nodes = 0
    if "paper_edges" not in st.session_state:
        st.session_state.paper_edges = 0
    if "violations" not in st.session_state:
        st.session_state.violations = 0

    # st.title("Semantify paper")
    show_stats = st.container()
    semantify_paper = st.container()

    with semantify_paper:
        paper_doi = st.text_input('Paper DOI...',placeholder='10.1001/jamanetworkopen.2020.34578',value='10.1001/jamanetworkopen.2020.34578')
        sch = SemanticScholar()
        title = st.empty()
        title.caption('')
        empty_container = st.empty()
        empty_container.markdown(
            f'<div style="height: 150px; background: #ffffe0"></div>',
            unsafe_allow_html=True
        )

        if st.button('Process abstract'):
            try:
                paper = sch.get_paper(paper_doi)
                if paper:
                    abstract = paper['abstract']
            except:
                st.error('Cannot find paper abstract based on this DOI.')
                abstract = None

            if abstract:
                title.caption(paper['title'])
                empty_container.markdown(
                    f'<div style="height: 150px; background: #ffffe0">'+paper["abstract"]+'</div>',
                    unsafe_allow_html=True
                )

            col1, col2 = st.columns(2)

            with col1:

                st.session_state.paper_nodes, st.session_state.paper_edges = semantify.run(paper,"insert-your-openai-key",'./output/output.ttl')
                plot_network.mira_func(True)
                HtmlFile = open("mira.html", 'r', encoding='utf-8')
                source_code = HtmlFile.read()
                components.html(source_code, height = 610)

                if os.path.exists('./output/output.ttl'):
                    with open('./output/output.ttl') as f:
                        with st.expander('RDF output'):
                            st.code(f.read(), language='SPARQL')

                with col2:
                    with st.status("Validating output graph..."):
                        st.session_state.violations = validate.run('./output/output.ttl','./SHACL/shacl-shapes.ttl','./output/validation_output.ttl')

                    plot_network.mira_func(True,True)
                    HtmlFile = open("mira-validate.html", 'r', encoding='utf-8')
                    source_code = HtmlFile.read()
                    components.html(source_code, height = 610)

                    # st.text('SHACL shapes')
                    if os.path.exists('./SHACL/shacl-shapes.ttl'):
                        with open('./SHACL/shacl-shapes.ttl') as f:
                            with st.expander('SHACL shapes'):
                                st.code(f.read(), language='SPARQL')

    with show_stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown('**MIRA-KG**')
        col1.markdown('*:violet[Semantify articles]* ')
        col2.metric("$\#$ Nodes", st.session_state.paper_nodes)
        col3.metric("$\#$ Edges", st.session_state.paper_edges)
        col4.metric("$\#$ Violations", st.session_state.violations)


if __name__ == '__main__':
    main()
