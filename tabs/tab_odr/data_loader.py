import streamlit as st
import duckdb
from pathlib import Path
import gdown

@st.cache_resource
def get_odr_db(file_id: str = "1BCn1CH_VNWMslHxe1MQ4q9F2bJhbhY0o"):
    local_file = Path("TTS_phat_data.parquet")

    if not local_file.exists():
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        with st.spinner("Đang tải dữ liệu TTS_phat_data.parquet..."):
            gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    con = duckdb.connect(database=':memory:')
    
    # Cột ngày chính là ngay_bat_dau_phai_phat (hoặc ngay_trong_khoang) có sẵn kiểu Date
    con.execute(f"""
        CREATE VIEW orders AS 
        SELECT *, 
               COALESCE(
                   TRY_CAST(ngay_bat_dau_phai_phat AS DATE),
                   TRY_CAST(ngay_trong_khoang AS DATE)
               ) as clean_date
        FROM read_parquet('{local_file}')
    """)
    return con

@st.cache_data
def get_odr_filter_options(_con):
    kh_list = ["Tất cả"] + [r[0] for r in _con.execute("SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    dt_list = ["Tất cả"] + [r[0] for r in _con.execute("SELECT DISTINCT CAST(ma_doitac AS VARCHAR) FROM orders WHERE ma_doitac IS NOT NULL ORDER BY 1").fetchall()]
    return kh_list, dt_list
