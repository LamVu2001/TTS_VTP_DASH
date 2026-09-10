import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from datetime import datetime, date

# Import trực tiếp file data_loader.py từ thư mục gốc
from data_loader import get_connection


def render(file_id: str):
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 1. KẾT NỐI DATA THEO FILE_ID
    con = get_connection(file_id)

    # 2. KHỞI TẠO SESSION STATE BỘ LỌC
    if "opr_date" not in st.session_state or not st.session_state.opr_date:
        today = date.today()
        first_day_of_month = today.replace(day=1)
        st.session_state.opr_date = (first_day_of_month, today)

    if "opr_kh" not in st.session_state: st.session_state.opr_kh = []
    if "opr_dt" not in st.session_state: st.session_state.opr_dt = []
    if "opr_kh2" not in st.session_state: st.session_state.opr_kh2 = []
    if "opr_ld" not in st.session_state: st.session_state.opr_ld = []
    if "opr_tep" not in st.session_state: st.session_state.opr_tep = []
    if "opr_tl" not in st.session_state: st.session_state.opr_tl = []

    # 3. HÀM XỬ LÝ SQL IN CLAUSE AN TOÀN
    def sql_in_clause(column_name, selected_list):
        if not selected_list:
            return None
        escaped = [str(x).replace("'", "''") for x in selected_list]
        vals = ", ".join([f"'{x}'" for x in escaped])
        return f"CAST({column_name} AS VARCHAR) IN ({vals})"

    # 4. HÀM DỰNG MỆNH ĐỀ WHERE CHO CROSS-FILTERING
    def build_where(exclude=None):
        conds = ["1=1"]
        
        # Lọc Ngày
        if exclude != "date" and isinstance(st.session_state.opr_date, (list, tuple)) and len(st.session_state.opr_date) == 2:
            conds.append(f"CAST(tg_ptc AS DATE) BETWEEN '{st.session_state.opr_date[0]}' AND '{st.session_state.opr_date[1]}'")
        
        # Lọc các danh mục (dùng Multi-select cross filtering)
        if exclude != "kh":
            c = sql_in_clause("ma_khgui", st.session_state.opr_kh)
            if c: conds.append(c)
        if exclude != "dt":
            c = sql_in_clause("ma_doitac", st.session_state.opr_dt)
            if c: conds.append(c)
        if exclude != "kh2":
            c = sql_in_clause("ma_khgui_2", st.session_state.opr_kh2)
            if c: conds.append(c)
        if exclude != "ld":
            c = sql_in_clause("loai_don", st.session_state.opr_ld)
            if c: conds.append(c)
        if exclude != "tep":
            c = sql_in_clause("tep_don", st.session_state.opr_tep)
            if c: conds.append(c)
        if exclude != "tl":
            c = sql_in_clause("nhom_trong_luong", st.session_state.opr_tl)
            if c: conds.append(c)
            
        return " AND ".join(conds)

    # 5. TRUY VẤN DANH SÁCH BỘ LỌC ĐỘNG (CROSS-FILTERING)
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    dt_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_doitac AS VARCHAR) FROM orders WHERE {build_where('dt')} AND ma_doitac IS NOT NULL ORDER BY 1").fetchall()]
    kh2_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui_2 AS VARCHAR) FROM orders WHERE {build_where('kh2')} AND ma_khgui_2 IS NOT NULL ORDER BY 1").fetchall()]
    ld_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(loai_don AS VARCHAR) FROM orders WHERE {build_where('ld')} AND loai_don IS NOT NULL ORDER BY 1").fetchall()]
    tep_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tep_don AS VARCHAR) FROM orders WHERE {build_where('tep')} AND tep_don IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(nhom_trong_luong AS VARCHAR) FROM orders WHERE {build_where('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]

    # Validate lọc sạch giá trị cũ không hợp lệ
    st.session_state.opr_kh = [v for v in st.session_state.opr_kh if v in kh_opts]
    st.session_state.opr_dt = [v for v in st.session_state.opr_dt if v in dt_opts]
    st.session_state.opr_kh2 = [v for v in st.session_state.opr_kh2 if v in kh2_opts]
    st.session_state.opr_ld = [v for v in st.session_state.opr_ld if v in ld_opts]
    st.session_state.opr_tep = [v for v in st.session_state.opr_tep if v in tep_opts]
    st.session_state.opr_tl = [v for v in st.session_state.opr_tl if v in tl_opts]

    # 6. GIAO DIỆN BỘ LỌC DÀN NGANG MULTI-SELECT
    f_opr1, f_opr2, f_opr3, f_opr4, f_opr5, f_opr6, f_opr7 = st.columns(7)

    with f_opr1:
        st.date_input("NGÀY", key="opr_date")
    with f_opr2:
        st.multiselect("MÃ KHÁCH HÀNG", kh_opts, key="opr_kh", placeholder="Tất cả")
    with f_opr3:
        st.multiselect("MÃ ĐỐI TÁC", dt_opts, key="opr_dt", placeholder="Tất cả")
    with f_opr4:
        st.multiselect("MÃ KHÁCH HÀNG (2)", kh2_opts, key="opr_kh2", placeholder="Tất cả")
    with f_opr5:
        st.multiselect("LOẠI ĐƠN", ld_opts, key="opr_ld", placeholder="Tất cả")
    with f_opr6:
        st.multiselect("TỆP ĐƠN", tep_opts, key="opr_tep", placeholder="Tất cả")
    with f_opr7:
        st.multiselect("TRỌNG LƯỢNG", tl_opts, key="opr_tl", placeholder="Tất cả")

    # 7. TÍNH TOÁN DATA THEO BỘ LỌC CHÍNH
    where_sql_opr = build_where()
    
    try:
        tong_sl_opr = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr}").fetchone()[0]
    except Exception:
        tong_sl_opr = 0

    sl_hien_thi = tong_sl_opr if tong_sl_opr > 0 else 0

    st.write("")

    # 8. CSS VÀ 6 THẺ KPI CARD
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            border: 1px solid #e0e0e0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .metric-title { font-size: 11px; font-weight: bold; color: #555; text-transform: uppercase; }
        .metric-value { font-size: 20px; font-weight: bold; color: #111; margin: 4px 0; }
        .metric-sub-green { font-size: 11px; color: #2e7d32; font-weight: 500; }
        .metric-sub-red { font-size: 11px; color: #c62828; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI THU</div><div class="metric-value">{sl_hien_thi:,.0f}</div><div class="metric-sub-green">▲ +6.8% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU TC</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐG LẦN 1</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k4: 
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG GIỜ</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ XUẤT SẠCH</div><div class="metric-value">2.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k6:
        st.markdown('<div class="metric-card"><div class="metric-title">ĐƠN TỒN QUÁ HẠN >1 NGÀY</div><div class="metric-value">221</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
