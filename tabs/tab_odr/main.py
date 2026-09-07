import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from datetime import datetime, date
from .data_loader import get_odr_db

def render(file_id: str):
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    con = get_odr_db(file_id)

    # 1. KHỞI TẠO STATE NGÀY MẶC ĐỊNH TỪ ĐẦU THÁNG HIỆN TẠI ĐẾN NGÀY HIỆN TẠI
    if "f_date" not in st.session_state or not st.session_state.f_date:
        today = date.today()
        first_day_of_month = today.replace(day=1)
        st.session_state.f_date = (first_day_of_month, today)

    if "f_tinh" not in st.session_state: st.session_state.f_tinh = []
    if "f_kh" not in st.session_state: st.session_state.f_kh = []
    if "f_bc" not in st.session_state: st.session_state.f_bc = []
    if "f_tuyen" not in st.session_state: st.session_state.f_tuyen = []
    if "f_ld" not in st.session_state: st.session_state.f_ld = []
    if "f_tl" not in st.session_state: st.session_state.f_tl = []

    # Hàm trợ giúp tạo mệnh đề SQL IN (...) an toàn chống SQL Injection
    def sql_in_clause(column_name, selected_list):
        if not selected_list:
            return None
        escaped = [str(x).replace("'", "''") for x in selected_list]
        vals = ", ".join([f"'{x}'" for x in escaped])
        return f"CAST({column_name} AS VARCHAR) IN ({vals})"

    # Hàm dựng câu lệnh WHERE cho Cross-Filtering
    def build_where(exclude=None):
        conds = ["1=1"]
        if isinstance(st.session_state.f_date, (list, tuple)) and len(st.session_state.f_date) == 2:
            conds.append(f"clean_date BETWEEN '{st.session_state.f_date[0]}' AND '{st.session_state.f_date[1]}'")
        
        if exclude != "tinh":
            c = sql_in_clause("tinh_phat", st.session_state.f_tinh)
            if c: conds.append(c)
        if exclude != "kh":
            c = sql_in_clause("ma_khgui", st.session_state.f_kh)
            if c: conds.append(c)
        if exclude != "bc":
            c = sql_in_clause("ma_buucuc_phat", st.session_state.f_bc)
            if c: conds.append(c)
        if exclude != "tuyen":
            c = sql_in_clause("tuyen", st.session_state.f_tuyen)
            if c: conds.append(c)
        if exclude != "ld":
            c = sql_in_clause("ma_dv_viettel", st.session_state.f_ld)
            if c: conds.append(c)
        if exclude != "tl":
            c = sql_in_clause("nhom_trong_luong", st.session_state.f_tl)
            if c: conds.append(c)
            
        return " AND ".join(conds)

    # 2. LẤY DANH SÁCH TỰ ĐỘNG THEO DỮ LIỆU CROSS-FILTER
    tinh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tinh_phat AS VARCHAR) FROM orders WHERE {build_where('tinh')} AND tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    bc_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_buucuc_phat AS VARCHAR) FROM orders WHERE {build_where('bc')} AND ma_buucuc_phat IS NOT NULL ORDER BY 1").fetchall()]
    tuyen_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tuyen AS VARCHAR) FROM orders WHERE {build_where('tuyen')} AND tuyen IS NOT NULL ORDER BY 1").fetchall()]
    ld_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_dv_viettel AS VARCHAR) FROM orders WHERE {build_where('ld')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(nhom_trong_luong AS VARCHAR) FROM orders WHERE {build_where('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]

    # Validate lọc sạch các value cũ không còn nằm trong danh sách tùy chọn mới
    st.session_state.f_tinh = [v for v in st.session_state.f_tinh if v in tinh_opts]
    st.session_state.f_kh = [v for v in st.session_state.f_kh if v in kh_opts]
    st.session_state.f_bc = [v for v in st.session_state.f_bc if v in bc_opts]
    st.session_state.f_tuyen = [v for v in st.session_state.f_tuyen if v in tuyen_opts]
    st.session_state.f_ld = [v for v in st.session_state.f_ld if v in ld_opts]
    st.session_state.f_tl = [v for v in st.session_state.f_tl if v in tl_opts]

    # 3. HIỂN THỊ BỘ LỌC NGANG DẠNG MULTI-SELECT (7 Ô LỌC)
    of1, of2, of3, of4, of5, of6, of7 = st.columns(7)

    with of1:
        st.date_input("NGÀY PHẢI PHÁT", key="f_date")
    with of2:
        st.multiselect("TỈNH PHÁT", tinh_opts, key="f_tinh", placeholder="Tất cả")
    with of3:
        st.multiselect("MÃ KHÁCH HÀNG", kh_opts, key="f_kh", placeholder="Tất cả")
    with of4:
        st.multiselect("BƯU CỤC PHÁT", bc_opts, key="f_bc", placeholder="Tất cả")
    with of5:
        st.multiselect("TUYẾN", tuyen_opts, key="f_tuyen", placeholder="Tất cả")
    with of6:
        st.multiselect("LOẠI ĐƠN (DV)", ld_opts, key="f_ld", placeholder="Tất cả")
    with of7:
        st.multiselect("TRỌNG LƯỢNG", tl_opts, key="f_tl", placeholder="Tất cả")

    # 4. TỔNG HỢP MỆNH ĐỀ WHERE VÀ TRUY VẤN KPI
    where_sql_odr = build_where()

    res_metrics_odr = con.execute(f"""
        SELECT 
            COUNT(*) AS tong_sl,
            COALESCE(SUM(PTC), 0) AS sl_ptc,
            COALESCE(SUM(PTC_1), 0) AS sl_ptc1
        FROM orders 
        WHERE {where_sql_odr}
    """).fetchone()

    tong_sl_odr = res_metrics_odr[0]
    sl_ptc = res_metrics_odr[1]
    sl_ptc1 = res_metrics_odr[2]

    pct_ptc = (sl_ptc / tong_sl_odr * 100) if tong_sl_odr > 0 else 0
    pct_ptc1 = (sl_ptc1 / tong_sl_odr * 100) if tong_sl_odr > 0 else 0

    m_odr1, m_odr2, m_odr3, m_odr4 = st.columns(4)
    with m_odr1: st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{tong_sl_odr:,.0f}</div><div class="metric-sub-green">▲ Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr2: st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">{pct_ptc:.1f}%</div><div class="metric-sub-green">Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr3: st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC LẦN 1</div><div class="metric-value">{pct_ptc1:.1f}%</div><div class="metric-sub-green">Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr4: st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">{pct_ptc:.1f}%</div><div class="metric-sub-green">Thực tế</div></div>', unsafe_allow_html=True)

    st.write("")
    
    # 5. BIỂU ĐỒ XU HƯỚNG PHÁT THÀNH CÔNG THEO THỜI GIAN PHẢI PHÁT (clean_date)
    c_odr_chart, c_odr_right = st.columns([2, 1.3])
    with c_odr_chart:
        st.subheader("📈 XU HƯỚNG SẢN LƯỢNG PHÁT THÀNH CÔNG")
        try:
            # Dùng chung mệnh đề build_where() hiện tại và thêm điều kiện PTC = 1
            where_chart_sql = f"{where_sql_odr} AND PTC = 1 AND clean_date IS NOT NULL"

            df_odr_daily = con.execute(f"""
                SELECT 
                    CAST(clean_date AS VARCHAR) as ngay_phai_phat, 
                    COUNT(*) as SanLuongPTC 
                FROM orders 
                WHERE {where_chart_sql}
                GROUP BY clean_date 
                ORDER BY clean_date ASC
            """).fetchdf()

            if len(df_odr_daily) > 0:
                fig_odr = px.line(df_odr_daily, x="ngay_phai_phat", y="SanLuongPTC", markers=True)
                fig_odr.update_traces(line=dict(color="#c62828", width=2.5), marker=dict(size=6, color="#c62828"))
                fig_odr.update_layout(
                    height=380, 
                    margin=dict(l=10, r=10, t=10, b=10), 
                    yaxis_title=None, 
                    xaxis_title=None,
                    xaxis=dict(type='category')
                )
                st.plotly_chart(fig_odr, use_container_width=True)
            else:
                st.warning("Không có dữ liệu phát thành công trong khoảng thời gian đã chọn.")
        except Exception as e:
            st.error(f"Lỗi tính toán biểu đồ: {e}")

    with c_odr_right:
        st.subheader("💡 THÔNG TIN TỔNG QUAN ODR")
        st.info("Biểu đồ bên trái thể hiện số lượng đơn phát thành công (PTC = 1) phân bổ theo thời gian phải phát (clean_date) trong khoảng thời gian đã chọn.")

    st.divider()
    # (Giữ nguyên các phần Bảng tương tác, Ma trận vận hành & Bảng tồn khâu ở bên dưới)
