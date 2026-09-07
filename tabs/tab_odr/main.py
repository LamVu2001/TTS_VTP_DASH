import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from .data_loader import get_odr_db

def render(file_id: str):
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    con = get_odr_db(file_id)

    # 1. KHỞI TẠO STATE NGÀY MẶC ĐỊNH TỪ DỮ LIỆU THỰC TẾ (NẾU CHƯA CÓ)
    if "f_date" not in st.session_state or not st.session_state.f_date:
        min_max = con.execute("SELECT MIN(clean_date), MAX(clean_date) FROM orders WHERE clean_date IS NOT NULL").fetchone()
        if min_max[0] and min_max[1]:
            st.session_state.f_date = (min_max[0], min_max[1])
        else:
            st.session_state.f_date = ()

    if "f_kh" not in st.session_state: st.session_state.f_kh = "Tất cả"
    if "f_bc" not in st.session_state: st.session_state.f_bc = "Tất cả"
    if "f_tuyen" not in st.session_state: st.session_state.f_tuyen = "Tất cả"
    if "f_ld" not in st.session_state: st.session_state.f_ld = "Tất cả"
    if "f_tl" not in st.session_state: st.session_state.f_tl = "Tất cả"

    # Hàm dựng câu lệnh WHERE cho các ô KPI / Bảng (lọc theo ngay_bat_dau_phai_phat)
    def build_where(exclude=None):
        conds = ["1=1"]
        if isinstance(st.session_state.f_date, (list, tuple)) and len(st.session_state.f_date) == 2:
            conds.append(f"clean_date BETWEEN '{st.session_state.f_date[0]}' AND '{st.session_state.f_date[1]}'")
        if exclude != "kh" and st.session_state.f_kh != "Tất cả":
            conds.append(f"CAST(ma_khgui AS VARCHAR) = '{st.session_state.f_kh}'")
        if exclude != "bc" and st.session_state.f_bc != "Tất cả":
            conds.append(f"CAST(ma_buucuc_phat AS VARCHAR) = '{st.session_state.f_bc}'")
        if exclude != "tuyen" and st.session_state.f_tuyen != "Tất cả":
            conds.append(f"CAST(tuyen AS VARCHAR) = '{st.session_state.f_tuyen}'")
        if exclude != "ld" and st.session_state.f_ld != "Tất cả":
            conds.append(f"CAST(ma_dv_viettel AS VARCHAR) = '{st.session_state.f_ld}'")
        if exclude != "tl" and st.session_state.f_tl != "Tất cả":
            conds.append(f"CAST(nhom_trong_luong AS VARCHAR) = '{st.session_state.f_tl}'")
        return " AND ".join(conds)

    # 2. LẤY DANH SÁCH TỰ ĐỘNG THEO DỮ LIỆU CROSS-FILTER
    kh_opts = ["Tất cả"] + [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    bc_opts = ["Tất cả"] + [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_buucuc_phat AS VARCHAR) FROM orders WHERE {build_where('bc')} AND ma_buucuc_phat IS NOT NULL ORDER BY 1").fetchall()]
    tuyen_opts = ["Tất cả"] + [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tuyen AS VARCHAR) FROM orders WHERE {build_where('tuyen')} AND tuyen IS NOT NULL ORDER BY 1").fetchall()]
    ld_opts = ["Tất cả"] + [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_dv_viettel AS VARCHAR) FROM orders WHERE {build_where('ld')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = ["Tất cả"] + [r[0] for r in con.execute(f"SELECT DISTINCT CAST(nhom_trong_luong AS VARCHAR) FROM orders WHERE {build_where('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]

    if st.session_state.f_kh not in kh_opts: st.session_state.f_kh = "Tất cả"
    if st.session_state.f_bc not in bc_opts: st.session_state.f_bc = "Tất cả"
    if st.session_state.f_tuyen not in tuyen_opts: st.session_state.f_tuyen = "Tất cả"
    if st.session_state.f_ld not in ld_opts: st.session_state.f_ld = "Tất cả"
    if st.session_state.f_tl not in tl_opts: st.session_state.f_tl = "Tất cả"

    # 3. HIỂN THỊ BỘ LỌC NGANG TRỰC TIẾP
    of1, of2, of3, of4, of5, of6 = st.columns(6)

    with of1:
        st.date_input("NGÀY", key="f_date")
    with of2:
        st.selectbox("MÃ KHÁCH HÀNG", kh_opts, key="f_kh")
    with of3:
        st.selectbox("MÃ BƯU CỤC PHÁT", bc_opts, key="f_bc")
    with of4:
        st.selectbox("TUYẾN", tuyen_opts, key="f_tuyen")
    with of5:
        st.selectbox("LOẠI ĐƠN (MÃ DV)", ld_opts, key="f_ld")
    with of6:
        st.selectbox("TRỌNG LƯỢNG", tl_opts, key="f_tl")

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
    
    # 5. BIỂU ĐỒ XU HƯỚNG SẢN LƯỢNG PHÁT THÀNH CÔNG (LỌC CHUẨN NGÀY PTC + PTC=1)
    c_odr_chart, c_odr_right = st.columns([2, 1.3])
    with c_odr_chart:
        st.subheader("📈 XU HƯỚNG SẢN LƯỢNG PHÁT THÀNH CÔNG")
        try:
            chart_conds = ["PTC = 1", "clean_date_ptc IS NOT NULL"]
            
            if st.session_state.f_kh != "Tất cả": chart_conds.append(f"CAST(ma_khgui AS VARCHAR) = '{st.session_state.f_kh}'")
            if st.session_state.f_bc != "Tất cả": chart_conds.append(f"CAST(ma_buucuc_phat AS VARCHAR) = '{st.session_state.f_bc}'")
            if st.session_state.f_tuyen != "Tất cả": chart_conds.append(f"CAST(tuyen AS VARCHAR) = '{st.session_state.f_tuyen}'")
            if st.session_state.f_ld != "Tất cả": chart_conds.append(f"CAST(ma_dv_viettel AS VARCHAR) = '{st.session_state.f_ld}'")
            if st.session_state.f_tl != "Tất cả": chart_conds.append(f"CAST(nhom_trong_luong AS VARCHAR) = '{st.session_state.f_tl}'")
            
            # Ép điều kiện ngày phát thành công nằm đúng khoảng thời gian được chọn
            if isinstance(st.session_state.f_date, (list, tuple)) and len(st.session_state.f_date) == 2:
                chart_conds.append(f"clean_date_ptc BETWEEN '{st.session_state.f_date[0]}' AND '{st.session_state.f_date[1]}'")
                
            where_chart_sql = " AND ".join(chart_conds)

            df_odr_daily = con.execute(f"""
                SELECT 
                    CAST(clean_date_ptc AS VARCHAR) as ngay_ptc, 
                    COUNT(*) as SanLuongPTC 
                FROM orders 
                WHERE {where_chart_sql}
                GROUP BY clean_date_ptc 
                ORDER BY clean_date_ptc ASC
            """).fetchdf()

            if len(df_odr_daily) > 0:
                fig_odr = px.line(df_odr_daily, x="ngay_ptc", y="SanLuongPTC", markers=True)
                fig_odr.update_traces(line=dict(color="#c62828", width=2.5), marker=dict(size=6, color="#c62828"))
                fig_odr.update_layout(
                    height=380, 
                    margin=dict(l=10, r=10, t=10, b=10), 
                    yaxis_title=None, 
                    xaxis_title=None,
                    xaxis=dict(type='category') # Dùng kiểu category để chỉ hiện các ngày có dữ liệu phát thành công thực tế
                )
                st.plotly_chart(fig_odr, use_container_width=True)
            else:
                st.warning("Không có dữ liệu phát thành công trong khoảng thời gian đã chọn.")
        except Exception as e:
            st.error(f"Lỗi tính toán biểu đồ: {e}")

    with c_odr_right:
        st.subheader("💡 THÔNG TIN TỔNG QUAN ODR")
        st.info("Biểu đồ bên trái thể hiện sản lượng đơn phát thành công thực tế theo cột clean_date_ptc (ngay_phat_cuoi_cung) trong khoảng thời gian đã chọn.")

    st.divider()

    # (Các phần bảng Tỉnh/Bưu cục, Ma trận vận hành & Bảng Tồn giữ nguyên)
