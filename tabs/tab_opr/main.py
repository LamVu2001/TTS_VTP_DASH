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

    # MA TRẬN VẬN HÀNH
    st.subheader("📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH (OPR)")

    try:
        # Sửa lại thành where_sql_opr cho đúng ngữ cảnh file OPR
        base_where = f"WHERE {where_sql_opr} AND tg_ptc IS NOT NULL" if 'where_sql_opr' in locals() and where_sql_opr else "WHERE tg_ptc IS NOT NULL"
    
        # ==========================================
        # 1. XÁC ĐỊNH MỐC THỜI GIAN THEO FILTER (MAX DATE)
        # ==========================================
        max_date_df = con.execute(f"SELECT MAX(CAST(tg_ptc AS DATE)) as max_dt FROM orders {base_where}").fetchdf()
        
        if max_date_df is not None and not max_date_df.empty and max_date_df["max_dt"].iloc[0] is not None:
            max_dt = max_date_df["max_dt"].iloc[0]
        else:
            max_dt = con.execute("SELECT MAX(CAST(tg_ptc AS DATE)) FROM orders WHERE tg_ptc IS NOT NULL").fetchone()[0]
    
        # A. 7 ngày gần nhất (tính lùi từ max_dt)
        days_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as dt, 
                STRFTIME(CAST(tg_ptc AS DATE), '%d/%m') as dt_label
            FROM orders 
            {base_where} AND CAST(tg_ptc AS DATE) <= '{max_dt}'
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 7
        """).fetchdf()
    
        day_cols = days_df["dt"].tolist()[::-1] if days_df is not None and not days_df.empty else []
        day_labels = days_df["dt_label"].tolist()[::-1] if days_df is not None and not days_df.empty else []
    
        # B. 5 tuần gần nhất (tính lùi từ max_dt)
        weeks_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as min_date,
                'W' || STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%W') as week_label
            FROM orders 
            {base_where} AND CAST(tg_ptc AS DATE) <= '{max_dt}'
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 5
        """).fetchdf()
    
        week_cols = weeks_df["min_date"].tolist()[::-1] if weeks_df is not None and not weeks_df.empty else []
        week_labels = weeks_df["week_label"].tolist()[::-1] if weeks_df is not None and not weeks_df.empty else []
    
        # C. Tháng M (Tháng của Max Date) và Tháng M-1 (Tháng liền trước)
        m1_key = con.execute(f"SELECT STRFTIME(CAST('{max_dt}' AS DATE), '%Y-%m')").fetchone()[0] 
        m0_key = con.execute(f"SELECT STRFTIME(CAST('{max_dt}' AS DATE) - INTERVAL 1 MONTH, '%Y-%m')").fetchone()[0] 
    
        month_cols = [m0_key, m1_key]
        month_labels = [f"M-{m0_key.split('-')[1]}", f"M-{m1_key.split('-')[1]}"]
    
        # ==========================================
        # 2. ĐIỀU KIỆN TÍNH ODR VÀ PTC_1
        # ==========================================
        sql_ptc1_expr = "CAST(PTC_1 AS VARCHAR) IN ('1', '1.0', 'true', 'TRUE')"
        sql_lydo_l1_expr = """
            CAST(ly_do_giao_hang_lan_1 AS VARCHAR) IN (
                'Khách hàng hẹn lại ngày giao',
                'Khách hàng đổi địa chỉ giao hàng',
                'Không liên lạc được khách hàng',
                'Khách hàng không bắt máy',
                'Thuê bao không liên lạc được'
            )
        """
        sql_odr_expr = f"({sql_ptc1_expr} OR {sql_lydo_l1_expr})"
    
        # ==========================================
        # 3. AGGREGATE BẢNG TỔNG
        # ==========================================
        df_d = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key,
                COUNT(DISTINCT ma_phieugui) as phat,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_odr_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_ptc1_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as ptc1,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 0 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as inday,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 1 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as nextday
            FROM orders {base_where}
            GROUP BY 1
        """).fetchdf()
    
        df_w = con.execute(f"""
            SELECT 
                STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as w_key,
                COUNT(DISTINCT ma_phieugui) as phat,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_odr_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_ptc1_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as ptc1,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 0 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as inday,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 1 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as nextday
            FROM orders {base_where}
            GROUP BY 1
        """).fetchdf()
    
        df_m = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key,
                COUNT(DISTINCT ma_phieugui) as phat,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_odr_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
                ROUND(COUNT(DISTINCT CASE WHEN {sql_ptc1_expr} AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as ptc1,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 0 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as inday,
                ROUND(COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 1 THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as nextday
            FROM orders {base_where}
            GROUP BY 1
        """).fetchdf()
    
        dict_d = {str(row.d_key): row for row in df_d.itertuples()} if df_d is not None and not df_d.empty else {}
        dict_w = {str(row.w_key): row for row in df_w.itertuples()} if df_w is not None and not df_w.empty else {}
        dict_m = {str(row.m_key): row for row in df_m.itertuples()} if df_m is not None and not df_m.empty else {}
    
        def get_v_fast(d_map, key, field_idx):
            k_str = str(key)
            if k_str in d_map:
                val = d_map[k_str][field_idx]
                if val is not None and val == val: return float(val)
            return 0.0
    
        v_d_phat = [get_v_fast(dict_d, d, 2) for d in day_cols]
        v_d_odr  = [get_v_fast(dict_d, d, 3) for d in day_cols]
        v_d_ptc1 = [get_v_fast(dict_d, d, 4) for d in day_cols]
        v_d_in   = [get_v_fast(dict_d, d, 5) for d in day_cols]
        v_d_next = [get_v_fast(dict_d, d, 6) for d in day_cols]
    
        v_w_phat = [get_v_fast(dict_w, w, 2) for w in week_cols]
        v_w_odr  = [get_v_fast(dict_w, w, 3) for w in week_cols]
        v_w_ptc1 = [get_v_fast(dict_w, w, 4) for w in week_cols]
        v_w_in   = [get_v_fast(dict_w, w, 5) for w in week_cols]
        v_w_next = [get_v_fast(dict_w, w, 6) for w in week_cols]
    
        v_m_phat = [get_v_fast(dict_m, m, 2) for m in month_cols]
        v_m_odr  = [get_v_fast(dict_m, m, 3) for m in month_cols]
        v_m_ptc1 = [get_v_fast(dict_m, m, 4) for m in month_cols]
        v_m_in   = [get_v_fast(dict_m, m, 5) for m in month_cols]
        v_m_next = [get_v_fast(dict_m, m, 6) for m in month_cols]
    
        def fmt_diff(val, is_pct=False):
            color = "text-green" if val >= 0 else "text-red"
            sign = "+" if val >= 0 else ""
            unit = "%" if not is_pct else ""
            return f'<td class="{color}">{sign}{val:.2f}{unit}</td>'
    
        dod_p = ((v_d_phat[-1] - v_d_phat[-2])/v_d_phat[-2]*100) if len(v_d_phat)>1 and v_d_phat[-2]>0 else 0
        wow_p = ((v_w_phat[-1] - v_w_phat[-2])/v_w_phat[-2]*100) if len(v_w_phat)>1 and v_w_phat[-2]>0 else 0
        mom_p = ((v_m_phat[1] - v_m_phat[0])/v_m_phat[0]*100) if len(v_m_phat)>1 and v_m_phat[0]>0 else 0
    
        dod_odr = v_d_odr[-1] - v_d_odr[-2] if len(v_d_odr)>1 else 0
        wow_odr = v_w_odr[-1] - v_w_odr[-2] if len(v_w_odr)>1 else 0
        mom_odr = (v_m_odr[1] - v_m_odr[0]) if len(v_m_odr)>1 else 0
    
        dod_ptc1 = v_d_ptc1[-1] - v_d_ptc1[-2] if len(v_d_ptc1)>1 else 0
        wow_ptc1 = v_w_ptc1[-1] - v_w_ptc1[-2] if len(v_w_ptc1)>1 else 0
        mom_ptc1 = (v_m_ptc1[1] - v_m_ptc1[0]) if len(v_m_ptc1)>1 else 0
    
        dod_in = v_d_in[-1] - v_d_in[-2] if len(v_d_in)>1 else 0
        wow_in = v_w_in[-1] - v_w_in[-2] if len(v_w_in)>1 else 0
        mom_in = (v_m_in[1] - v_m_in[0]) if len(v_m_in)>1 else 0
    
        dod_next = v_d_next[-1] - v_d_next[-2] if len(v_d_next)>1 else 0
        wow_next = v_w_next[-1] - v_w_next[-2] if len(v_w_next)>1 else 0
        mom_next = (v_m_next[1] - v_m_next[0]) if len(v_m_next)>1 else 0
    
        # ==========================================
        # 4. TRUY VẤN CÂY DỮ LIỆU ĐỐI TÁC / TỈNH / BƯU CỤC
        # ==========================================
        tree_day_df = con.execute(f"""
            SELECT 
                COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt,
                COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh,
                COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc,
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key,
                COUNT(DISTINCT ma_phieugui) as sl
            FROM orders {base_where}
            GROUP BY 1, 2, 3, 4
        """).fetchdf()
    
        tree_week_df = con.execute(f"""
            SELECT 
                COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt,
                COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh,
                COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc,
                STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as w_key,
                COUNT(DISTINCT ma_phieugui) as sl
            FROM orders {base_where}
            GROUP BY 1, 2, 3, 4
        """).fetchdf()
    
        tree_month_df = con.execute(f"""
            SELECT 
                COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt,
                COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh,
                COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc,
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key,
                COUNT(DISTINCT ma_phieugui) as sl
            FROM orders {base_where}
            GROUP BY 1, 2, 3, 4
        """).fetchdf()
    
        map_dt_d, map_tinh_d, map_bc_d = {}, {}, {}
        if tree_day_df is not None and not tree_day_df.empty:
            for r in tree_day_df.itertuples():
                map_dt_d[(str(r.dt), str(r.d_key))] = map_dt_d.get((str(r.dt), str(r.d_key)), 0) + r.sl
                map_tinh_d[(str(r.dt), str(r.tinh), str(r.d_key))] = map_tinh_d.get((str(r.dt), str(r.tinh), str(r.d_key)), 0) + r.sl
                map_bc_d[(str(r.dt), str(r.tinh), str(r.bc), str(r.d_key))] = map_bc_d.get((str(r.dt), str(r.tinh), str(r.bc), str(r.d_key)), 0) + r.sl
    
        map_dt_w, map_tinh_w, map_bc_w = {}, {}, {}
        if tree_week_df is not None and not tree_week_df.empty:
            for r in tree_week_df.itertuples():
                map_dt_w[(str(r.dt), str(r.w_key))] = map_dt_w.get((str(r.dt), str(r.w_key)), 0) + r.sl
                map_tinh_w[(str(r.dt), str(r.tinh), str(r.w_key))] = map_tinh_w.get((str(r.dt), str(r.tinh), str(r.w_key)), 0) + r.sl
                map_bc_w[(str(r.dt), str(r.tinh), str(r.bc), str(r.w_key))] = map_bc_w.get((str(r.dt), str(r.tinh), str(r.bc), str(r.w_key)), 0) + r.sl
    
        map_dt_m, map_tinh_m, map_bc_m = {}, {}, {}
        if tree_month_df is not None and not tree_month_df.empty:
            for r in tree_month_df.itertuples():
                map_dt_m[(str(r.dt), str(r.m_key))] = map_dt_m.get((str(r.dt), str(r.m_key)), 0) + r.sl
                map_tinh_m[(str(r.dt), str(r.tinh), str(r.m_key))] = map_tinh_m.get((str(r.dt), str(r.tinh), str(r.m_key)), 0) + r.sl
                map_bc_m[(str(r.dt), str(r.tinh), str(r.bc), str(r.m_key))] = map_bc_m.get((str(r.dt), str(r.tinh), str(r.bc), str(r.m_key)), 0) + r.sl
    
        tree_struct_df = con.execute(f"""
            SELECT DISTINCT 
                COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt,
                COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh,
                COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc
            FROM orders {base_where}
            ORDER BY 1, 2, 3
        """).fetchdf()
    
        dt_hierarchy = {}
        if tree_struct_df is not None and not tree_struct_df.empty:
            for r in tree_struct_df.itertuples():
                dt_str, tinh_str, bc_str = str(r.dt), str(r.tinh), str(r.bc)
                if dt_str not in dt_hierarchy: dt_hierarchy[dt_str] = {}
                if tinh_str not in dt_hierarchy[dt_str]: dt_hierarchy[dt_str][tinh_str] = []
                dt_hierarchy[dt_str][tinh_str].append(bc_str)
    
        matrix_rows_list = []
    
        for idx_dt, (dt_name, tinhs_dict) in enumerate(dt_hierarchy.items()):
            dt_clean_id = f"dt_{idx_dt}"
            
            d_vals_dt = [map_dt_d.get((dt_name, str(d)), 0) for d in day_cols]
            w_vals_dt = [map_dt_w.get((dt_name, str(w)), 0) for w in week_cols]
            m_vals_dt = [map_dt_m.get((dt_name, str(m)), 0) for m in month_cols]
            
            dod_dt = ((d_vals_dt[-1] - d_vals_dt[-2])/d_vals_dt[-2]*100) if len(d_vals_dt)>1 and d_vals_dt[-2]>0 else 0
            wow_dt = ((w_vals_dt[-1] - w_vals_dt[-2])/w_vals_dt[-2]*100) if len(w_vals_dt)>1 and w_vals_dt[-2]>0 else 0
            mom_dt = ((m_vals_dt[1] - m_vals_dt[0])/m_vals_dt[0]*100) if len(m_vals_dt)>1 and m_vals_dt[0]>0 else 0
    
            d_cells = "".join([f"<td>{v:,.0f}</td>" for v in d_vals_dt])
            w_cells = "".join([f"<td>{v:,.0f}</td>" for v in w_vals_dt])
    
            m0_val = m_vals_dt[0] if len(m_vals_dt) > 0 else 0
            m1_val = m_vals_dt[1] if len(m_vals_dt) > 1 else 0
    
            matrix_rows_list.append(f"""
            <tr class="sub-row-1 group_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
                <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
                {d_cells}{fmt_diff(dod_dt)}{w_cells}{fmt_diff(wow_dt)}<td>{m0_val:,.0f}</td><td><b>{m1_val:,.0f}</b></td>{fmt_diff(mom_dt)}
            </tr>
            """)
    
            for idx_tinh, (tinh_name, bcs_list) in enumerate(tinhs_dict.items()):
                tinh_clean_id = f"{dt_clean_id}_tinh_{idx_tinh}"
                
                d_vals_tinh = [map_tinh_d.get((dt_name, tinh_name, str(d)), 0) for d in day_cols]
                w_vals_tinh = [map_tinh_w.get((dt_name, tinh_name, str(w)), 0) for w in week_cols]
                m_vals_tinh = [map_tinh_m.get((dt_name, tinh_name, str(m)), 0) for m in month_cols]
                
                dod_tinh = ((d_vals_tinh[-1] - d_vals_tinh[-2])/d_vals_tinh[-2]*100) if len(d_vals_tinh)>1 and d_vals_tinh[-2]>0 else 0
                wow_tinh = ((w_vals_tinh[-1] - w_vals_tinh[-2])/w_vals_tinh[-2]*100) if len(w_vals_tinh)>1 and w_vals_tinh[-2]>0 else 0
                mom_tinh = ((m_vals_tinh[1] - m_vals_tinh[0])/m_vals_tinh[0]*100) if len(m_vals_tinh)>1 and m_vals_tinh[0]>0 else 0
    
                t_d_cells = "".join([f"<td>{v:,.0f}</td>" for v in d_vals_tinh])
                t_w_cells = "".join([f"<td>{v:,.0f}</td>" for v in w_vals_tinh])
    
                tm0_val = m_vals_tinh[0] if len(m_vals_tinh) > 0 else 0
                tm1_val = m_vals_tinh[1] if len(m_vals_tinh) > 1 else 0
    
                matrix_rows_list.append(f"""
                <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; color: #1565c0;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                    <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh: <b>{tinh_name}</b></td>
                    {t_d_cells}{fmt_diff(dod_tinh)}{t_w_cells}{fmt_diff(wow_tinh)}<td>{tm0_val:,.0f}</td><td><b>{tm1_val:,.0f}</b></td>{fmt_diff(mom_tinh)}
                </tr>
                """)
    
                for bc_name in bcs_list:
                    d_vals_bc = [map_bc_d.get((dt_name, tinh_name, bc_name, str(d)), 0) for d in day_cols]
                    w_vals_bc = [map_bc_w.get((dt_name, tinh_name, bc_name, str(w)), 0) for w in week_cols]
                    m_vals_bc = [map_bc_m.get((dt_name, tinh_name, bc_name, str(m)), 0) for m in month_cols]
                    
                    dod_bc = ((d_vals_bc[-1] - d_vals_bc[-2])/d_vals_bc[-2]*100) if len(d_vals_bc)>1 and d_vals_bc[-2]>0 else 0
                    wow_bc = ((w_vals_bc[-1] - w_vals_bc[-2])/w_vals_bc[-2]*100) if len(w_vals_bc)>1 and w_vals_bc[-2]>0 else 0
                    mom_bc = ((m_vals_bc[1] - m_vals_bc[0])/m_vals_bc[0]*100) if len(m_vals_bc)>1 and m_vals_bc[0]>0 else 0
    
                    b_d_cells = "".join([f"<td>{v:,.0f}</td>" for v in d_vals_bc])
                    b_w_cells = "".join([f"<td>{v:,.0f}</td>" for v in w_vals_bc])
    
                    bm0_val = m_vals_bc[0] if len(m_vals_bc) > 0 else 0
                    bm1_val = m_vals_bc[1] if len(m_vals_bc) > 1 else 0
    
                    matrix_rows_list.append(f"""
                    <tr class="sub-row-3 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                        <td style="padding-left: 60px;">• Bưu cục: <b>{bc_name}</b></td>
                        {b_d_cells}{fmt_diff(dod_bc)}{b_w_cells}{fmt_diff(wow_bc)}<td>{bm0_val:,.0f}</td><td><b>{bm1_val:,.0f}</b></td>{fmt_diff(mom_bc)}
                    </tr>
                    """)
    
        matrix_rows_html = "".join(matrix_rows_list)
    
        n_day_cols = len(day_labels)
        n_week_cols = len(week_labels)
    
        m0_tot = v_m_phat[0] if len(v_m_phat) > 0 else 0
        m1_tot = v_m_phat[1] if len(v_m_phat) > 1 else 0
    
        m0_odr = v_m_odr[0] if len(v_m_odr) > 0 else 0
        m1_odr = v_m_odr[1] if len(v_m_odr) > 1 else 0
    
        m0_ptc1 = v_m_ptc1[0] if len(v_m_ptc1) > 0 else 0
        m1_ptc1 = v_m_ptc1[1] if len(v_m_ptc1) > 1 else 0
    
        m0_in = v_m_in[0] if len(v_m_in) > 0 else 0
        m1_in = v_m_in[1] if len(v_m_in) > 1 else 0
    
        m0_next = v_m_next[0] if len(v_m_next) > 0 else 0
        m1_next = v_m_next[1] if len(v_m_next) > 1 else 0
    
        # ==========================================
        # 5. RENDER HTML BẢNG MA TRẬN
        # ==========================================
        matrix_full_html = f"""
        <!DOCTYPE html><html><head><style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }}
            .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; background-color: #ffffff; color: #111111; border: 1px solid #222222; }}
            .matrix-table th {{ background-color: #222222; color: #ffffff; text-align: center; padding: 7px 4px; border: 1px solid #444444; font-weight: 600; font-size: 11px; }}
            .matrix-table td {{ padding: 6px 8px; border: 1px solid #dddddd; vertical-align: middle; text-align: right; }}
            .matrix-table td:first-child {{ text-align: left; }}
            .row-group {{ font-weight: bold; background-color: #f8f9fa; cursor: pointer; }}
            .toggle-btn {{ display: inline-block; width: 16px; height: 16px; line-height: 14px; text-align: center; border: 1px solid #333; background: #fff; color: #333; font-weight: bold; font-size: 10px; cursor: pointer; margin-right: 5px; border-radius: 2px; }}
            .text-green {{ color: #2e7d32; font-weight: bold; }}
            .text-red {{ color: #c62828; font-weight: bold; }}
        </style></head><body>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th rowspan="2" style="width: 32%;">Chỉ tiêu</th>
                    <th colspan="{n_day_cols + 1}" style="background-color: #2a2a2a;">{n_day_cols} ngày gần nhất</th>
                    <th colspan="{n_week_cols + 1}" style="background-color: #333333;">{n_week_cols} tuần gần nhất</th>
                    <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
                </tr>
                <tr>
                    {"".join([f"<th>{d}</th>" for d in day_labels])}<th style="color: #ff5252;">DoD</th>
                    {"".join([f"<th>{w}</th>" for w in week_labels])}<th style="color: #ff5252;">WoW</th>
                    <th>{month_labels[0]}</th><th>{month_labels[1]}</th><th style="color: #ff5252;">MoM</th>
                </tr>
            </thead>
            <tbody>
                <!-- 1. SẢN LƯỢNG PHÁT -->
                <tr class="row-group" onclick="toggleRow('group_root', event, 'btn_root')">
                    <td><span class="toggle-btn" id="btn_root">[+]</span> <b>Sản lượng phát</b></td>
                    {"".join([f"<td>{v:,.0f}</td>" for v in v_d_phat])}
                    {fmt_diff(dod_p)}
                    {"".join([f"<td>{v:,.0f}</td>" for v in v_w_phat])}
                    {fmt_diff(wow_p)}
                    <td>{m0_tot:,.0f}</td><td><b>{m1_tot:,.0f}</b></td>
                    {fmt_diff(mom_p)}
                </tr>
    
                {matrix_rows_html}
    
                <!-- 2. % PHÁT THÀNH CÔNG ĐÚNG GIỜ (ODR) -->
                <tr>
                    <td style="font-weight: bold;">% Phát thành công đg (ODR)</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in v_d_odr])}
                    {fmt_diff(dod_odr, is_pct=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in v_w_odr])}
                    {fmt_diff(wow_odr, is_pct=True)}
                    <td>{m0_odr:.2f}</td><td><b>{m1_odr:.2f}</b></td>
                    {fmt_diff(mom_odr, is_pct=True)}
                </tr>
    
                <!-- 3. % PHÁT THÀNH CÔNG ĐÚNG GIỜ LẦN 1 -->
                <tr>
                    <td style="font-weight: bold;">% Phát thành công đg lần 1</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in v_d_ptc1])}
                    {fmt_diff(dod_ptc1, is_pct=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in v_w_ptc1])}
                    {fmt_diff(wow_ptc1, is_pct=True)}
                    <td>{m0_ptc1:.2f}</td><td><b>{m1_ptc1:.2f}</b></td>
                    {fmt_diff(mom_ptc1, is_pct=True)}
                </tr>
    
                <!-- 4. % PTC IN-DAY -->
                <tr>
                    <td style="font-weight: bold;">% PTC in-day</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in v_d_in])}
                    {fmt_diff(dod_in, is_pct=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in v_w_in])}
                    {fmt_diff(wow_in, is_pct=True)}
                    <td>{m0_in:.2f}</td><td><b>{m1_in:.2f}</b></td>
                    {fmt_diff(mom_in, is_pct=True)}
                </tr>
    
                <!-- 5. % PTC NEXT-DAY -->
                <tr>
                    <td style="font-weight: bold;">% PTC Next-day</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in v_d_next])}
                    {fmt_diff(dod_next, is_pct=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in v_w_next])}
                    {fmt_diff(wow_next, is_pct=True)}
                    <td>{m0_next:.2f}</td><td><b>{m1_next:.2f}</b></td>
                    {fmt_diff(mom_next, is_pct=True)}
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
        </script></body></html>
        """
        components.html(matrix_full_html, height=480, scrolling=True)
    
    except Exception as e:
        st.error(f"Lỗi tính toán Ma trận chất lượng vận hành: {e}")
    
    st.divider()
