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

pnl_table_style = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        .header-row{
            font-weight: bold;
            text-align: center;
            position: sticky;
            top: 1px;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
            outline: 1px solid #ddd;
        }
        
        .sticky1, .sticky2, .sticky3, .sticky4 {
            position: sticky;
            z-index: 50;
            background-color: inherit; !important;
            outline: 1px solid #ddd;
        }
        .sticky1 { left: 1px; }
        .sticky2 { left: 17px; }
        .sticky3 { left: 34px; }
        .sticky4 { left: 118px; }

        .white {
            background-color: white;
        }
        .gray {
            background-color: #f2f2f2;
        }

        td {
            padding: 8px;
            border: 1px solid #ddd;
            text-align: right;
        }
        th {
            padding: 8px;
            border: 1px solid #ddd;
            background-color: #f2f2f2;
        }
        .main-category {
            font-weight: bold;
            background-color: #d9d9d9;
            text-align: left;
        }
        .sub-category {
            font-weight: bold;
            background-color: #f9f9f9;
            text-align: left;
        }
        .sub-total {
            font-weight: bold;
            background-color: #ececec;
        }
        .main-total {
            font-weight: bold;
            background-color: #c0c0c0;
        }
        tr:hover {
            background-color: #e6f7ff;
        }
    </style>
    """


def style_page():

    st.set_page_config(layout="wide", page_icon="logo.png")
    st.logo("logo.png")

    st.markdown(
        """
    <style>
    .block-container {
        padding: 3rem;
    }
    h4, h5, div, span {
        margin: 0px; 
        padding: 0px;
    }
    .stMarkdown {
        margin: 0px;
        padding: 0px;
    }
    [data-testid='stHeaderActionElements'] {
    display: none;
    }
    header {
        visibility: hidden;
        } 
    footer {
        visibility: hidden;
        }   
    </style>
    """,
        unsafe_allow_html=True,
    )
