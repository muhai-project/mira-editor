import streamlit as st
import os
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript


def main():
    if os.path.exists('./figures/data-explanations.png'):
        st.image('./figures/data-explanations.png', caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")

        # st.markdown("""
        # Matching a theory with a use case: can we explain patterns using a theory from our KG?
        # """)
        st.subheader("Mathing a theory with a use case:")
        st.write("Sample of population:")
        # image = Image.open('figures/example-claim.png')
        st.image('figures/example-claim.png', caption='Example claim')
        st.markdown("Use case from IISH: Is there a difference in **mortality rates** of **children** with fathers having **occupations** in varying HISCO classifications, in the **Netherlands between 1910-1920?**")
        # image = Image.open('usecase.png')
        # st.image(image, caption='Use case')
        query = """
            PREFIX schema: <http://schema.org/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX civ: <https://iisg.amsterdam/id/civ/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            SELECT ?occupation ?n_occs ?deaths (xsd:float(?deaths)/xsd:float(?n_occs) * 100 AS ?share)
            WHERE {

              SELECT

              (sum(?hasDeath) as ?deaths) (count(?occupation) as ?n_occs) ?occupation

              WHERE {

             ?birth civ:father ?father .
             ?father schema:hasOccupation ?occupation .
             BIND(exists{?birth civ:linkedToDeath ?death} AS ?hasDeath )

              }
              }
            ORDER BY DESC(?n_occs)
        """
        js_code = """
        const yasgui = new Yasgui(document.getElementById("yasgui"), {
        requestConfig: { endpoint: "https://api.druid.datalegend.net/datasets/dataLegend/workshop-demo/services/workshop-demo/sparql" },
        copyEndpointOnNewTab: false});

        """

        components.html(
        """<head>
          <link href="https://unpkg.com/@triply/yasgui/build/yasgui.min.css" rel="stylesheet" type="text/css" />
          <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css"
     integrity="sha256-kLaT2GOSpHechhsozzB+flnD+zUyjE2LlfWPgU04xyI="crossorigin=""/>
          <script src="https://unpkg.com/@triply/yasgui/build/yasgui.min.js"></script>
          <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"
     integrity="sha256-WBkoXOwTeyKclOHuWtc+i2uENFpDZ9YPdf5Hf+D7ewM="crossorigin=""></script>
        </head>
        <body>
          <div id="yasgui"></div>
          <script>
          """+js_code+"""
          </script>
        </body>

        """, height=660)




if __name__ == '__main__':
    main()
