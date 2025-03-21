import streamlit as st

cf_table_style = """
        <style>
            table { 
                width: 100%; 
                border-collapse: collapse; 
                font-family: Arial, sans-serif; 
                font-size: 14px; 
                border: 1px solid #ccc;
                overflow: scroll;
            }
            th, td { 
                padding: 8px; 
                border: 1px solid #ccc; 
                text-align: center; 
            }
            th { 
                background-color: #e6e6e6; 
                color: black; 
                font-weight: bold; 
                text-align: center;
                border-bottom: 2px solid #203354;
            }
            .actual-row td:first-child { 
                background-color: #e6e6e6; 
                font-weight: bold; 
                text-align: center; 
            }
            .actual-row td:nth-child(2) {  
                background-color: #e6e6e6; 
                font-weight: bold; 
                text-align: left; 
            }
            tbody tr:nth-last-child(-n+3) td { 
                background-color: #e6e6e6 !important;  
                font-weight: bold;  
            }
        </style>
    """


def style_page():

    st.set_page_config(layout="wide")
    st.logo("logo.png")

    st.markdown("""
    <style>
    .block-container {
        padding: 3rem;
    }
    h4, h5, p, div {
        margin: 0px; 
        padding: 0px;
    }
    .stMarkdown {
        margin: -5px;
    }
    [data-testid='stHeaderActionElements'] {
    display: none;
    }
    </style>
    """, unsafe_allow_html=True,)