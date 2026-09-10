from pathlib import Path
import duckdb
import gdown
import streamlit as st


@st.cache_resource
def get_doanhthu_db():
  local_file = Path("TTS_phat_data.parquet")

  if not local_file.exists():
    url = "https://drive.google.com/uc?export=download&id=1BCn1CH_VNWms1Hxe1MQ4q9F2bJhbhY0o"
    gdown.download(url, str(local_file), quiet=False, use_cookies=False)

  con = duckdb.connect(database=":memory:")
  con.execute(f"""
        CREATE VIEW orders AS 
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
