import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
# from datetime import datetime, date
import datetime
from datetime import date
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
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu failed</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu đúng giờ</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold;">Tỷ lệ thu thành công</th>
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
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu failed</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold; border-right: 1px solid #444;">Sản lượng thu đúng giờ</th>
                    <th style="padding: 9px 4px; text-align: center; font-weight: bold;">Tỷ lệ thu thành công</th>
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
    
    # 4. DANH SÁCH CHI NHÁNH & BƯU CỤC THỰC HIỆN
    st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:8px;">DANH SÁCH CHI NHÁNH & BƯU CỤC THU</div>', unsafe_allow_html=True)

    
    # 1. TRUY VẤN DỮ LIỆU CHI NHÁNH (tinh_nhan)
    cn_data_raw = con.execute(f"""
        SELECT 
            tinh_nhan AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_sl,
            COUNT(DISTINCT CASE 
                WHEN LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%sai%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%fail%'
                  OR CAST(danh_gia AS VARCHAR) IN ('0', 'false', 'FALSE')
                THEN ma_phieugui 
            END) AS sl_failed,
            COUNT(DISTINCT CASE 
                WHEN LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%pass%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%ok%'
                  OR CAST(danh_gia AS VARCHAR) IN ('1', 'true', 'TRUE')
                THEN ma_phieugui 
            END) AS sl_dung
        FROM orders 
        WHERE {where_sql_opr} AND tinh_nhan IS NOT NULL AND tinh_nhan != ''
        GROUP BY tinh_nhan 
        ORDER BY tinh_nhan ASC
    """).fetchall()
    
    # 2. TRUY VẤN DỮ LIỆU BƯU CỤC (ma_buucuc_goc + tinh_nhan)
    bc_data_raw = con.execute(f"""
        SELECT 
            ma_buucuc_goc AS bc, 
            tinh_nhan AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_sl,
            COUNT(DISTINCT CASE 
                WHEN LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%sai%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%fail%'
                  OR CAST(danh_gia AS VARCHAR) IN ('0', 'false', 'FALSE')
                THEN ma_phieugui 
            END) AS sl_failed,
            COUNT(DISTINCT CASE 
                WHEN LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%dung%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%đúng%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%pass%'
                  OR LOWER(CAST(danh_gia AS VARCHAR)) LIKE '%ok%'
                  OR CAST(danh_gia AS VARCHAR) IN ('1', 'true', 'TRUE')
                THEN ma_phieugui 
            END) AS sl_dung
        FROM orders 
        WHERE {where_sql_opr} AND tinh_nhan IS NOT NULL AND ma_buucuc_goc IS NOT NULL
        GROUP BY ma_buucuc_goc, tinh_nhan 
        ORDER BY ma_buucuc_goc ASC
    """).fetchall()
    
    # 3. RENDER HÀNG DỮ LIỆU CHI NHÁNH
    rows_cn_html = ""
    for item in cn_data_raw:
        cn_code = item[0]
        tong_sl = item[1] or 0
        sl_failed = item[2] or 0
        sl_dung = item[3] or 0
        ty_le_dung = (sl_dung / tong_sl * 100) if tong_sl > 0 else 0
    
        rows_cn_html += f"""<tr class="cn-row" data-cn="{cn_code}" onclick="filterBC('{cn_code}', this)">
    <td style="font-weight: bold; cursor: pointer;">{cn_code}</td>
    <td>{tong_sl:,.0f}</td>
    <td class="text-red">{sl_failed:,.0f}</td>
    <td>{sl_dung:,.0f}</td>
    <td style="font-weight: bold; color: #2e7d32;">{ty_le_dung:.1f}%</td>
    </tr>"""
    
    # 4. RENDER HÀNG DỮ LIỆU BƯU CỤC (Chi nhánh trước, Bưu cục sau)
    rows_bc_html = ""
    for item in bc_data_raw:
        bc_code = item[0]
        cn_code = item[1]
        tong_sl = item[2] or 0
        sl_failed = item[3] or 0
        sl_dung = item[4] or 0
        ty_le_dung = (sl_dung / tong_sl * 100) if tong_sl > 0 else 0
    
        rows_bc_html += f"""<tr class="bc-row" data-cn="{cn_code}">
    <td style="font-weight: bold;">{cn_code}</td>
    <td style="font-weight: bold;">{bc_code}</td>
    <td>{tong_sl:,.0f}</td>
    <td class="text-red">{sl_failed:,.0f}</td>
    <td>{sl_dung:,.0f}</td>
    <td style="font-weight: bold; color: #2e7d32;">{ty_le_dung:.1f}%</td>
    </tr>"""
    
    # 5. TẠO KHỐI HTML + JAVASCRIPT HIỂN THỊ
    interactive_tables_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
            margin: 0; padding: 0; background: transparent; 
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}
        .table-title {{
            font-size: 12px; font-weight: bold; color: #333; margin-bottom: 6px;
        }}
        .table-scroll {{
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid #d3d3d3;
            border-radius: 4px;
            background: #fff;
        }}
        table {{
            width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px;
        }}
        th {{
            position: sticky; top: 0; z-index: 10;
            background-color: #1e1e1e; color: #ffffff;
            text-align: center; padding: 8px 4px;
            border-bottom: 1px solid #444; border-right: 1px solid #444;
            font-weight: bold;
        }}
        td {{
            padding: 6px 4px; border-bottom: 1px solid #eee; border-right: 1px solid #eee;
            text-align: center; color: #111;
        }}
        tr.cn-row:hover {{
            background-color: #ffebee !important;
            cursor: pointer;
        }}
        tr.selected-cn {{
            background-color: #ffcdd2 !important;
        }}
        .text-red {{ color: #c62828; font-weight: bold; }}
        .btn-reset {{
            display: inline-block; padding: 2px 8px; font-size: 11px;
            background: #eee; border: 1px solid #ccc; border-radius: 3px;
            cursor: pointer; margin-left: 8px; font-weight: normal;
        }}
    </style>
    </head>
    <body>
    
    <div class="grid-container">
        <div>
            <div class="table-title">
                Bảng Chi Nhánh Thu <span style="font-weight:normal; color:#666;">(Bấm chọn dòng để lọc Bưu cục)</span>
                <span class="btn-reset" onclick="resetFilter()">Xóa lọc</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Chi nhánh</th>
                            <th>SL Thu</th>
                            <th>SL Thu Failed</th>
                            <th>SL Thu Đúng Giờ</th>
                            <th>Tỷ Lệ Thu Đúng Giờ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_cn_html if rows_cn_html else "<tr><td colspan='5'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    
        <div>
            <div class="table-title">
                Bưu Cục Thu <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span>
            </div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th>Chi nhánh</th>
                            <th>Bưu cục</th>
                            <th>SL Thu</th>
                            <th>SL Thu Failed</th>
                            <th>SL Thu Đúng Giờ</th>
                            <th>Tỷ Lệ Thu Đúng Giờ</th>
                        </tr>
                    </thead>
                    <tbody id="bc-tbody">
                        {rows_bc_html if rows_bc_html else "<tr><td colspan='6'>Không có dữ liệu</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function filterBC(cnCode, rowElem) {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            if (rowElem) rowElem.classList.add('selected-cn');
    
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                if (bcRows[j].getAttribute('data-cn') === cnCode) {{
                    bcRows[j].style.display = 'table-row';
                }} else {{
                    bcRows[j].style.display = 'none';
                }}
            }}
            document.getElementById('bc-title-status').innerText = '(Chi nhánh: ' + cnCode + ')';
        }}
    
        function resetFilter() {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) {{
                cnRows[i].classList.remove('selected-cn');
            }}
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                bcRows[j].style.display = 'table-row';
            }}
            document.getElementById('bc-title-status').innerText = '(Toàn Quốc)';
        }}
    </script>
    </body>
    </html>
    """
    
    components.html(textwrap.dedent(interactive_tables_html), height=410, scrolling=False)
    st.divider()

    # 5. BÁO CÁO MA TRẬN CHẤT LƯỢNG KHÂU THU
    st.markdown('<p class="section-red-title">MA TRẬN CHẤT LƯỢNG KHÂU THU (DRILL-DOWN DỮ LIỆU)</p>', unsafe_allow_html=True)

    # 1. TRUY VẤN DỮ LIỆU 7 NGÀY GẦN NHẤT (SẢN LƯỢNG)
    days_data_matrix_opr = con.execute(f"""
        SELECT DATE(time_nhap_may) as clean_date, COUNT(*) as sl 
        FROM orders 
        WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL 
        GROUP BY DATE(time_nhap_may) 
        ORDER BY clean_date DESC LIMIT 7
    """).fetchall()

    days_dict_matrix_opr = {row[0].strftime('%Y-%m-%d'): row[1] for row in days_data_matrix_opr}
    sorted_days_sql = sorted(list(days_dict_matrix_opr.keys()))
    sorted_days_display = [d.split('-')[2] + '/' + d.split('-')[1] for d in sorted_days_sql]
    while len(sorted_days_display) < 7:
        sorted_days_display.insert(0, "--/--")
        sorted_days_sql.insert(0, "1970-01-01")
    d_vals_matrix_opr = [days_dict_matrix_opr.get(d, 0) for d in sorted_days_sql]

    day_prev_tot = d_vals_matrix_opr[-2]
    day_cur_tot = d_vals_matrix_opr[-1]
    dod_tot = ((day_cur_tot - day_prev_tot) / day_prev_tot * 100) if day_prev_tot > 0 else 0.0

    # 2. XÁC ĐỊNH DANH SÁCH 5 TUẦN VÀ 2 THÁNG
    weeks_list = con.execute(f"""
        SELECT DISTINCT STRFTIME(DATE(time_nhap_may), '%W') as wk
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL
        ORDER BY wk DESC LIMIT 5
    """).fetchall()
    sorted_weeks = sorted([r[0] for r in weeks_list])
    while len(sorted_weeks) < 5: sorted_weeks.insert(0, "00")

    months_list = con.execute(f"""
        SELECT DISTINCT STRFTIME(DATE(time_nhap_may), '%m') as m
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL
        ORDER BY m DESC LIMIT 2
    """).fetchall()
    
    raw_months = [r[0] for r in months_list]
    if len(raw_months) == 1:
        cur_m_int = int(raw_months[0])
        prev_m_int = 12 if cur_m_int == 1 else cur_m_int - 1
        sorted_months = [f"{prev_m_int:02d}", raw_months[0]]
    else:
        sorted_months = sorted(raw_months)
        while len(sorted_months) < 2: sorted_months.insert(0, "00")

    # 3. TRUY VẤN TỔNG SẢN LƯỢNG CHO 2 THÁNG & TUẦN
    m_prev_matrix_opr = con.execute(f"""
        SELECT COUNT(*) FROM orders 
        WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL 
        AND STRFTIME(DATE(time_nhap_may), '%m') = '{sorted_months[0]}'
    """).fetchone()[0]

    m_current_matrix_opr = con.execute(f"""
        SELECT COUNT(*) FROM orders 
        WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL 
        AND STRFTIME(DATE(time_nhap_may), '%m') = '{sorted_months[1]}'
    """).fetchone()[0]

    mom_tot = ((m_current_matrix_opr - m_prev_matrix_opr) / m_prev_matrix_opr * 100) if m_prev_matrix_opr > 0 else 0.0

    weeks_data_sql = con.execute(f"""
        SELECT STRFTIME(DATE(time_nhap_may), '%W') as wk, COUNT(*) as sl
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL
        GROUP BY wk
    """).fetchall()
    weeks_dict_tot = {row[0]: row[1] for row in weeks_data_sql}
    w_vals_matrix_opr = [weeks_dict_tot.get(w, 0) for w in sorted_weeks]

    wk_prev_tot = w_vals_matrix_opr[-2]
    wk_cur_tot = w_vals_matrix_opr[-1]
    wow_tot = ((wk_cur_tot - wk_prev_tot) / wk_prev_tot * 100) if wk_prev_tot > 0 else 0.0

    # 4. TRUY VẤN TỶ LỆ TỔNG THEO NGÀY CHO 2 DÒNG DƯỚI (Đã đổi sang time_thulan2 & time_thulan3)
    dung_day_tot = con.execute(f"""
        SELECT DATE(time_nhap_may), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung'
        GROUP BY DATE(time_nhap_may)
    """).fetchall()
    dung_day_dict = {str(r[0]): r[1] for r in dung_day_tot}

    dung1_day_tot = con.execute(f"""
        SELECT DATE(time_nhap_may), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung' AND time_thulan2 IS NULL AND time_thulan3 IS NULL
        GROUP BY DATE(time_nhap_may)
    """).fetchall()
    dung1_day_dict = {str(r[0]): r[1] for r in dung1_day_tot}

    dung_week_tot = con.execute(f"""
        SELECT STRFTIME(DATE(time_nhap_may), '%W'), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung'
        GROUP BY STRFTIME(DATE(time_nhap_may), '%W')
    """).fetchall()
    dung_w_dict = {r[0]: r[1] for r in dung_week_tot}

    dung1_week_tot = con.execute(f"""
        SELECT STRFTIME(DATE(time_nhap_may), '%W'), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung' AND time_thulan2 IS NULL AND time_thulan3 IS NULL
        GROUP BY STRFTIME(DATE(time_nhap_may), '%W')
    """).fetchall()
    dung1_w_dict = {r[0]: r[1] for r in dung1_week_tot}

    dung_m_tot = con.execute(f"""
        SELECT STRFTIME(DATE(time_nhap_may), '%m'), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung'
        GROUP BY STRFTIME(DATE(time_nhap_may), '%m')
    """).fetchall()
    dung_m_dict = {r[0]: r[1] for r in dung_m_tot}

    dung1_m_tot = con.execute(f"""
        SELECT STRFTIME(DATE(time_nhap_may), '%m'), COUNT(*) 
        FROM orders WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL AND danh_gia = 'Dung' AND time_thulan2 IS NULL AND time_thulan3 IS NULL
        GROUP BY STRFTIME(DATE(time_nhap_may), '%m')
    """).fetchall()
    dung1_m_dict = {r[0]: r[1] for r in dung1_m_tot}

    # Tính mảng hiển thị % cho dòng tổng
    rate_dung_days = [(dung_day_dict.get(d, 0) / days_dict_matrix_opr.get(d, 1) * 100) if days_dict_matrix_opr.get(d, 0) > 0 else 0.0 for d in sorted_days_sql]
    rate_dung1_days = [(dung1_day_dict.get(d, 0) / days_dict_matrix_opr.get(d, 1) * 100) if days_dict_matrix_opr.get(d, 0) > 0 else 0.0 for d in sorted_days_sql]

    rate_dung_weeks = [(dung_w_dict.get(w, 0) / weeks_dict_tot.get(w, 1) * 100) if weeks_dict_tot.get(w, 0) > 0 else 0.0 for w in sorted_weeks]
    rate_dung1_weeks = [(dung1_w_dict.get(w, 0) / weeks_dict_tot.get(w, 1) * 100) if weeks_dict_tot.get(w, 0) > 0 else 0.0 for w in sorted_weeks]

    m_prev_tot_sl = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr} AND STRFTIME(DATE(time_nhap_may), '%m') = '{sorted_months[0]}'").fetchone()[0]
    m_curr_tot_sl = con.execute(f"SELECT COUNT(*) FROM orders WHERE {where_sql_opr} AND STRFTIME(DATE(time_nhap_may), '%m') = '{sorted_months[1]}'").fetchone()[0]

    rate_dung_m_prev = (dung_m_dict.get(sorted_months[0], 0) / m_prev_tot_sl * 100) if m_prev_tot_sl > 0 else 0.0
    rate_dung_m_curr = (dung_m_dict.get(sorted_months[1], 0) / m_curr_tot_sl * 100) if m_curr_tot_sl > 0 else 0.0

    rate_dung1_m_prev = (dung1_m_dict.get(sorted_months[0], 0) / m_prev_tot_sl * 100) if m_prev_tot_sl > 0 else 0.0
    rate_dung1_m_curr = (dung1_m_dict.get(sorted_months[1], 0) / m_curr_tot_sl * 100) if m_curr_tot_sl > 0 else 0.0

    # 5. TRUY VẤN DRILL-DOWN CÂY DỮ LIỆU (CHI NHÁNH -> BƯU CỤC)
    tree_raw_data = con.execute(f"""
        SELECT 
            COALESCE(tinh_nhan, 'Khác') as tinh,
            COALESCE(ma_buucuc_goc, 'Khác') as bc,
            CAST(DATE(time_nhap_may) AS VARCHAR) as ngay,
            STRFTIME(DATE(time_nhap_may), '%W') as tuan,
            STRFTIME(DATE(time_nhap_may), '%m') as thang,
            COUNT(*) as sl,
            SUM(CASE WHEN danh_gia = 'Dung' THEN 1 ELSE 0 END) as sl_dung,
            SUM(CASE WHEN danh_gia = 'Dung' AND time_thulan2 IS NULL AND time_thulan3 IS NULL THEN 1 ELSE 0 END) as sl_dung1
        FROM orders 
        WHERE {where_sql_opr} AND time_nhap_may IS NOT NULL
        GROUP BY tinh_nhan, ma_buucuc_goc, DATE(time_nhap_may), STRFTIME(DATE(time_nhap_may), '%W'), STRFTIME(DATE(time_nhap_may), '%m')
    """).fetchall()

    tree_struct_opr = {}
    for tinh, bc, ngay, tuan, thang, sl, sl_dung, sl_dung1 in tree_raw_data:
        if tinh not in tree_struct_opr:
            tree_struct_opr[tinh] = {
                'days': {d: 0 for d in sorted_days_sql},
                'weeks': {w: 0 for w in sorted_weeks},
                'months': {m: 0 for m in sorted_months},
                'days_dung': {d: 0 for d in sorted_days_sql},
                'weeks_dung': {w: 0 for w in sorted_weeks},
                'months_dung': {m: 0 for m in sorted_months},
                'days_dung1': {d: 0 for d in sorted_days_sql},
                'weeks_dung1': {w: 0 for w in sorted_weeks},
                'months_dung1': {m: 0 for m in sorted_months},
                'bcs': {}
            }
        if ngay in tree_struct_opr[tinh]['days']: 
            tree_struct_opr[tinh]['days'][ngay] += sl
            tree_struct_opr[tinh]['days_dung'][ngay] += sl_dung
            tree_struct_opr[tinh]['days_dung1'][ngay] += sl_dung1
        if tuan in tree_struct_opr[tinh]['weeks']: 
            tree_struct_opr[tinh]['weeks'][tuan] += sl
            tree_struct_opr[tinh]['weeks_dung'][tuan] += sl_dung
            tree_struct_opr[tinh]['weeks_dung1'][tuan] += sl_dung1
        if thang in tree_struct_opr[tinh]['months']: 
            tree_struct_opr[tinh]['months'][thang] += sl
            tree_struct_opr[tinh]['months_dung'][thang] += sl_dung
            tree_struct_opr[tinh]['months_dung1'][thang] += sl_dung1

        if bc not in tree_struct_opr[tinh]['bcs']:
            tree_struct_opr[tinh]['bcs'][bc] = {
                'days': {d: 0 for d in sorted_days_sql},
                'weeks': {w: 0 for w in sorted_weeks},
                'months': {m: 0 for m in sorted_months},
                'days_dung': {d: 0 for d in sorted_days_sql},
                'weeks_dung': {w: 0 for w in sorted_weeks},
                'months_dung': {m: 0 for m in sorted_months},
                'days_dung1': {d: 0 for d in sorted_days_sql},
                'weeks_dung1': {w: 0 for w in sorted_weeks},
                'months_dung1': {m: 0 for m in sorted_months}
            }
        bc_node = tree_struct_opr[tinh]['bcs'][bc]
        if ngay in bc_node['days']: 
            bc_node['days'][ngay] += sl
            bc_node['days_dung'][ngay] += sl_dung
            bc_node['days_dung1'][ngay] += sl_dung1
        if tuan in bc_node['weeks']: 
            bc_node['weeks'][tuan] += sl
            bc_node['weeks_dung'][tuan] += sl_dung
            bc_node['weeks_dung1'][tuan] += sl_dung1
        if thang in bc_node['months']: 
            bc_node['months'][thang] += sl
            bc_node['months_dung'][thang] += sl_dung
            bc_node['months_dung1'][thang] += sl_dung1

    # 6. RENDER HÀNG DRILL DOWN
    matrix_rows_opr_html = ""
    for idx_tinh, (tinh_name, t_data) in enumerate(tree_struct_opr.items()):
        tinh_clean_id = f"opr_tinh_{idx_tinh}"
        
        tinh_day_tds = "".join([f"<td>{t_data['days'].get(d, 0):,.0f}</td>" for d in sorted_days_sql])
        tinh_week_tds = "".join([f"<td>{t_data['weeks'].get(w, 0):,.0f}</td>" for w in sorted_weeks])
        tinh_m1 = t_data['months'].get(sorted_months[0], 0)
        tinh_m = t_data['months'].get(sorted_months[1], 0)
        
        day_prev_tinh = t_data['days'].get(sorted_days_sql[-2], 0)
        day_cur_tinh = t_data['days'].get(sorted_days_sql[-1], 0)
        dod_tinh = ((day_cur_tinh - day_prev_tinh) / day_prev_tinh * 100) if day_prev_tinh > 0 else 0.0

        wk_prev_tinh = t_data['weeks'].get(sorted_weeks[-2], 0)
        wk_cur_tinh = t_data['weeks'].get(sorted_weeks[-1], 0)
        wow_tinh = ((wk_cur_tinh - wk_prev_tinh) / wk_prev_tinh * 100) if wk_prev_tinh > 0 else 0.0
        mom_tinh = ((tinh_m - tinh_m1) / tinh_m1 * 100) if tinh_m1 > 0 else 0.0

        # Render Chi nhánh
        matrix_rows_opr_html += f"""
        <tr class="sub-row-1 group_root_opr" style="display:none; background-color: #ffffff; color: #1565c0; font-weight:600;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Chi nhánh thu: <b>{tinh_name}</b></td>
            {tinh_day_tds}<td class="{ 'text-green' if dod_tinh>=0 else 'text-red' }">{dod_tinh:+.2f}%</td>
            {tinh_week_tds}<td class="{ 'text-green' if wow_tinh>=0 else 'text-red' }">{wow_tinh:+.2f}%</td>
            <td>{tinh_m1:,.0f}</td><td>{tinh_m:,.0f}</td><td class="{ 'text-green' if mom_tinh>=0 else 'text-red' }">{mom_tinh:+.2f}%</td>
        </tr>
        """

        # Tính tỷ lệ Chi nhánh (Đúng giờ & Đúng giờ lần 1)
        tinh_dung_days_tds = "".join([f"<td>{(t_data['days_dung'].get(d,0)/t_data['days'].get(d,1)*100 if t_data['days'].get(d,0)>0 else 0):.2f}%</td>" for d in sorted_days_sql])
        tinh_dung_weeks_tds = "".join([f"<td>{(t_data['weeks_dung'].get(w,0)/t_data['weeks'].get(w,1)*100 if t_data['weeks'].get(w,0)>0 else 0):.2f}%</td>" for w in sorted_weeks])
        tinh_dung_m1 = (t_data['months_dung'].get(sorted_months[0], 0) / tinh_m1 * 100) if tinh_m1 > 0 else 0.0
        tinh_dung_m = (t_data['months_dung'].get(sorted_months[1], 0) / tinh_m * 100) if tinh_m > 0 else 0.0

        matrix_rows_opr_html += f"""
        <tr class="sub-row-1 {tinh_clean_id}" style="display:none; background-color: #fcfcfc; color: #333; font-style: italic;">
            <td style="padding-left: 35px;">↳ % Đúng giờ ({tinh_name})</td>
            {tinh_dung_days_tds}<td>-</td>
            {tinh_dung_weeks_tds}<td>-</td>
            <td>{tinh_dung_m1:.2f}%</td><td>{tinh_dung_m:.2f}%</td><td>-</td>
        </tr>
        """

        tinh_dung1_days_tds = "".join([f"<td>{(t_data['days_dung1'].get(d,0)/t_data['days'].get(d,1)*100 if t_data['days'].get(d,0)>0 else 0):.2f}%</td>" for d in sorted_days_sql])
        tinh_dung1_weeks_tds = "".join([f"<td>{(t_data['weeks_dung1'].get(w,0)/t_data['weeks'].get(w,1)*100 if t_data['weeks'].get(w,0)>0 else 0):.2f}%</td>" for w in sorted_weeks])
        tinh_dung1_m1 = (t_data['months_dung1'].get(sorted_months[0], 0) / tinh_m1 * 100) if tinh_m1 > 0 else 0.0
        tinh_dung1_m = (t_data['months_dung1'].get(sorted_months[1], 0) / tinh_m * 100) if tinh_m > 0 else 0.0

        matrix_rows_opr_html += f"""
        <tr class="sub-row-1 {tinh_clean_id}" style="display:none; background-color: #fcfcfc; color: #333; font-style: italic;">
            <td style="padding-left: 35px;">↳ % Đúng giờ lần 1 ({tinh_name})</td>
            {tinh_dung1_days_tds}<td>-</td>
            {tinh_dung1_weeks_tds}<td>-</td>
            <td>{tinh_dung1_m1:.2f}%</td><td>{tinh_dung1_m:.2f}%</td><td>-</td>
        </tr>
        """

        # Bưu cục cấp 2
        for bc_name, bc_data in t_data['bcs'].items():
            bc_day_tds = "".join([f"<td>{bc_data['days'].get(d, 0):,.0f}</td>" for d in sorted_days_sql])
            bc_week_tds = "".join([f"<td>{bc_data['weeks'].get(w, 0):,.0f}</td>" for w in sorted_weeks])
            bc_m1 = bc_data['months'].get(sorted_months[0], 0)
            bc_m = bc_data['months'].get(sorted_months[1], 0)

            day_prev_bc = bc_data['days'].get(sorted_days_sql[-2], 0)
            day_cur_bc = bc_data['days'].get(sorted_days_sql[-1], 0)
            dod_bc = ((day_cur_bc - day_prev_bc) / day_prev_bc * 100) if day_prev_bc > 0 else 0.0

            wk_prev_bc = bc_data['weeks'].get(sorted_weeks[-2], 0)
            wk_cur_bc = bc_data['weeks'].get(sorted_weeks[-1], 0)
            wow_bc = ((wk_cur_bc - wk_prev_bc) / wk_prev_bc * 100) if wk_prev_bc > 0 else 0.0
            mom_bc = ((bc_m - bc_m1) / bc_m1 * 100) if bc_m1 > 0 else 0.0

            matrix_rows_opr_html += f"""
            <tr class="sub-row-2 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                <td style="padding-left: 40px;">• Bưu cục thu: <b>{bc_name}</b></td>
                {bc_day_tds}<td class="{ 'text-green' if dod_bc>=0 else 'text-red' }">{dod_bc:+.2f}%</td>
                {bc_week_tds}<td class="{ 'text-green' if wow_bc>=0 else 'text-red' }">{wow_bc:+.2f}%</td>
                <td>{bc_m1:,.0f}</td><td>{bc_m:,.0f}</td><td class="{ 'text-green' if mom_bc>=0 else 'text-red' }">{mom_bc:+.2f}%</td>
            </tr>
            """

    # 7. KHỐI HTML BẢNG MA TRẬN TỔNG HỢP
    matrix_opr_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }}
        .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; background-color: #ffffff; color: #111111; border: 1px solid #222222; }}
        .matrix-table th {{ background-color: #222222; color: #ffffff; text-align: center; padding: 7px 4px; border: 1px solid #444444; font-weight: 600; font-size: 11px; }}
        .matrix-table td {{ padding: 6px 8px; border: 1px solid #dddddd; vertical-align: middle; text-align: right; }}
        .matrix-table td:first-child {{ text-align: left; }}
        .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
        .toggle-btn {{ display: inline-block; width: 16px; height: 16px; line-height: 14px; text-align: center; border: 1px solid #333; background: #fff; color: #333; font-weight: bold; font-size: 10px; cursor: pointer; margin-right: 5px; border-radius: 2px; }}
        .text-green {{ color: #2e7d32; font-weight: bold; }}
        .text-red {{ color: #c62828; font-weight: bold; }}
    </style>
    </head>
    <body>

    <table class="matrix-table">
        <thead>
            <tr>
                <th rowspan="2" style="width: 30%;">Chỉ tiêu khâu Thu</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days_display[0]}</th><th>{sorted_days_display[1]}</th><th>{sorted_days_display[2]}</th><th>{sorted_days_display[3]}</th><th>{sorted_days_display[4]}</th><th>{sorted_days_display[5]}</th><th>{sorted_days_display[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W{sorted_weeks[0]}</th><th>W{sorted_weeks[1]}</th><th>W{sorted_weeks[2]}</th><th>W{sorted_weeks[3]}</th><th>W{sorted_weeks[4]}</th><th style="color: #ff5252;">WoW</th>
                <th>M-{sorted_months[0]}</th><th>M-{sorted_months[1]}</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_root_opr', event, 'btn_root_opr')">
                <td><span class="toggle-btn" id="btn_root_opr">[+]</span> <b>Sản lượng phải thu</b></td>
                <td>{d_vals_matrix_opr[0]:,.0f}</td><td>{d_vals_matrix_opr[1]:,.0f}</td><td>{d_vals_matrix_opr[2]:,.0f}</td><td>{d_vals_matrix_opr[3]:,.0f}</td><td>{d_vals_matrix_opr[4]:,.0f}</td><td>{d_vals_matrix_opr[5]:,.0f}</td><td><b>{d_vals_matrix_opr[6]:,.0f}</b></td><td class="{ 'text-green' if dod_tot>=0 else 'text-red' }">{dod_tot:+.2f}%</td>
                <td>{w_vals_matrix_opr[0]:,.0f}</td><td>{w_vals_matrix_opr[1]:,.0f}</td><td>{w_vals_matrix_opr[2]:,.0f}</td><td>{w_vals_matrix_opr[3]:,.0f}</td><td><b>{w_vals_matrix_opr[4]:,.0f}</b></td><td class="{ 'text-green' if wow_tot>=0 else 'text-red' }">{wow_tot:+.2f}%</td>
                <td>{m_prev_matrix_opr:,.0f}</td><td><b>{m_current_matrix_opr:,.0f}</b></td><td class="{ 'text-green' if mom_tot>=0 else 'text-red' }">{mom_tot:+.2f}%</td>
            </tr>

            {matrix_rows_opr_html}

            <tr>
                <td style="font-weight: bold;">% Thu thành công đúng giờ</td>
                {"".join([f"<td>{v:.2f}%</td>" for v in rate_dung_days])}<td>-</td>
                {"".join([f"<td>{v:.2f}%</td>" for v in rate_dung_weeks])}<td>-</td>
                <td>{rate_dung_m_prev:.2f}%</td><td>{rate_dung_m_curr:.2f}%</td><td>-</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Thu thành công đúng giờ lần 1</td>
                {"".join([f"<td>{v:.2f}%</td>" for v in rate_dung1_days])}<td>-</td>
                {"".join([f"<td>{v:.2f}%</td>" for v in rate_dung1_weeks])}<td>-</td>
                <td>{rate_dung1_m_prev:.2f}%</td><td>{rate_dung1_m_curr:.2f}%</td><td>-</td>
            </tr>
        </tbody>
    </table>

    <script>
        function toggleRow(className, event, btnId) {{
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {{
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }}
            if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
        }}
    </script>
    </body>
    </html>
    """

    components.html(matrix_opr_html, height=450, scrolling=True)
