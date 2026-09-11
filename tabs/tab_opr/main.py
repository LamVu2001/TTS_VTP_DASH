import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from datetime import datetime, date
import textwrap

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
        
        # Lọc ngày sử dụng time_nhap_may
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

        # Lọc Bưu cục phát
        if exclude != "bc" and st.session_state.opr_bc:
            c = sql_in_clause("ma_buucuc_goc", st.session_state.opr_bc)
            if c: conds.append(c)
            
        # Lọc Mã dịch vụ
        if exclude != "dv" and st.session_state.opr_dv:
            c = sql_in_clause("ma_dv_viettel", st.session_state.opr_dv)
            if c: conds.append(c)
            
        # Lọc Trọng lượng trực tiếp từ cột nhom_trong_luong
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

    # 5. GIAO DIỆN BỘ LỌC (6 CỘT DÀN NGANG)
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

    # 6. TÍNH TOÁN DỮ LIỆU CÁC THẺ KPI
    where_sql_opr = build_where()
    
    try:
        query_kpi = f"""
            SELECT 
                COUNT(DISTINCT ma_phieugui) AS tong_sl,
                COUNT(DISTINCT CASE 
                    WHEN LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('dung', 'đúng', '1', 'true', 'ok', 'pass') 
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%'
                    THEN ma_phieugui 
                END) AS sl_dung,
                COUNT(DISTINCT CASE 
                    WHEN LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('sai', '0', 'false', 'fail', 'not ok') 
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%sai%'
                    THEN ma_phieugui 
                END) AS sl_sai,
                COUNT(DISTINCT CASE 
                    WHEN (LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('dung', 'đúng', '1', 'true', 'ok', 'pass') 
                          OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                          OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%') 
                         AND (time_thulan2 IS NULL OR CAST(time_thulan2 AS VARCHAR) = '')
                         AND (time_thulan3 IS NULL OR CAST(time_thulan3 AS VARCHAR) = '')
                    THEN ma_phieugui 
                END) AS sl_dung_lan1
            FROM orders 
            WHERE {where_sql_opr}
        """
        res = con.execute(query_kpi).fetchone()
        
        tong_sl = res[0] or 0
        sl_dung = res[1] or 0
        sl_sai = res[2] or 0
        sl_dung_lan1 = res[3] or 0

        if sl_dung == 0 and sl_sai > 0 and tong_sl > sl_sai:
            sl_dung = tong_sl - sl_sai

        ty_le_dung_gio = (sl_dung / tong_sl * 100) if tong_sl > 0 else 0.0
        ty_le_dung_lan1 = (sl_dung_lan1 / tong_sl * 100) if tong_sl > 0 else 0.0
        ty_le_failed = (sl_sai / tong_sl * 100) if tong_sl > 0 else 0.0

    except Exception:
        tong_sl = sl_dung = sl_sai = 0
        ty_le_dung_gio = ty_le_dung_lan1 = ty_le_failed = 0.0

    st.write("")

    # 7. CSS & METRIC CARDS (DÀN NGANG 6 CỘT - ĐÃ BỎ ĐỌAN SUBTITLE XANH/ĐỎ)
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 16px 8px;
            text-align: center;
            border: 1px solid #e0e0e0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .metric-title { font-size: 11px; font-weight: bold; color: #555; text-transform: uppercase; white-space: nowrap; }
        .metric-value { font-size: 20px; font-weight: bold; color: #111; margin-top: 6px; }
        </style>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG THU</div><div class="metric-value">{tong_sl:,.0f}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG THU ĐÚNG SLA</div><div class="metric-value">{sl_dung:,.0f}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG THU SAI SLA</div><div class="metric-value">{sl_sai:,.0f}</div></div>', unsafe_allow_html=True)
    with k4: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG SLA</div><div class="metric-value">{ty_le_dung_gio:.1f}%</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ THU ĐÚNG SLA LẦN ĐẦU</div><div class="metric-value">{ty_le_dung_lan1:.1f}%</div></div>', unsafe_allow_html=True)
    with k6:
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ THU SAI SLA</div><div class="metric-value">{ty_le_failed:.1f}%</div></div>', unsafe_allow_html=True)

    st.write("")
    
    # 3. BIỂU ĐỒ XU HƯỚNG & TOP 10 DÀN NGANG
    c_opr_left, c_opr_right = st.columns([1.2, 1])

    with c_opr_left:
        # 1. TIÊU ĐỀ
        st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:8px;">XU HƯỚNG SẢN LƯỢNG VÀ TỶ LỆ THU ĐÚNG SLA</div>', unsafe_allow_html=True)
    
        # 2. BỘ CHỌN TIME VIEW (TRÊN BIỂU ĐỒ)
        view_type = st.radio("", ["Ngày", "Tuần", "Tháng"], horizontal=True, key="opr_trend_view", label_visibility="collapsed")
    
        # 3. XỬ LÝ GOM NHÓM THỜI GIAN THEO DUCKDB chuẩn
        if view_type == "Ngày":
            time_group_sql = "STRFTIME('%d/%m', time_nhap_may)"
            order_sql = "MIN(CAST(time_nhap_may AS DATE))"
        elif view_type == "Tuần":
            # DuckDB: Trừ đi thứ trong tuần để lùi về Chủ Nhật (Chủ Nhật = 0)
            # dayofweek() trong DuckDB: 0 (Chủ Nhật) -> 6 (Thứ 7)
            time_group_sql = "STRFTIME('%d/%m', CAST(time_nhap_may AS DATE) - INTERVAL (DAYOFWEEK(CAST(time_nhap_may AS DATE))) DAY)"
            order_sql = "MIN(CAST(time_nhap_may AS DATE))"
        else: # Tháng
            time_group_sql = "STRFTIME('%m/%Y', time_nhap_may)"
            order_sql = "MIN(CAST(time_nhap_may AS DATE))"
    
        # 4. TRUY VẤN DỮ LIỆU DUCKDB
        query_trend = f"""
            SELECT 
                {time_group_sql} AS time_label,
                COUNT(DISTINCT ma_phieugui) AS tong_sl,
                COUNT(DISTINCT CASE 
                    WHEN LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('dung', 'đúng', '1', 'true', 'ok', 'pass') 
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%'
                    THEN ma_phieugui 
                END) AS sl_dung,
                {order_sql} AS sort_date
            FROM orders 
            WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL
            GROUP BY 1
            ORDER BY sort_date ASC
        """
        df_trend = con.execute(query_trend).df()
    
        if not df_trend.empty:
            df_trend['ty_le_dung'] = (df_trend['sl_dung'] / df_trend['tong_sl'] * 100).round(1)
    
            fig = make_subplots(specs=[[{"secondary_y": True}]])
    
            # Cột: Sản lượng thu
            fig.add_trace(
                go.Bar(
                    x=df_trend['time_label'],
                    y=df_trend['tong_sl'],
                    name="Sản lượng thu",
                    marker_color="#b0bec5",
                    opacity=0.65
                ),
                secondary_y=False,
            )
    
            # Đường: Tỷ lệ thu đúng SLA (%) - Luôn show số % trên đỉnh chấm
            fig.add_trace(
                go.Scatter(
                    x=df_trend['time_label'],
                    y=df_trend['ty_le_dung'],
                    name="Tỷ lệ thu đúng SLA (%)",
                    mode="lines+markers+text",
                    line=dict(color="#c62828", width=3),
                    marker=dict(size=6, color="#c62828"),
                    text=[f"{v:.1f}%" for v in df_trend['ty_le_dung']],
                    textposition="top center",
                    textfont=dict(size=10, color="#c62828")
                ),
                secondary_y=True,
            )
    
            # Cấu hình Layout: Đẩy Legend xuống y=-0.45 để không bị đè vào nhãn Trục X
            fig.update_layout(
                margin=dict(l=10, r=10, t=25, b=60),
                height=340,
                hovermode="x unified",
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.30, 
                    xanchor="center", 
                    x=0.5
                ),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
    
            fig.update_xaxes(showgrid=False, type='category', tickangle=-90)
            fig.update_yaxes(title_text="Sản lượng", secondary_y=False, showgrid=True, gridcolor="#eee")
            fig.update_yaxes(title_text="Tỷ lệ (%)", secondary_y=True, showgrid=False, range=[0, 115])
    
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Không có dữ liệu xu hướng.")

    with c_opr_right:
        # 1. TIÊU ĐỀ
        st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:10px;">TOP 10 KHÁCH HÀNG CÓ SẢN LƯỢNG THU FAILED CAO NHẤT</div>', unsafe_allow_html=True)
    
        # 2. TRUY VẤN DỮ LIỆU
        query_top_failed = f"""
            SELECT 
                ma_khgui,
                COUNT(DISTINCT ma_phieugui) AS tong_sl,
                COUNT(DISTINCT CASE 
                    WHEN LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('sai', '0', 'false', 'fail', 'not ok') 
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%sai%'
                    THEN ma_phieugui 
                END) AS sl_failed,
                COUNT(DISTINCT CASE 
                    WHEN LOWER(TRIM(CAST(danh_gia AS VARCHAR))) IN ('dung', 'đúng', '1', 'true', 'ok', 'pass') 
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                      OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%'
                    THEN ma_phieugui 
                END) AS sl_dung
            FROM orders 
            WHERE {where_sql_opr} AND ma_khgui IS NOT NULL AND ma_khgui != ''
            GROUP BY 1
            ORDER BY sl_failed DESC, tong_sl DESC
            LIMIT 10
        """
        
        df_top_failed = con.execute(query_top_failed).df()
    
        if not df_top_failed.empty:
            rows_html = ""
            for _, row in df_top_failed.iterrows():
                # Tính tỷ lệ thu thành công (%)
                ty_le_thanh_cong = (row['sl_dung'] / row['tong_sl'] * 100) if row['tong_sl'] > 0 else 0
                
                rows_html += f"""<tr style="border-bottom: 1px solid #e0e0e0;">
    <td style="padding: 7px 4px; font-weight: bold; text-align: center; border-right: 1px solid #eee;">{row['ma_khgui']}</td>
    <td style="padding: 7px 4px; font-weight: bold; text-align: center; border-right: 1px solid #eee;">{row['tong_sl']:,.0f}</td>
    <td style="padding: 7px 4px; font-weight: bold; text-align: center; color: #c62828; border-right: 1px solid #eee;">{row['sl_failed']:,.0f}</td>
    <td style="padding: 7px 4px; font-weight: bold; text-align: center; border-right: 1px solid #eee;">{row['sl_dung']:,.0f}</td>
    <td style="padding: 7px 4px; font-weight: bold; text-align: center; color: #2e7d32;">{ty_le_thanh_cong:.1f}%</td>
    </tr>"""
    
            # Header nền đen (#1e1e1e), chữ trắng, đổi tên cột cuối thành Tỷ Lệ Thành Công
            raw_table_html = f"""
    <div style="border: 1px solid #ccc; border-radius: 6px; overflow: hidden;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #1e1e1e; color: #ffffff;">
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Mã KH</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu Failed SLA</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu Đúng Giờ</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold;">Tỷ Lệ Thành Công</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
            st.markdown(textwrap.dedent(raw_table_html), unsafe_allow_html=True)
        else:
            no_data_html = """
    <div style="border: 1px solid #ccc; border-radius: 6px; overflow: hidden;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; font-family: sans-serif;">
            <thead>
                <tr style="background-color: #1e1e1e; color: #ffffff;">
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Mã KH</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">SL Thu</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Failed SLA</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Đúng Giờ</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold;">Tỷ Lệ Thành Công</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="5" style="padding: 15px; text-align: center; color: #666;">Không có dữ liệu</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
            st.markdown(textwrap.dedent(no_data_html), unsafe_allow_html=True)

    st.divider()
