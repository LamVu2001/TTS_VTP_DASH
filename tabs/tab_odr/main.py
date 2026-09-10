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

   # 7. BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH
    st.subheader("📊 BÁO CÁO MA TRẬN CHẤT LƯỢNG VẬN HÀNH")

    try:
        # --- 1. LẤY DANH SÁCH CỘT THỜI GIAN ĐỘNG (7 NGÀY, 5 TUẦN, THÁNG) ---
        days_info = con.execute(f"""
            SELECT 
                CAST(tg_ptc AS DATE) as dt,
                STRFTIME(CAST(tg_ptc AS DATE), '%d/%m') as dt_label
            FROM orders 
            WHERE {where_sql_odr} AND tg_ptc IS NOT NULL 
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 7
        """).fetchdf()

        if not days_info.empty:
            days_info = days_info.sort_values("dt", ascending=True).reset_index(drop=True)
            day_cols = days_info["dt"].tolist()
            day_labels = days_info["dt_label"].tolist()
        else:
            day_cols, day_labels = [], ["--/--"] * 7

        weeks_info = con.execute(f"""
            SELECT 
                'W' || STRFTIME(CAST((DATE_TRUNC('week', CAST(tg_ptc AS DATE) + INTERVAL 1 DAY) - INTERVAL 1 DAY) AS DATE), '%W') as week_label,
                MIN(CAST((DATE_TRUNC('week', CAST(tg_ptc AS DATE) + INTERVAL 1 DAY) - INTERVAL 1 DAY) AS DATE)) as min_date
            FROM orders 
            WHERE {where_sql_odr} AND tg_ptc IS NOT NULL 
            GROUP BY 1 ORDER BY min_date DESC LIMIT 5
        """).fetchdf()

        if not weeks_info.empty:
            weeks_info = weeks_info.sort_values("min_date", ascending=True).reset_index(drop=True)
            week_cols = weeks_info["min_date"].tolist()
            week_labels = weeks_info["week_label"].tolist()
        else:
            week_cols, week_labels = [], ["W--"] * 5

        # Query gom dữ liệu ma trận trực tiếp từ DuckDB
        matrix_df = con.execute(f"""
            SELECT 
                COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt,
                COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh,
                COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc,
                CAST(tg_ptc AS DATE) as date_key,
                CAST((DATE_TRUNC('week', CAST(tg_ptc AS DATE) + INTERVAL 1 DAY) - INTERVAL 1 DAY) AS DATE) as week_key,
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as month_key,
                COUNT(DISTINCT ma_phieugui) as sl_phat,
                COUNT(DISTINCT CASE WHEN danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) as sl_dung_gio,
                COUNT(DISTINCT CASE WHEN PTC_1 = 1 THEN ma_phieugui END) as sl_ptc1,
                COUNT(DISTINCT CASE WHEN PTC_1 = 1 AND danh_gia_giao_hang = 'Giao đúng giờ' THEN ma_phieugui END) as sl_ptc1_dung_gio,
                COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 0 THEN ma_phieugui END) as sl_inday,
                COUNT(DISTINCT CASE WHEN DATEDIFF('day', CAST(ngay_bat_dau_phai_phat AS DATE), CAST(tg_ptc AS DATE)) = 1 THEN ma_phieugui END) as sl_nextday
            FROM orders
            WHERE {where_sql_odr} AND tg_ptc IS NOT NULL
            GROUP BY 1, 2, 3, 4, 5, 6
        """).fetchdf()

        # Hàm helper format class màu xanh/đỏ
        def fmt_diff(val, is_pct_point=False):
            color = "text-green" if val >= 0 else "text-red"
            sign = "+" if val >= 0 else ""
            unit = "%" if not is_pct_point else ""
            return f'<td class="{color}">{sign}{val:.2f}{unit}</td>'

        # Helper tính toán danh sách giá trị theo danh mục
        def calc_row_metrics(df_sub):
            # 7 ngày
            d_phat = [df_sub[df_sub["date_key"] == d]["sl_phat"].sum() for d in day_cols]
            d_dg = [df_sub[df_sub["date_key"] == d]["sl_dung_gio"].sum() for d in day_cols]
            d_p1 = [df_sub[df_sub["date_key"] == d]["sl_ptc1"].sum() for d in day_cols]
            d_p1g = [df_sub[df_sub["date_key"] == d]["sl_ptc1_dung_gio"].sum() for d in day_cols]
            d_in = [df_sub[df_sub["date_key"] == d]["sl_inday"].sum() for d in day_cols]
            d_next = [df_sub[df_sub["date_key"] == d]["sl_nextday"].sum() for d in day_cols]

            # 5 tuần
            w_phat = [df_sub[df_sub["week_key"] == w]["sl_phat"].sum() for w in week_cols]
            w_dg = [df_sub[df_sub["week_key"] == w]["sl_dung_gio"].sum() for w in week_cols]
            w_p1 = [df_sub[df_sub["week_key"] == w]["sl_ptc1"].sum() for w in week_cols]
            w_p1g = [df_sub[df_sub["week_key"] == w]["sl_ptc1_dung_gio"].sum() for w in week_cols]
            w_in = [df_sub[df_sub["week_key"] == w]["sl_inday"].sum() for w in week_cols]
            w_next = [df_sub[df_sub["week_key"] == w]["sl_nextday"].sum() for w in week_cols]

            # Tháng
            m_list = sorted(df_sub["month_key"].dropna().unique().tolist(), reverse=True)
            m_curr_k = m_list[0] if len(m_list) > 0 else ""
            m_prev_k = m_list[1] if len(m_list) > 1 else m_curr_k

            m_curr_df = df_sub[df_sub["month_key"] == m_curr_k]
            m_prev_df = df_sub[df_sub["month_key"] == m_prev_k]

            m_phat_c, m_phat_p = m_curr_df["sl_phat"].sum(), m_prev_df["sl_phat"].sum()
            m_dg_c, m_dg_p = m_curr_df["sl_dung_gio"].sum(), m_prev_df["sl_dung_gio"].sum()
            m_p1_c, m_p1_p = m_curr_df["sl_ptc1"].sum(), m_prev_df["sl_ptc1"].sum()
            m_p1g_c, m_p1g_p = m_curr_df["sl_ptc1_dung_gio"].sum(), m_prev_df["sl_ptc1_dung_gio"].sum()
            m_in_c, m_in_p = m_curr_df["sl_inday"].sum(), m_prev_df["sl_inday"].sum()
            m_next_c, m_next_p = m_curr_df["sl_nextday"].sum(), m_prev_df["sl_nextday"].sum()

            return {
                "d_phat": d_phat, "w_phat": w_phat, "m_phat_p": m_phat_p, "m_phat_c": m_phat_c,
                "d_odr": [(g/p*100) if p>0 else 0 for g,p in zip(d_dg, d_phat)],
                "w_odr": [(g/p*100) if p>0 else 0 for g,p in zip(w_dg, w_phat)],
                "m_odr_p": (m_dg_p/m_phat_p*100) if m_phat_p>0 else 0, "m_odr_c": (m_dg_c/m_phat_c*100) if m_phat_c>0 else 0,
                
                "d_ptc1": [(g/p*100) if p>0 else 0 for g,p in zip(d_p1g, d_p1)],
                "w_ptc1": [(g/p*100) if p>0 else 0 for g,p in zip(w_p1g, w_p1)],
                "m_ptc1_p": (m_p1g_p/m_p1_p*100) if m_p1_p>0 else 0, "m_ptc1_c": (m_p1g_c/m_p1_c*100) if m_p1_c>0 else 0,

                "d_inday": [(i/p*100) if p>0 else 0 for i,p in zip(d_in, d_phat)],
                "w_inday": [(i/p*100) if p>0 else 0 for i,p in zip(w_in, w_phat)],
                "m_inday_p": (m_in_p/m_phat_p*100) if m_phat_p>0 else 0, "m_inday_c": (m_in_c/m_phat_c*100) if m_phat_c>0 else 0,

                "d_nextday": [(n/p*100) if p>0 else 0 for n,p in zip(d_next, d_phat)],
                "w_nextday": [(n/p*100) if p>0 else 0 for n,p in zip(w_next, w_phat)],
                "m_nextday_p": (m_next_p/m_phat_p*100) if m_phat_p>0 else 0, "m_nextday_c": (m_next_c/m_phat_c*100) if m_phat_c>0 else 0,
            }

        # Tính tổng dự án
        root_m = calc_row_metrics(matrix_df)

        dod_phat = ((root_m["d_phat"][-1] - root_m["d_phat"][-2]) / root_m["d_phat"][-2] * 100) if len(root_m["d_phat"]) > 1 and root_m["d_phat"][-2] > 0 else 0
        wow_phat = ((root_m["w_phat"][-1] - root_m["w_phat"][-2]) / root_m["w_phat"][-2] * 100) if len(root_m["w_phat"]) > 1 and root_m["w_phat"][-2] > 0 else 0
        mom_phat = ((root_m["m_phat_c"] - root_m["m_phat_p"]) / root_m["m_phat_p"] * 100) if root_m["m_phat_p"] > 0 else 0

        # --- XÂY DỰNG HTML NÚT CÂY ĐỐI TÁC -> TỈNH -> BƯU CỤC ---
        matrix_rows_html = ""
        for idx_dt, dt_name in enumerate(matrix_df["dt"].unique()):
            df_dt = matrix_df[matrix_df["dt"] == dt_name]
            dt_m = calc_row_metrics(df_dt)
            dt_clean_id = f"dt_{idx_dt}"

            dod_dt = ((dt_m["d_phat"][-1] - dt_m["d_phat"][-2]) / dt_m["d_phat"][-2] * 100) if len(dt_m["d_phat"]) > 1 and dt_m["d_phat"][-2] > 0 else 0
            wow_dt = ((dt_m["w_phat"][-1] - dt_m["w_phat"][-2]) / dt_m["w_phat"][-2] * 100) if len(dt_m["w_phat"]) > 1 and dt_m["w_phat"][-2] > 0 else 0
            mom_dt = ((dt_m["m_phat_c"] - dt_m["m_phat_p"]) / dt_m["m_phat_p"] * 100) if dt_m["m_phat_p"] > 0 else 0

            matrix_rows_html += f"""
            <tr class="sub-row-1 group_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
                <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
                <td>-</td><td>-</td>
                {"".join([f"<td>{v:,.0f}</td>" for v in dt_m["d_phat"]])}
                {fmt_diff(dod_dt)}
                {"".join([f"<td>{v:,.0f}</td>" for v in dt_m["w_phat"]])}
                {fmt_diff(wow_dt)}
                <td>{dt_m["m_phat_p"]:,.0f}</td><td>{dt_m["m_phat_c"]:,.0f}</td>
                {fmt_diff(mom_dt)}
            </tr>
            """

            for idx_tinh, tinh_name in enumerate(df_dt["tinh"].unique()):
                df_tinh = df_dt[df_dt["tinh"] == tinh_name]
                tinh_m = calc_row_metrics(df_tinh)
                tinh_clean_id = f"{dt_clean_id}_tinh_{idx_tinh}"

                dod_tinh = ((tinh_m["d_phat"][-1] - tinh_m["d_phat"][-2]) / tinh_m["d_phat"][-2] * 100) if len(tinh_m["d_phat"]) > 1 and tinh_m["d_phat"][-2] > 0 else 0
                wow_tinh = ((tinh_m["w_phat"][-1] - tinh_m["w_phat"][-2]) / tinh_m["w_phat"][-2] * 100) if len(tinh_m["w_phat"]) > 1 and tinh_m["w_phat"][-2] > 0 else 0
                mom_tinh = ((tinh_m["m_phat_c"] - tinh_m["m_phat_p"]) / tinh_m["m_phat_p"] * 100) if tinh_m["m_phat_p"] > 0 else 0

                matrix_rows_html += f"""
                <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; color: #1565c0;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                    <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh: <b>{tinh_name}</b></td>
                    <td>-</td><td>-</td>
                    {"".join([f"<td>{v:,.0f}</td>" for v in tinh_m["d_phat"]])}
                    {fmt_diff(dod_tinh)}
                    {"".join([f"<td>{v:,.0f}</td>" for v in tinh_m["w_phat"]])}
                    {fmt_diff(wow_tinh)}
                    <td>{tinh_m["m_phat_p"]:,.0f}</td><td>{tinh_m["m_phat_c"]:,.0f}</td>
                    {fmt_diff(mom_tinh)}
                </tr>
                """

                for bc_name in df_tinh["bc"].unique():
                    df_bc = df_tinh[df_tinh["bc"] == bc_name]
                    bc_m = calc_row_metrics(df_bc)

                    dod_bc = ((bc_m["d_phat"][-1] - bc_m["d_phat"][-2]) / bc_m["d_phat"][-2] * 100) if len(bc_m["d_phat"]) > 1 and bc_m["d_phat"][-2] > 0 else 0
                    wow_bc = ((bc_m["w_phat"][-1] - bc_m["w_phat"][-2]) / bc_m["w_phat"][-2] * 100) if len(bc_m["w_phat"]) > 1 and bc_m["w_phat"][-2] > 0 else 0
                    mom_bc = ((bc_m["m_phat_c"] - bc_m["m_phat_p"]) / bc_m["m_phat_p"] * 100) if bc_m["m_phat_p"] > 0 else 0

                    matrix_rows_html += f"""
                    <tr class="sub-row-3 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                        <td style="padding-left: 60px;">• Bưu cục: <b>{bc_name}</b></td>
                        <td>-</td><td>-</td>
                        {"".join([f"<td>{v:,.0f}</td>" for v in bc_m["d_phat"]])}
                        {fmt_diff(dod_bc)}
                        {"".join([f"<td>{v:,.0f}</td>" for v in bc_m["w_phat"]])}
                        {fmt_diff(wow_bc)}
                        <td>{bc_m["m_phat_p"]:,.0f}</td><td>{bc_m["m_phat_c"]:,.0f}</td>
                        {fmt_diff(mom_bc)}
                    </tr>
                    """

        # Pad danh sách tiêu đề nếu thiếu
        while len(day_labels) < 7: day_labels.insert(0, "--/--")
        while len(week_labels) < 5: week_labels.insert(0, "W--")

        dod_odr = root_m["d_odr"][-1] - root_m["d_odr"][-2] if len(root_m["d_odr"]) > 1 else 0
        wow_odr = root_m["w_odr"][-1] - root_m["w_odr"][-2] if len(root_m["w_odr"]) > 1 else 0
        mom_odr = root_m["m_odr_c"] - root_m["m_odr_p"]

        dod_ptc1 = root_m["d_ptc1"][-1] - root_m["d_ptc1"][-2] if len(root_m["d_ptc1"]) > 1 else 0
        wow_ptc1 = root_m["w_ptc1"][-1] - root_m["w_ptc1"][-2] if len(root_m["w_ptc1"]) > 1 else 0
        mom_ptc1 = root_m["m_ptc1_c"] - root_m["m_ptc1_p"]

        dod_in = root_m["d_inday"][-1] - root_m["d_inday"][-2] if len(root_m["d_inday"]) > 1 else 0
        wow_in = root_m["w_inday"][-1] - root_m["w_inday"][-2] if len(root_m["w_inday"]) > 1 else 0
        mom_in = root_m["m_inday_c"] - root_m["m_inday_p"]

        dod_next = root_m["d_nextday"][-1] - root_m["d_nextday"][-2] if len(root_m["d_nextday"]) > 1 else 0
        wow_next = root_m["w_nextday"][-1] - root_m["w_nextday"][-2] if len(root_m["w_nextday"]) > 1 else 0
        mom_next = root_m["m_nextday_c"] - root_m["m_nextday_p"]

        # --- 2. RENDER TABLE HTML ---
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
                    <th rowspan="2" style="width: 24%;">Chỉ tiêu</th>
                    <th rowspan="2" style="width: 4%;">Mục tiêu</th>
                    <th rowspan="2" style="width: 4%;">Kết quả</th>
                    <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                    <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
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
                    <td style="text-align: center;">-</td><td style="text-align: center;">100%</td>
                    {"".join([f"<td>{v:,.0f}</td>" for v in root_m["d_phat"]])}
                    {fmt_diff(dod_phat)}
                    {"".join([f"<td>{v:,.0f}</td>" for v in root_m["w_phat"]])}
                    {fmt_diff(wow_phat)}
                    <td>{root_m["m_phat_p"]:,.0f}</td><td><b>{root_m["m_phat_c"]:,.0f}</b></td>
                    {fmt_diff(mom_phat)}
                </tr>

                {matrix_rows_html}

                <!-- 2. % PHÁT THÀNH CÔNG ĐÚNG GIỜ (ODR) -->
                <tr>
                    <td style="font-weight: bold;">% Phát thành công đg (ODR)</td>
                    <td style="text-align: center;">99.00</td><td style="text-align: center;">100.00</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["d_odr"]])}
                    {fmt_diff(dod_odr, is_pct_point=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["w_odr"]])}
                    {fmt_diff(wow_odr, is_pct_point=True)}
                    <td>{root_m["m_odr_p"]:.2f}</td><td><b>{root_m["m_odr_c"]:.2f}</b></td>
                    {fmt_diff(mom_odr, is_pct_point=True)}
                </tr>

                <!-- 3. % PHÁT THÀNH CÔNG ĐÚNG GIỜ LẦN 1 -->
                <tr>
                    <td style="font-weight: bold;">% Phát thành công đg lần 1</td>
                    <td style="text-align: center;">98.00</td><td style="text-align: center;">100.00</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["d_ptc1"]])}
                    {fmt_diff(dod_ptc1, is_pct_point=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["w_ptc1"]])}
                    {fmt_diff(wow_ptc1, is_pct_point=True)}
                    <td>{root_m["m_ptc1_p"]:.2f}</td><td><b>{root_m["m_ptc1_c"]:.2f}</b></td>
                    {fmt_diff(mom_ptc1, is_pct_point=True)}
                </tr>

                <!-- 4. % PTC IN-DAY -->
                <tr>
                    <td style="font-weight: bold;">% PTC in-day</td>
                    <td style="text-align: center;">80.00</td><td style="text-align: center;">100.00</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["d_inday"]])}
                    {fmt_diff(dod_in, is_pct_point=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["w_inday"]])}
                    {fmt_diff(wow_in, is_pct_point=True)}
                    <td>{root_m["m_inday_p"]:.2f}</td><td><b>{root_m["m_inday_c"]:.2f}</b></td>
                    {fmt_diff(mom_in, is_pct_point=True)}
                </tr>

                <!-- 5. % PTC NEXT-DAY -->
                <tr>
                    <td style="font-weight: bold;">% PTC Next-day</td>
                    <td style="text-align: center;">20.00</td><td style="text-align: center;">100.00</td>
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["d_nextday"]])}
                    {fmt_diff(dod_next, is_pct_point=True)}
                    {"".join([f"<td>{v:.2f}</td>" for v in root_m["w_nextday"]])}
                    {fmt_diff(wow_next, is_pct_point=True)}
                    <td>{root_m["m_nextday_p"]:.2f}</td><td><b>{root_m["m_nextday_c"]:.2f}</b></td>
                    {fmt_diff(mom_next, is_pct_point=True)}
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
                    if (!isHidden) {{
                        var childClasses = rows[i].className.split(' ');
                        for (var j = 0; j < childClasses.length; j++) {{
                            if (childClasses[j].startsWith('dt_')) {{
                                var subRows = document.getElementsByClassName(childClasses[j]);
                                for (var k = 0; k < subRows.length; k++) subRows[k].style.display = 'none';
                            }}
                        }}
                    }}
                }}
                if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
            }}
        </script></body></html>
        """
        components.html(matrix_full_html, height=520, scrolling=True)

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
