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
    if "opr_dt" not in st.session_state: st.session_state.opr_dt = []
    if "opr_dv" not in st.session_state: st.session_state.opr_dv = []
    
    if "opr_tl" not in st.session_state:
        st.session_state.opr_tl = st.session_state.get("f_tl", [])

    # 2. HÀM XỬ LÝ SQL IN CLAUSE
    def sql_in_clause(column_name, selected_list):
        if not selected_list:
            return None
        escaped = [str(x).replace("'", "''") for x in selected_list]
        vals = ", ".join([f"'{x}'" for x in escaped])
        return f"{column_name} IN ({vals})"

    # 3. HÀM DỰNG MỆNH ĐỀ WHERE CROSS-FILTERING (CẬP NHẬT ĐIỀU KIỆN TRỌNG LƯỢNG MỚI)
    def build_where(exclude=None):
        conds = ["1=1"]
        
        # Lọc ngày dùng time_nhap_may
        if exclude != "date" and isinstance(st.session_state.opr_date, (list, tuple)) and len(st.session_state.opr_date) == 2:
            d_start, d_end = st.session_state.opr_date
            conds.append(f"time_nhap_may >= '{d_start} 00:00:00' AND time_nhap_may <= '{d_end} 23:59:59'")
        
        if exclude != "kh" and st.session_state.opr_kh:
            c = sql_in_clause("ma_khgui", st.session_state.opr_kh)
            if c: conds.append(c)
            
        if exclude != "dt" and st.session_state.opr_dt:
            c = sql_in_clause("ma_doitac", st.session_state.opr_dt)
            if c: conds.append(c)
            
        if exclude != "dv" and st.session_state.opr_dv:
            c = sql_in_clause("ma_dv_viettel", st.session_state.opr_dv)
            if c: conds.append(c)
            
        # Phân loại trọng lượng khớp 100% hình ảnh mẫu
        selected_tl = st.session_state.get("opr_tl", [])
        if exclude != "tl" and selected_tl:
            tl_conds = []
            for val in selected_tl:
                if val == "< 500g":
                    tl_conds.append("trong_luong < 500")
                elif val == "500g - < 1000g":
                    tl_conds.append("trong_luong >= 500 AND trong_luong < 1000")
                elif val == "1000g - < 2000g":
                    tl_conds.append("trong_luong >= 1000 AND trong_luong < 2000")
                elif val == ">= 2000g":
                    tl_conds.append("trong_luong >= 2000")
            if tl_conds:
                conds.append(f"({' OR '.join(tl_conds)})")
            
        return " AND ".join(conds)

    # 4. DANH SÁCH TÙY CHỌN BỘ LỌC
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_khgui FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    dt_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_doitac FROM orders WHERE {build_where('dt')} AND ma_doitac IS NOT NULL ORDER BY 1").fetchall()]
    dv_opts = [r[0] for r in con.execute(f"SELECT DISTINCT ma_dv_viettel FROM orders WHERE {build_where('dv')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    
    # Khai báo các nhãn đúng như ảnh giao diện của bạn
    tl_opts = ["1000g - < 2000g", "500g - < 1000g", "< 500g", ">= 2000g"]

    # 5. GIAO DIỆN BỘ LỌC
    f_opr1, f_opr2, f_opr3, f_opr4, f_opr7 = st.columns(5)

    with f_opr1:
        st.date_input("NGÀY NHẬP MÁY", key="opr_date")
    with f_opr2:
        st.multiselect("MÃ KHÁCH HÀNG", kh_opts, key="opr_kh", placeholder="Tất cả")
    with f_opr3:
        st.multiselect("MÃ ĐỐI TÁC", dt_opts, key="opr_dt", placeholder="Tất cả")
    with f_opr4:
        st.multiselect("MÃ DỊCH VỤ", dv_opts, key="opr_dv", placeholder="Tất cả")
    with f_opr7:
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
