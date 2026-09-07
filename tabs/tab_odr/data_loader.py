import streamlit as st
import duckdb
from pathlib import Path
import gdown

@st.cache_resource
def get_odr_db(file_id: str = "1BCn1CH_VNWMslHxe1MQ4q9F2bJhbhY0o"):
    local_file = Path("TTS_phat_data.parquet")

    # Tải file từ Google Drive nếu máy local chưa có
    if not local_file.exists():
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        with st.spinner("Đang tải dữ liệu TTS_phat_data.parquet..."):
            gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    con = duckdb.connect(database=':memory:')
    
    # Đọc dữ liệu từ file Parquet và chuẩn hóa cột ngày
    con.execute(f"""
        CREATE VIEW orders AS 
        SELECT *, 
               COALESCE(
                   TRY_CAST(ngay_bat_dau_phai_phat AS DATE),
                   TRY_CAST(ngay_trong_khoang AS DATE)
               ) as clean_date
        FROM read_parquet('{local_file}', ignore_errors=true)
    """)
    return con
