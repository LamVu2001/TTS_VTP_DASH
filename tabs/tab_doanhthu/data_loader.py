import streamlit as st
from tabs.tab_odr.data_loader import get_odr_db

@st.cache_data
def load_doanhthu_data():
    # Khởi tạo kết nối DuckDB
    con = get_odr_db()
    
    # Query lấy dữ liệu từ VIEW 'orders' đã tạo ở tab_odr
    query = """
        SELECT *
        FROM orders
    """
    df = con.execute(query).df()
    return df
