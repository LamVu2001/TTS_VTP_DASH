import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from datetime import datetime, date

# Import trực tiếp file data_loader.py từ thư mục gốc
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

    # Hàm dựng câu lệnh WHERE cho Cross-Filtering (Lọc ngày theo CAST(tg_ptc AS DATE))
    def build_where(exclude=None):
        conds = ["1=1"]
        if exclude != "date" and isinstance(st.session_state.f_date, (list, tuple)) and len(st.session_state.f_date) == 2:
            conds.append(f"CAST(tg_ptc AS DATE) BETWEEN '{st.session_state.f_date[0]}' AND '{st.session_state.f_date[1]}'")
        
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

    # MỆNH ĐỀ WHERE TOÀN CỤC LỌC THEO CỘT tg_ptc
    where_sql_odr = build_where()

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

    # 3. HIỂN THỊ BỘ LỌC NGANG DẠNG MULTI-SELECT
    of1, of2, of3, of4, of5, of6, of7 = st.columns(7)

    with of1:
        st.date_input("NGÀY", key="f_date")
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

    # 4. TỔNG HỢP TRUY VẤN KPI THEO NGÀY PHÁT THỰC TẾ (tg_ptc)
    res_metrics_odr = con.execute(f"""
        SELECT 
            -- Tổng sản lượng phát trong khoảng tg_ptc
            COUNT(DISTINCT ma_phieugui) AS tong_sl_phat,

            -- Sản lượng phát failed SLA (Giao không đúng giờ)
            COUNT(DISTINCT CASE 
                WHEN danh_gia_giao_hang = 'Giao không đúng giờ' THEN ma_phieugui 
            END) AS sl_failed_sla,

            -- (2) Mẫu số: Tổng đơn PTC TT 501 trong kỳ phát
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) = '501' THEN ma_phieugui 
            END) AS tong_ptc_501,

            -- (1a) Tử số: Đơn PTC 501 trong SLA cam kết (Phát đúng giờ)
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) = '501' 
                 AND danh_gia_giao_hang = 'Giao đúng giờ' 
                THEN ma_phieugui 
            END) AS sl_ptc_501_in_sla,
            
            -- (1b) Tử số: Đơn có TT 501, 505, 506, 507, 509 phát lần 1 trong SLA cam kết
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) IN ('501', '505', '506', '507', '509') 
                 AND PTC_1 = 1 
                 AND danh_gia_giao_hang = 'Giao đúng giờ' 
                THEN ma_phieugui 
            END) AS sl_lan1_in_sla,

            -- Đơn PTC Lần 1 chung trong kỳ
            COUNT(DISTINCT CASE WHEN PTC_1 = 1 THEN ma_phieugui END) AS sl_ptc1

        FROM orders 
        WHERE {where_sql_odr} AND tg_ptc IS NOT NULL
    """).fetchone()

    tong_sl_phat = res_metrics_odr[0] or 0
    sl_failed_sla = res_metrics_odr[1] or 0
    mau_so_501 = res_metrics_odr[2] or 0          # (2) Mẫu số đơn PTC TT 501
    tu_so_dung_gio = res_metrics_odr[3] or 0      # (1a) Tử số Đúng giờ
    tu_so_lan1_dung_gio = res_metrics_odr[4] or 0 # (1b) Tử số Đúng giờ lần 1
    sl_ptc1 = res_metrics_odr[5] or 0

    # Tính toán tỷ lệ %
    pct_failed_sla = (sl_failed_sla / tong_sl_phat * 100) if tong_sl_phat > 0 else 0
    pct_ptc1 = (sl_ptc1 / tong_sl_phat * 100) if tong_sl_phat > 0 else 0
    pct_ptc_dung_gio = (tu_so_dung_gio / mau_so_501 * 100) if mau_so_501 > 0 else 0
    pct_ptc1_dung_gio = (tu_so_lan1_dung_gio / mau_so_501 * 100) if mau_so_501 > 0 else 0

    # HIỂN THỊ 5 THẺ KPI (ĐÃ BỎ CHỮ XANH, TĂNG KÍCH THƯỚC CHỮ)
    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    
    with m_odr1: 
        st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 15px 10px;">
                <div class="metric-title" style="font-size: 13px; font-weight: bold; color: #555555; margin-bottom: 8px;">SẢN LƯỢNG PHÁT</div>
                <div class="metric-value" style="font-size: 28px; font-weight: 800; color: #111111;">{tong_sl_phat:,.0f}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_odr2: 
        st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 15px 10px;">
                <div class="metric-title" style="font-size: 13px; font-weight: bold; color: #555555; margin-bottom: 8px;">SẢN LƯỢNG PHÁT FAILED SLA</div>
                <div class="metric-value" style="font-size: 28px; font-weight: 800; color: #111111;">{sl_failed_sla:,.0f}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_odr3: 
        st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 15px 10px;">
                <div class="metric-title" style="font-size: 13px; font-weight: bold; color: #555555; margin-bottom: 8px;">TỶ LỆ PHÁT FAILED SLA</div>
                <div class="metric-value" style="font-size: 28px; font-weight: 800; color: #111111;">{pct_failed_sla:.1f}%</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_odr4: 
        st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 15px 10px;">
                <div class="metric-title" style="font-size: 13px; font-weight: bold; color: #555555; margin-bottom: 8px;">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div>
                <div class="metric-value" style="font-size: 28px; font-weight: 800; color: #111111;">{pct_ptc_dung_gio:.1f}%</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with m_odr5: 
        st.markdown(f'''
            <div class="metric-card" style="text-align: center; padding: 15px 10px;">
                <div class="metric-title" style="font-size: 13px; font-weight: bold; color: #555555; margin-bottom: 8px;">TỶ LỆ PHÁT ĐÚNG GIỜ LẦN 1</div>
                <div class="metric-value" style="font-size: 28px; font-weight: 800; color: #111111;">{pct_ptc1_dung_gio:.1f}%</div>
            </div>
        ''', unsafe_allow_html=True)
        
    st.write("")
    
   # =========================================================================
    # 5. BIỂU ĐỒ XU HƯỚNG PHÁT THÀNH CÔNG VÀ TỶ TRỌNG CÁC KHÂU SAI
    # =========================================================================
    c_odr_chart, c_odr_right = st.columns([2, 1.3])

    # --- BIỂU ĐỒ TRÁI: XU HƯỚNG SẢN LƯỢNG VÀ TỶ LỆ ODR ---
    with c_odr_chart:
        st.subheader("📈 XU HƯỚNG SẢN LƯỢNG VÀ TỶ LỆ ODR")

        # Bộ lọc Chế độ xem nằm NGAY DƯỚI Tiêu đề
        time_view = st.radio(
            "Chế độ xem:",
            options=["Ngày", "Tuần", "Tháng"],
            index=0,
            horizontal=True,
            key="chart_time_view",
            label_visibility="collapsed",
        )

        try:
            # Quy chuẩn thời gian DuckDB & Định dạng hiển thị
            if time_view == "Tuần":
                # Quy chuẩn Chủ Nhật -> Thứ 7 cho TikTok Shop
                date_expr = "CAST((DATE_TRUNC('week', CAST(tg_ptc AS DATE) + INTERVAL 1 DAY) - INTERVAL 1 DAY) AS DATE)"
                date_format = "%d/%m/%Y"
            elif time_view == "Tháng":
                date_expr = "DATE_TRUNC('month', CAST(tg_ptc AS DATE))"
                date_format = "%m/%Y"
            else:
                date_expr = "CAST(tg_ptc AS DATE)"
                date_format = "%d/%m/%Y"

            # SQL nhóm theo thời gian
            df_odr_daily = con.execute(f"""
                SELECT 
                    STRFTIME({date_expr}, '{date_format}') as time_label, 
                    COUNT(DISTINCT ma_phieugui) as tong_sl_phat,
                    COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) as sl_dung_gio,
                    ROUND(
                        COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / 
                        NULLIF(COUNT(DISTINCT ma_phieugui), 0), 
                    1) as ty_le_odr,
                    MIN({date_expr}) as sort_key
                FROM orders 
                WHERE {where_sql_odr} AND tg_ptc IS NOT NULL
                GROUP BY 1
                ORDER BY sort_key ASC
            """).fetchdf()

            if len(df_odr_daily) > 0:
                fig_odr = make_subplots(specs=[[{"secondary_y": True}]])

                # Line 1: Sản lượng phát (Trục trái - Đỏ đô đậm dễ nhìn)
                fig_odr.add_trace(
                    go.Scatter(
                        x=df_odr_daily["time_label"],
                        y=df_odr_daily["tong_sl_phat"],
                        name="Sản lượng phát",
                        mode="lines+markers+text",
                        text=df_odr_daily["tong_sl_phat"].apply(
                            lambda x: f"{x:,.0f}"
                        ),
                        textposition="top center",
                        textfont=dict(
                            size=10, color="#800000", family="Arial Black"
                        ),
                        line=dict(color="#d32f2f", width=2.5),
                        marker=dict(size=5, color="#d32f2f"),
                    ),
                    secondary_y=False,
                )

                # Line 2: Tỷ lệ ODR % (Trục phải - Xanh lá đậm Forest Green tương phản)
                fig_odr.add_trace(
                    go.Scatter(
                        x=df_odr_daily["time_label"],
                        y=df_odr_daily["ty_le_odr"],
                        name="Tỷ lệ ODR (%)",
                        mode="lines+markers+text",
                        text=df_odr_daily["ty_le_odr"].apply(
                            lambda x: f"{x:.1f}%"
                        ),
                        textposition="bottom center",
                        textfont=dict(
                            size=10, color="#1b5e20", family="Arial Black"
                        ),
                        line=dict(color="#2e7d32", width=2, dash="dot"),
                        marker=dict(size=5, color="#2e7d32"),
                    ),
                    secondary_y=True,
                )

                # Khóa dải giá trị Y để KHÔNG HIỂN THỊ SỐ ÂM
                max_sl = (
                    df_odr_daily["tong_sl_phat"].max()
                    if not df_odr_daily.empty
                    else 100000
                )
                min_odr = (
                    df_odr_daily["ty_le_odr"].min()
                    if not df_odr_daily.empty
                    else 50
                )
                start_odr_range = max(50, min_odr - 5) if min_odr >= 50 else 0

                fig_odr.update_layout(
                    height=410,
                    margin=dict(l=10, r=10, t=35, b=10),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.05,
                        xanchor="right",
                        x=1,
                        font=dict(size=11),
                    ),
                    xaxis=dict(
                        type="category",
                        title=None,
                        tickangle=-35,
                        tickfont=dict(size=10, color="#333333"),
                    ),
                    hovermode="x unified",
                    plot_bgcolor="#ffffff",
                )

                # Trục Y Trái (Sản lượng): Bắt đầu từ 0
                fig_odr.update_yaxes(
                    title_text="Sản lượng phát",
                    secondary_y=False,
                    showgrid=True,
                    gridcolor="#eeeeee",
                    zeroline=True,
                    zerolinecolor="#cccccc",
                    range=[0, max_sl * 1.25],
                )

                # Trục Y Phải (Tỷ lệ ODR %): Khóa dải từ 50% trở lên
                fig_odr.update_yaxes(
                    title_text="Tỷ lệ ODR (%)",
                    secondary_y=True,
                    showgrid=False,
                    zeroline=False,
                    range=[start_odr_range, 105],
                )

                st.plotly_chart(
                    fig_odr,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                st.warning(
                    "Không có dữ liệu phát thành công trong khoảng thời gian đã chọn."
                )
        except Exception as e:
            st.error(f"Lỗi tính toán biểu đồ: {e}")

    # --- BIỂU ĐỒ PHẢI: TỶ TRỌNG CÁC KHÂU SAI (%) ---
    with c_odr_right:
        st.subheader("📊 TỶ TRỌNG CÁC KHÂU SAI (%)")
        try:
            # Truy vấn đếm đơn Failed SLA theo cột KHAU_SAI
            df_khau_sai = con.execute(f"""
                WITH failed_orders AS (
                    SELECT 
                        COALESCE(CAST(KHAU_SAI AS VARCHAR), 'Chưa xác định') as khau_sai_name,
                        COUNT(DISTINCT ma_phieugui) as sl_failed
                    FROM orders
                    WHERE {where_sql_odr} 
                      AND tg_ptc IS NOT NULL
                      AND danh_gia_giao_hang = 'Giao không đúng giờ'
                    GROUP BY COALESCE(CAST(KHAU_SAI AS VARCHAR), 'Chưa xác định')
                ),
                total_failed AS (
                    SELECT SUM(sl_failed) as total_sl FROM failed_orders
                )
                SELECT 
                    f.khau_sai_name,
                    f.sl_failed,
                    ROUND(f.sl_failed * 100.0 / NULLIF(t.total_sl, 0), 2) as ty_le_pct
                FROM failed_orders f, total_failed t
                WHERE f.khau_sai_name IS NOT NULL AND f.khau_sai_name != ''
                ORDER BY f.sl_failed ASC
            """).fetchdf()

            if len(df_khau_sai) > 0:
                fig_khau_sai = px.bar(
                    df_khau_sai,
                    x="ty_le_pct",
                    y="khau_sai_name",
                    orientation="h",
                    text=df_khau_sai["ty_le_pct"].apply(lambda x: f"{x:.2f}%"),
                )

                fig_khau_sai.update_traces(
                    marker_color="#c62828",
                    textposition="outside",
                    textfont=dict(
                        size=11, color="#111111", family="Arial Black"
                    ),
                )

                max_pct = (
                    df_khau_sai["ty_le_pct"].max()
                    if not df_khau_sai.empty
                    else 100
                )

                fig_khau_sai.update_layout(
                    height=410,
                    margin=dict(l=10, r=45, t=35, b=10),
                    xaxis_title=None,
                    yaxis_title=None,
                    plot_bgcolor="#ffffff",
                    xaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        range=[0, max_pct * 1.25],
                    ),
                    yaxis=dict(
                        showgrid=False,
                        tickfont=dict(size=12, color="#111111"),
                    ),
                )

                st.plotly_chart(
                    fig_khau_sai,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                st.info(
                    "Không có dữ liệu khâu sai cho các đơn Failed SLA trong khoảng thời gian đã chọn."
                )
        except Exception as e:
            st.error(f"Lỗi tính toán biểu đồ khâu sai: {e}")
    st.divider()

    # 6. BẢNG TƯƠNG TÁC TỈNH PHÁT / BƯU CỤC PHÁT
    st.markdown('<p class="section-red-title">DANH SÁCH CHI NHÁNH & BƯU CỤC PHÁT</p>', unsafe_allow_html=True)

    cn_data_raw = con.execute(f"""
        SELECT 
            CAST(tinh_phat AS VARCHAR) AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_don,
            COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) AS ptc_dung_gio,
            COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao không đúng giờ' THEN ma_phieugui END) AS sl_failed,
            ROUND(COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 1) AS ty_le_odr
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND tg_ptc IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    bc_data_raw = con.execute(f"""
        SELECT 
            CAST(ma_buucuc_phat AS VARCHAR) AS bc, 
            CAST(tinh_phat AS VARCHAR) AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_don,
            COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) AS ptc_dung_gio,
            COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao không đúng giờ' THEN ma_phieugui END) AS sl_failed,
            ROUND(COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 1) AS ty_le_odr
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL AND tg_ptc IS NOT NULL
        GROUP BY ma_buucuc_phat, tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    # Render dòng cho bảng Tỉnh Phát (Trái)
    rows_cn_html = "".join([
        f'<tr class="cn-row" data-cn="{item[0]}" onclick="filterBC(\'{item[0]}\', this)">'
        f'<td style="font-weight: bold; cursor: pointer; text-align: left; padding-left: 10px;">{item[0]}</td>'
        f'<td style="text-align: right; padding-right: 10px;">{item[1]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px;">{item[2]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px; color: #c62828;">{item[3]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px; font-weight: bold; color: #2e7d32;">{item[4]:.1f}%</td>'
        f'</tr>' 
        for item in cn_data_raw
    ])

    # Render dòng cho bảng Bưu Cục Phát (Phải)
    rows_bc_html = "".join([
        f'<tr class="bc-row" data-cn="{item[1]}">'
        f'<td style="font-weight: bold; text-align: left; padding-left: 10px;">{item[0]}</td>'
        f'<td style="font-weight: bold; text-align: center;">{item[1]}</td>'
        f'<td style="text-align: right; padding-right: 10px;">{item[2]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px;">{item[3]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px; color: #c62828;">{item[4]:,}</td>'
        f'<td style="text-align: right; padding-right: 10px; font-weight: bold; color: #2e7d32;">{item[5]:.1f}%</td>'
        f'</tr>' 
        for item in bc_data_raw
    ])

    interactive_tables_html = f"""
    <!DOCTYPE html><html><head><style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: transparent; }}
        .grid-container {{ display: grid; grid-template-columns: 1fr 1.15fr; gap: 15px; }}
        .table-title {{ font-size: 12px; font-weight: bold; color: #333; margin-bottom: 6px; }}
        .table-scroll {{ max-height: 360px; overflow-y: auto; border: 1px solid #d3d3d3; border-radius: 4px; background: #fff; }}
        table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px; }}
        th {{ position: sticky; top: 0; z-index: 10; background-color: #222222; color: #ffffff; text-align: center; padding: 7px 8px; border-bottom: 1px solid #444; border-right: 1px solid #444; font-weight: bold; }}
        td {{ padding: 6px 8px; border-bottom: 1px solid #eee; border-right: 1px solid #eee; color: #111; }}
        tr.cn-row:hover {{ background-color: #ffebee !important; cursor: pointer; }}
        tr.selected-cn {{ background-color: #ffcdd2 !important; }}
        .btn-reset {{ display: inline-block; padding: 2px 8px; font-size: 11px; background: #eee; border: 1px solid #ccc; border-radius: 3px; cursor: pointer; margin-left: 8px; font-weight: normal; }}
    </style></head><body>
    <div class="grid-container">
        <div>
            <div class="table-title">Bảng Tỉnh Phát <span style="font-weight:normal; color:#666;">(Bấm chọn dòng để lọc Bưu cục)</span> <span class="btn-reset" onclick="resetFilter()">Xóa lọc</span></div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Tỉnh phát</th>
                            <th style="text-align: right; padding-right: 10px;">SL PTC</th>
                            <th style="text-align: right; padding-right: 10px;">PTC Đúng Giờ</th>
                            <th style="text-align: right; padding-right: 10px;">Failed SLA</th>
                            <th style="text-align: right; padding-right: 10px;">Tỷ lệ ODR</th>
                        </tr>
                    </thead>
                    <tbody>{rows_cn_html if rows_cn_html else "<tr><td colspan='5' style='text-align:center;'>Không có dữ liệu</td></tr>"}</tbody>
                </table>
            </div>
        </div>
        <div>
            <div class="table-title">Bưu Cục Phát <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span></div>
            <div class="table-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align: left; padding-left: 10px;">Mã bưu cục phát</th>
                            <th>Tỉnh phát</th>
                            <th style="text-align: right; padding-right: 10px;">SL PTC</th>
                            <th style="text-align: right; padding-right: 10px;">PTC Đúng Giờ</th>
                            <th style="text-align: right; padding-right: 10px;">Failed SLA</th>
                            <th style="text-align: right; padding-right: 10px;">Tỷ lệ ODR</th>
                        </tr>
                    </thead>
                    <tbody id="bc-tbody">{rows_bc_html if rows_bc_html else "<tr><td colspan='6' style='text-align:center;'>Không có dữ liệu</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        function filterBC(cnCode, rowElem) {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) cnRows[i].classList.remove('selected-cn');
            if (rowElem) rowElem.classList.add('selected-cn');
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) {{
                bcRows[j].style.display = (bcRows[j].getAttribute('data-cn') === cnCode) ? 'table-row' : 'none';
            }}
            document.getElementById('bc-title-status').innerText = '(Tỉnh: ' + cnCode + ')';
        }}
        function resetFilter() {{
            var cnRows = document.getElementsByClassName('cn-row');
            for (var i = 0; i < cnRows.length; i++) cnRows[i].classList.remove('selected-cn');
            var bcRows = document.getElementsByClassName('bc-row');
            for (var j = 0; j < bcRows.length; j++) bcRows[j].style.display = 'table-row';
            document.getElementById('bc-title-status').innerText = '(Toàn Quốc)';
        }}
    </script></body></html>
    """
    components.html(interactive_tables_html, height=410, scrolling=False)

    st.divider()

# 7. BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH (FIX CHỦN LỖI PTC_1 100%)
    st.subheader("📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH")

    try:
        base_where = f"WHERE {where_sql_odr} AND tg_ptc IS NOT NULL" if where_sql_odr else "WHERE tg_ptc IS NOT NULL"

        # 1. LẤY MỐC THỜI GIAN
        days_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as dt, 
                STRFTIME(CAST(tg_ptc AS DATE), '%d/%m') as dt_label
            FROM orders {base_where}
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 7
        """).fetchdf()

        day_cols = days_df["dt"].tolist()[::-1] if days_df is not None and not days_df.empty else []
        day_labels = days_df["dt_label"].tolist()[::-1] if days_df is not None and not days_df.empty else []

        weeks_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as min_date,
                'W' || STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%W') as week_label
            FROM orders {base_where}
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 5
        """).fetchdf()

        week_cols = weeks_df["min_date"].tolist()[::-1] if weeks_df is not None and not weeks_df.empty else []
        week_labels = weeks_df["week_label"].tolist()[::-1] if weeks_df is not None and not weeks_df.empty else []

        months_df = con.execute(f"""
            SELECT DISTINCT STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key
            FROM orders {base_where}
            ORDER BY 1 DESC LIMIT 2
        """).fetchdf()

        month_cols = months_df["m_key"].tolist()[::-1] if months_df is not None and not months_df.empty else []
        while len(month_cols) < 2:
            month_cols.insert(0, f"M_empty_{len(month_cols)}")

        # 2. AGGREGATE BẢNG TỔNG (FIX ĐIỀU KIỆN PTC_1 ÉP KIỂU VARCHAR CHUẨN)
        sql_ptc1_expr = "CAST(PTC_1 AS VARCHAR) IN ('1', '1.0', 'true', 'TRUE')"

        df_d = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key,
                COUNT(DISTINCT ma_phieugui) as phat,
                ROUND(COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
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
                ROUND(COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
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
                ROUND(COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) * 100.0 / NULLIF(COUNT(DISTINCT ma_phieugui), 0), 2) as odr,
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

        # 3. TRUY VẤN CÂY DỮ LIỆU ĐỐI TÁC / TỈNH / BƯU CỤC
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
            m1_val = m_vals_dt[1] if len(m_vals_dt) > 1 else m0_val

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
                tm1_val = m_vals_tinh[1] if len(m_vals_tinh) > 1 else tm0_val

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
                    bm1_val = m_vals_bc[1] if len(m_vals_bc) > 1 else bm0_val

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
        m1_tot = v_m_phat[1] if len(v_m_phat) > 1 else m0_tot

        m0_odr = v_m_odr[0] if len(v_m_odr) > 0 else 0
        m1_odr = v_m_odr[1] if len(v_m_odr) > 1 else m0_odr

        m0_ptc1 = v_m_ptc1[0] if len(v_m_ptc1) > 0 else 0
        m1_ptc1 = v_m_ptc1[1] if len(v_m_ptc1) > 1 else m0_ptc1

        m0_in = v_m_in[0] if len(v_m_in) > 0 else 0
        m1_in = v_m_in[1] if len(v_m_in) > 1 else m0_in

        m0_next = v_m_next[0] if len(v_m_next) > 0 else 0
        m1_next = v_m_next[1] if len(v_m_next) > 1 else m0_next

        # 4. RENDER HTML
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
                    <th rowspan="2" style="width: 28%;">Chỉ tiêu</th>
                    <th colspan="{n_day_cols + 1}" style="background-color: #2a2a2a;">{n_day_cols} ngày gần nhất</th>
                    <th colspan="{n_week_cols + 1}" style="background-color: #333333;">{n_week_cols} tuần gần nhất</th>
                    <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
                </tr>
                <tr>
                    {"".join([f"<th>{d}</th>" for d in day_labels])}<th style="color: #ff5252;">DoD</th>
                    {"".join([f"<th>{w}</th>" for w in week_labels])}<th style="color: #ff5252;">WoW</th>
                    <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
                </tr>
            </thead>
            <tbody>
                <!-- 1. SẢN LƯỢNG PHẢI PHÁT -->
                <tr class="row-group" onclick="toggleRow('group_root', event, 'btn_root')">
                    <td><span class="toggle-btn" id="btn_root">[+]</span> <b>Sản lượng phải phát</b></td>
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

    # # 8. BA BẢNG TỒN KHÂU (FM, MM, LM)
    # ton_tree_data = con.execute(f"SELECT COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc, COUNT(DISTINCT ma_phieugui) as sl FROM orders WHERE {where_sql_odr} GROUP BY tinh_phat, ma_buucuc_phat ORDER BY 1, 3 DESC").fetchall()

    # tinh_tree = {}
    # for tinh, bc, sl in ton_tree_data:
    #     if tinh not in tinh_tree: tinh_tree[tinh] = {'sl': 0, 'bcs': {}}
    #     tinh_tree[tinh]['sl'] += sl
    #     if tinh not in tinh_tree[tinh]['tinhs']: tinh_tree[tinh]['bcs'][bc] = sl

    # base_style = """
    # <style>
    #     body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background-color: transparent; }
    #     .table-container { max-height: 380px; overflow-y: auto; border: 1px solid #d3d3d3; border-radius: 4px; }
    #     table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px; background: #fff; }
    #     th { position: sticky; top: 0; z-index: 10; background-color: #c62828; color: #ffffff; text-align: center; padding: 7px 4px; border-bottom: 2px solid #b71c1c; border-right: 1px solid #b71c1c; font-weight: bold; }
    #     tr.total-row td { position: sticky; top: 31px; z-index: 9; background-color: #f5f5f5; font-weight: bold; border-bottom: 2px solid #ccc; }
    #     td { padding: 6px 6px; border-bottom: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0; text-align: center; }
    #     td.col-branch { text-align: left; padding-left: 10px; }
    #     .ton-btn { display: inline-block; width: 14px; height: 14px; line-height: 12px; text-align: center; border: 1px solid #555; background: #fff; color: #333; font-weight: bold; font-size: 9px; cursor: pointer; margin-right: 5px; border-radius: 2px; }
    #     .ton-highlight-red { color: #c62828; font-weight: bold; }
    #     .ton-highlight-orange { color: #e65100; font-weight: bold; }
    # </style>
    # <script>
    #     function toggleTonRow(className, event, btnId) {
    #         if (event) event.stopPropagation();
    #         var rows = document.getElementsByClassName(className);
    #         var btn = document.getElementById(btnId);
    #         if (!rows || rows.length === 0) return;
    #         var isHidden = rows[0].style.display === 'none';
    #         for (var i = 0; i < rows.length; i++) {
    #             rows[i].style.display = isHidden ? 'table-row' : 'none';
    #         }
    #         if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
    #     }
    # </script>
    # """

    # # BẢNG 1: FM
    # st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU FM CÁC BƯU GỬI CHƯA XUẤT SẠCH – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    # fm_rows_html = ""
    # for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
    #     t_sl = t_data['sl']
    #     t_id = f"fm_tinh_{idx_t}"
    #     fm_rows_html += f"""
    #     <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
    #         <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
    #         <td>{t_sl:,.0f}</td><td>{int(t_sl*0.03):,.0f}</td><td>3.0%</td>
    #         <td class="ton-highlight-red">{int(t_sl*0.005):,.0f}</td>
    #         <td class="ton-highlight-orange">{int(t_sl*0.002):,.0f}</td>
    #         <td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
    #     </tr>
    #     """
    #     for b_name, b_sl in t_data['bcs'].items():
    #         fm_rows_html += f"""
    #         <tr class="{t_id}" style="display:none; background-color:#fafafa;">
    #             <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
    #             <td>{b_sl:,.0f}</td><td>{int(b_sl*0.03):,.0f}</td><td>3.0%</td>
    #             <td class="ton-highlight-red">{int(b_sl*0.005):,.0f}</td>
    #             <td class="ton-highlight-orange">{int(b_sl*0.002):,.0f}</td>
    #             <td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
    #         </tr>
    #         """

    # html_fm = f"""
    # <!DOCTYPE html><html><head>{base_style}</head><body>
    # <div class="table-container">
    #     <table>
    #         <thead>
    #             <tr>
    #                 <th style="width: 20%;">Chi Nhánh</th><th style="width: 14%;">Sản lượng đã thu thành công</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Tồn quá 1 ngày</th><th style="width: 11%;">Tồn quá 2 ngày</th><th style="width: 12%;">Tỷ lệ tồn quá 1 ngày</th><th style="width: 12%;">Tỷ lệ tồn quá 2 ngày</th>
    #             </tr>
    #         </thead>
    #         <tbody>
    #             <tr class="total-row">
    #                 <td class="col-branch">TOTAL</td><td>{tong_sl_phat:,.0f}</td><td>{int(tong_sl_phat*0.03):,.0f}</td><td>3.0%</td>
    #                 <td class="ton-highlight-red">{int(tong_sl_phat*0.005):,.0f}</td><td class="ton-highlight-orange">{int(tong_sl_phat*0.002):,.0f}</td><td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
    #             </tr>
    #             {fm_rows_html}
    #         </tbody>
    #     </table>
    # </div>
    # </body></html>
    # """
    # components.html(html_fm, height=390, scrolling=False)

    # # BẢNG 2: MM
    # st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU MM CÁC BƯU GỬI CHƯA KẾT NỐI – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    # html_mm = f"""
    # <!DOCTYPE html><html><head>{base_style}</head><body>
    # <div class="table-container" style="max-height: 220px;">
    #     <table>
    #         <thead>
    #             <tr>
    #                 <th style="width: 20%;">Đơn vị kết nối</th><th style="width: 14%;">Sản lượng đã nhận bàn giao</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Quá 6H</th><th style="width: 11%;">Quá 12H</th><th style="width: 12%;">Quá 24H</th><th style="width: 12%;">Quá 48H</th>
    #             </tr>
    #         </thead>
    #         <tbody>
    #             <tr class="total-row">
    #                 <td class="col-branch">TOTAL</td><td class="ton-highlight-red">222</td><td>1,381</td><td>1.12%</td><td class="ton-highlight-red">111</td><td class="ton-highlight-orange">111</td><td>13</td><td>23</td>
    #             </tr>
    #             <tr><td class="col-branch">TTKT3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
    #             <tr><td class="col-branch">HNIVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
    #             <tr><td class="col-branch">DVVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
    #             <tr><td class="col-branch">DVVTNN3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
    #         </tbody>
    #     </table>
    # </div>
    # </body></html>
    # """
    # components.html(html_mm, height=230, scrolling=False)

    # # BẢNG 3: LM
    # st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU LM CÁC BƯU GỬI CHƯA PHÁT – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    # lm_rows_html = ""
    # for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
    #     t_sl = t_data['sl']
    #     t_id = f"lm_tinh_{idx_t}"
    #     lm_rows_html += f"""
    #     <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
    #         <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
    #         <td>{t_sl:,.0f}</td><td>{int(t_sl*0.04):,.0f}</td><td>4.0%</td>
    #         <td class="ton-highlight-red">{int(t_sl*0.008):,.0f}</td>
    #         <td class="ton-highlight-orange">{int(t_sl*0.003):,.0f}</td>
    #         <td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
    #     </tr>
    #     """
    #     for b_name, b_sl in t_data['bcs'].items():
    #         lm_rows_html += f"""
    #         <tr class="{t_id}" style="display:none; background-color:#fafafa;">
    #             <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
    #             <td>{b_sl:,.0f}</td><td>{int(b_sl*0.04):,.0f}</td><td>4.0%</td>
    #             <td class="ton-highlight-red">{int(b_sl*0.008):,.0f}</td>
    #             <td class="ton-highlight-orange">{int(b_sl*0.003):,.0f}</td>
    #             <td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
    #         </tr>
    #         """

    # html_lm = f"""
    # <!DOCTYPE html><html><head>{base_style}</head><body>
    # <div class="table-container">
    #     <table>
    #         <thead>
    #             <tr>
    #                 <th style="width: 20%;">Chi nhánh</th><th style="width: 14%;">Sản lượng đã phát thành công</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Tồn quá 1 ngày</th><th style="width: 11%;">Tồn quá 2 ngày</th><th style="width: 12%;">Tồn quá 3 ngày</th><th style="width: 12%;">Tồn quá 4 ngày</th>
    #             </tr>
    #         </thead>
    #         <tbody>
    #             <tr class="total-row">
    #                 <td class="col-branch">TOTAL</td><td>{tong_sl_phat:,.0f}</td><td>{int(tong_sl_phat*0.04):,.0f}</td><td>4.0%</td>
    #                 <td class="ton-highlight-red">{int(tong_sl_phat*0.008):,.0f}</td><td class="ton-highlight-orange">{int(tong_sl_phat*0.003):,.0f}</td><td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
    #             </tr>
    #             {lm_rows_html}
    #         </tbody>
    #     </table>
    # </div>
    # </body></html>
    # """
    # components.html(html_lm, height=390, scrolling=False)
