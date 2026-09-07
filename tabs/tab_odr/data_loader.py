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
    
    # Xử lý ép kiểu ngày an toàn theo cả dạng DATE gốc lẫn dạng STRING (DD/MM/YYYY hoặc YYYY-MM-DD)
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
