import streamlit as st
import duckdb
from pathlib import Path
import gdown

@st.cache_resource
def get_connection(file_id: str = "1BCn1CH_VNWMslHxe1MQ4q9F2bJhbhY0o"):
    """
    Hàm kết nối DuckDB dùng chung cho tất cả các Tab (ODR, Doanh Thu,...).
    Tự động tải dữ liệu Parquet từ Google Drive nếu chưa có dưới local.
    """
    local_file = Path("TTS_phat_data.parquet")

    # Tải file parquet nếu chưa tồn tại
    if not local_file.exists():
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        with st.spinner("Đang tải dữ liệu TTS_phat_data.parquet..."):
            gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    # Khởi tạo DuckDB In-Memory
    con = duckdb.connect(database=':memory:')
    
    # Tạo VIEW orders chứa đầy đủ các trường dữ liệu và clean_date
    con.execute(f"""
        CREATE VIEW IF NOT EXISTS orders AS 
        SELECT *, 
               COALESCE(
                   TRY_CAST(ngay_bat_dau_phai_phat AS DATE),
                   TRY_CAST(STRPTIME(CAST(ngay_bat_dau_phai_phat AS VARCHAR), '%d/%m/%Y') AS DATE),
                   TRY_CAST(STRPTIME(CAST(ngay_bat_dau_phai_phat AS VARCHAR), '%Y-%m-%d') AS DATE)
               ) as clean_date,
               COALESCE(
                   TRY_CAST(ngay_phat_cuoi_cung AS DATE),
                   TRY_CAST(STRPTIME(CAST(ngay_phat_cuoi_cung AS VARCHAR), '%d/%m/%Y') AS DATE),
                   TRY_CAST(STRPTIME(CAST(ngay_phat_cuoi_cung AS VARCHAR), '%Y-%m-%d') AS DATE)
               ) as clean_date_ptc
        FROM read_parquet('{local_file}')
    """)
    
    return con


@st.cache_resource
def get_opr_connection(file_id: str = "1OUeMwfOHuI1sOMU2ilQySYK2IOl8Xx4n"):
    """
    Hàm kết nối DuckDB dùng chung cho tất cả các Tab (ODR, Doanh Thu,...).
    Tự động tải dữ liệu Parquet từ Google Drive nếu chưa có dưới local.
    """
    local_file = Path("TTS_thu_data.parquet")

    # Tải file parquet nếu chưa tồn tại
    if not local_file.exists():
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        with st.spinner("Đang tải dữ liệu TTS_phat_data.parquet..."):
            gdown.download(url, str(local_file), quiet=False, use_cookies=False)

    # Khởi tạo DuckDB In-Memory
    con = duckdb.connect(database=':memory:')
    
    # Tạo VIEW orders chứa đầy đủ các trường dữ liệu và clean_date
    con.execute(f"""
        CREATE VIEW IF NOT EXISTS orders AS 
        SELECT *
        FROM read_parquet('{local_file}')
    """)
    
    return con
