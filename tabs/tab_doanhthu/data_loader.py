import streamlit as st
from tabs.tab_odr.data_loader import get_odr_db

@st.cache_data
def load_doanhthu_data():
    con = get_odr_db()
    query = "SELECT * FROM orders"
    return con.execute(query).df()
