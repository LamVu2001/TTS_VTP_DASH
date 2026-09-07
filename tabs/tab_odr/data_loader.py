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
    
    con.execute(f"""
        CREATE VIEW orders AS 
        SELECT *, 
               TRY_CAST(ngay_bat_dau_phai_phat AS DATE) as clean_date
        FROM read_parquet('{local_file}')
    """)
    return con
