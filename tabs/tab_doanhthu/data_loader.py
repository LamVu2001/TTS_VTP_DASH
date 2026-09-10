from pathlib import Path
import duckdb
import gdown
import streamlit as st

@st.cache_resource
def get_doanhthu_db(file_id: str):
    local_file = Path("TTS_doanhthu_data.parquet")
    
    if not local_file.exists():
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    con = duckdb.connect(database=":memory:")
    con.execute(f"""
        CREATE VIEW orders AS 
        SELECT *,
            COALESCE(
                TRY_CAST(ngay_bat_dau_phai_phat AS DATE),
                TRY_CAST(STRPTIME(CAST(ngay_bat_dau_phai_phat AS VARCHAR), '%d/%m/%Y') AS DATE),
                TRY_CAST(STRPTIME(CAST(ngay_bat_dau_phai_phat AS VARCHAR), '%Y-%m-%d') AS DATE)
            ) as clean_date
        FROM read_parquet('{local_file}')
    """)
    return con
