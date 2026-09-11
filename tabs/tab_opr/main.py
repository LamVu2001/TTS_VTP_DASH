import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from datetime import datetime, date

# Import trực tiếp file data_loader.py từ thư mục gốc
from data_loader import get_opr_connection

def render(file_id: str):
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 1. KẾT NỐI DATA THEO FILE_ID
    con = get_opr_connection(file_id)

    # 1. KHỞI TẠO SESSION STATE BỘ LỌC
    if "opr_date" not in st.session_state or not st.session_state.opr_date:
        today = date.today()
        first_day_of_month = today.replace(day=1)
        st.session_state.opr_date = (first_day_of_month, today)

    if "opr_kh" not in st.session_state: st.session_state.opr_kh = []
    if "opr_tn" not in st.session_state: st.session_state.opr_tn = []
    if "opr_bc" not in st.session_state: st.session_state.opr_bc = []
    if "opr_dv" not in st.session_state: st.session_state.opr_dv = []
    if "opr_tl" not in st.session_state: st.session_state.opr_tl = []

    # 2. HÀM XỬ LÝ SQL IN CLAUSE
    def sql_in_clause(column_name, selected_list):
        if not selected_list:
            return None
        escaped = [str(x).replace("'", "''") for x in selected_list]
        vals = ", ".join([f"'{x}'" for x in escaped])
        return f"{column_name} IN ({vals})"

    # 3. HÀM DỰNG MỆNH ĐỀ WHERE CROSS-FILTERING
    def build_where(exclude=None):
        conds = ["1=1"]
        
        # Lọc ngày dùng time_nhap_may
        if exclude != "date" and isinstance(st.session_state.opr_date, (list, tuple)) and len(st.session_state.opr_date) == 2:
            d_start, d_end = st.session_state.opr_date
            conds.append(f"time_nhap_may >= '{d_start} 00:00:00' AND time_nhap_may <= '{d_end} 23:59:59'")
        
        # Lọc Mã khách hàng
        if exclude != "kh" and st.session_state.opr_kh:
            c = sql_in_clause("ma_khgui", st.session_state.opr_kh)
            if c: conds.append(c)
            
        # Lọc Tỉnh nhận
        if exclude != "tn" and st.session_state.opr_tn:
            c = sql_in_clause("tinh_nhan", st.session_state.opr_tn)
            if c: conds.append(c)

        # Lọc Bưu cục phát (map ma_buucuc_goc)
        if exclude != "bc" and st.session_state.opr_bc:
            c = sql_in_clause("ma_buucuc_goc", st.session_state.opr_bc)
            if c: conds.append(c)
            
        # Lọc Mã dịch vụ
        if exclude != "dv" and st.session_state.opr_dv:
            c = sql_in_clause("ma_dv_viettel", st.session_state.opr_dv)
            if c: conds.append(c)
            
        # Lọc Trọng lượng
        if exclude != "tl" and st.session_state.opr_tl:
            c = sql_in_clause("nhom_trong_luong", st.session_state.opr_tl)
            if c: conds.append(c)
            
        return " AND ".join(conds)

    # 4. DANH SÁCH TÙY CHỌN BỘ LỌC ĐỘNG TỪ DATABASE
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_khgui FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    tn_opts = [r[0] for r in con.execute(f"SELECT DISTINCT tinh_nhan FROM orders WHERE {build_where('tn')} AND tinh_nhan IS NOT NULL ORDER BY 1").fetchall()]
    bc_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_buucuc_goc FROM orders WHERE {build_where('bc')} AND ma_buucuc_goc IS NOT NULL ORDER BY 1").fetchall()]
    dv_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_dv_viettel FROM orders WHERE {build_where('dv')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = [r[0] for r in con.execute(f"SELECT DISTINCT nhom_trong_luong FROM orders WHERE {build_where('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]

    # 5. GIAO DIỆN BỘ LỌC DÀN NGANG (6 CỘT)
    f_opr1, f_opr2, f_opr3, f_opr4, f_opr5, f_opr6 = st.columns(6)

    with f_opr1:
        st.date_input("NGÀY NHẬP MÁY", key="opr_date")
    with f_opr2:
        st.multiselect("MÃ KHÁCH HÀNG", kh_opts, key="opr_kh", placeholder="Tất cả")
    with f_opr3:
        st.multiselect("TỈNH NHẬN", tn_opts, key="opr_tn", placeholder="Tất cả")
    with f_opr4:
        st.multiselect("BƯU CỤC PHÁT", bc_opts, key="opr_bc", placeholder="Tất cả")
    with f_opr5:
        st.multiselect("MÃ DỊCH VỤ", dv_opts, key="opr_dv", placeholder="Tất cả")
    with f_opr6:
        st.multiselect("TRỌNG LƯỢNG", tl_opts, key="opr_tl", placeholder="Tất cả")

    # 6. TÍNH TOÁN DỮ LIỆU
    where_sql_opr = build_where()
    
    try:
        tong_sl_opr = con.execute(f"SELECT COUNT(DISTINCT ma_phieugui) FROM orders WHERE {where_sql_opr}").fetchone()[0]
    except Exception:
        tong_sl_opr = 0

    sl_hien_thi = tong_sl_opr if tong_sl_opr > 0 else 0

    st.write("")

    # 7. CSS & METRIC CARDS
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

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG THU</div><div class="metric-value">{sl_hien_thi:,.0f}</div><div class="metric-sub-green">▲ +6.8% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU TC</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐG LẦN 1</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)
    with k4: 
        st.markdown('<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG GIỜ</div><div class="metric-value">82.4%</div><div class="metric-sub-red">▼ -3.1% vs Mục tiêu</div></div>', unsafe_allow_html=True)

    st.write("")
