import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date, datetime  # <-- THÊM DÒNG NÀY VÀO ĐẦU FILE

from data_loader import get_connection


def render(file_id=None):
    # Lấy kết nối DuckDB dùng chung
    try:
        con = get_connection(file_id)
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        return
    st.markdown('<div style="height: 3px; background-color: #c62828; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
   # ---------------------------------------------------------
    # 1. KHỞI TẠO STATE BỘ LỌC CHO TAB DOANH THU
    # ---------------------------------------------------------
    if "f_dt_date" not in st.session_state or not st.session_state.f_dt_date:
        today = date.today()
        first_day_of_month = today.replace(day=1)
        st.session_state.f_dt_date = (first_day_of_month, today)

    if "f_dt_kh" not in st.session_state: st.session_state.f_dt_kh = []
    if "f_dt_ld" not in st.session_state: st.session_state.f_dt_ld = []
    if "f_dt_tl" not in st.session_state: st.session_state.f_dt_tl = []

    # Hàm trợ giúp tạo mệnh đề SQL IN (...) an toàn
    def sql_in_clause(column_name, selected_list):
        if not selected_list:
            return None
        escaped = [str(x).replace("'", "''") for x in selected_list]
        vals = ", ".join([f"'{x}'" for x in escaped])
        return f"CAST({column_name} AS VARCHAR) IN ({vals})"

    # Hàm dựng câu lệnh WHERE cho Cross-Filtering Tab Doanh Thu
    def build_where_dt(exclude=None):
        conds = ["1=1"]
        
        # Sửa ép kiểu CAST AS DATE chuẩn xác giống Tab ODR
        if exclude != "date" and isinstance(st.session_state.f_dt_date, (list, tuple)) and len(st.session_state.f_dt_date) == 2:
            conds.append(f"CAST(tg_ptc AS DATE) BETWEEN '{st.session_state.f_dt_date[0]}' AND '{st.session_state.f_dt_date[1]}'")

        
        if exclude != "kh":
            c = sql_in_clause("ma_khgui", st.session_state.f_dt_kh)
            if c: conds.append(c)
        if exclude != "ld":
            c = sql_in_clause("ma_dv_viettel", st.session_state.f_dt_ld)
            if c: conds.append(c)
        if exclude != "tl":
            c = sql_in_clause("nhom_trong_luong", st.session_state.f_dt_tl)
            if c: conds.append(c)
            
        return " AND ".join(conds)

    # MỆNH ĐỀ WHERE TOÀN CỤC LỌC DỮ LIỆU
    where_sql_dt = build_where_dt()

    # ---------------------------------------------------------
    # 2. LẤY DANH SÁCH OPTION TỰ ĐỘNG (CROSS-FILTERING)
    # ---------------------------------------------------------
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE {build_where_dt('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    ld_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_dv_viettel AS VARCHAR) FROM orders WHERE {build_where_dt('ld')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(nhom_trong_luong AS VARCHAR) FROM orders WHERE {build_where_dt('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]

    # Validate lọc sạch các value cũ không còn nằm trong danh sách tùy chọn mới
    st.session_state.f_dt_kh = [v for v in st.session_state.f_dt_kh if v in kh_opts]
    st.session_state.f_dt_ld = [v for v in st.session_state.f_dt_ld if v in ld_opts]
    st.session_state.f_dt_tl = [v for v in st.session_state.f_dt_tl if v in tl_opts]

    # ---------------------------------------------------------
    # 3. HIỂN THỊ BỘ LỌC NGANG DÀN ĐỀU 4 CỘT
    # ---------------------------------------------------------
    dtf1, dtf2, dtf3, dtf4 = st.columns(4)

    with dtf1:
        st.date_input("NGÀY", key="f_dt_date")
    with dtf2:
        st.multiselect("MÃ KHÁCH HÀNG", kh_opts, key="f_dt_kh", placeholder="Tất cả")
    with dtf3:
        st.multiselect("LOẠI ĐƠN (DV)", ld_opts, key="f_dt_ld", placeholder="Tất cả")
    with dtf4:
        st.multiselect("TRỌNG LƯỢNG", tl_opts, key="f_dt_tl", placeholder="Tất cả")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 4. HIỂN THỊ METRICS TỔNG QUAN
    # ---------------------------------------------------------
    try:
        res_metrics = con.execute(f"""
            SELECT 
                COALESCE(SUM(tong_cuoc), 0) / 1e9 AS tong_doanh_thu,
                COUNT(ma_phieugui) AS tong_san_luong
            FROM orders 
            WHERE {where_sql_dt}
        """).fetchone()

        tong_dt = res_metrics[0] if res_metrics and res_metrics[0] else 0.0
        tong_sl = res_metrics[1] if res_metrics and res_metrics[1] else 0
    except Exception as e:
        st.error(f"Lỗi tính toán metrics: {e}")
        tong_dt, tong_sl = 0.0, 0

    m1, m2 = st.columns(2)

    with m1:
        st.metric(
            label="TỔNG DOANH THU",
            value = f"{(tong_dt or 0):,.2f} tỷ"
        )

    with m2:
        st.metric(
            label="TỔNG SẢN LƯỢNG",
            value=f"{tong_sl:,.0f}"
        )
    
   # chia 2 cột: Trái (Biểu đồ - 2 phần), Phải (Bảng - 1.3 phần)
    c_dt_chart, c_dt_right = st.columns([2, 1.3])

    # ---------------------------------------------------------
    # CỘT TRÁI: BIỂU ĐỒ XU HƯỚNG DOANH THU
    # ---------------------------------------------------------
    with c_dt_chart:
        st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:8px;">XU HƯỚNG DOANH THU</div>', unsafe_allow_html=True)


        time_view_dt = st.radio(
            "Chế độ xem:",
            options=["Ngày", "Tuần", "Tháng"],
            index=0,
            horizontal=True,
            key="dt_chart_time_view",
            label_visibility="collapsed",
        )

        try:
            if time_view_dt == "Tuần":
                date_expr_dt = "CAST((DATE_TRUNC('week', CAST(tg_ptc AS DATE) + INTERVAL 1 DAY) - INTERVAL 1 DAY) AS DATE)"
                date_format_dt = "%d/%m/%Y"
            elif time_view_dt == "Tháng":
                date_expr_dt = "DATE_TRUNC('month', CAST(tg_ptc AS DATE))"
                date_format_dt = "%m/%Y"
            else:
                date_expr_dt = "CAST(tg_ptc AS DATE)"
                date_format_dt = "%d/%m/%Y"

            df_dt_trend = con.execute(f"""
                SELECT 
                    STRFTIME({date_expr_dt}, '{date_format_dt}') as time_label, 
                    COALESCE(SUM(tong_cuoc), 0) / 1e9 as doanh_thu_ty,
                    MIN({date_expr_dt}) as sort_key
                FROM orders 
                WHERE {where_sql_dt} AND tg_ptc IS NOT NULL
                GROUP BY 1
                ORDER BY sort_key ASC
            """).fetchdf()

            if len(df_dt_trend) > 0:
                fig_dt = go.Figure()
                fig_dt.add_trace(
                    go.Scatter(
                        x=df_dt_trend["time_label"],
                        y=df_dt_trend["doanh_thu_ty"],
                        name="Doanh thu (Tỷ)",
                        mode="lines+markers+text",
                        text=df_dt_trend["doanh_thu_ty"].apply(lambda x: f"{x:,.2f}"),
                        textposition="top center",
                        textfont=dict(size=10, color="#800000", family="Arial Black"),
                        line=dict(color="#c62828", width=2.5),
                        marker=dict(size=6, color="#c62828"),
                    )
                )

                max_val = df_dt_trend["doanh_thu_ty"].max() if not df_dt_trend.empty else 1.0

                fig_dt.update_layout(
                    height=410,
                    margin=dict(l=10, r=10, t=35, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=11)),
                    xaxis=dict(type="category", title=None, tickangle=-35, tickfont=dict(size=10, color="#333333")),
                    yaxis=dict(title="Tỷ đồng", showgrid=True, gridcolor="#eeeeee", zeroline=True, zerolinecolor="#cccccc", range=[0, max_val * 1.25]),
                    hovermode="x unified",
                    plot_bgcolor="#ffffff",
                )

                st.plotly_chart(fig_dt, use_container_width=True, config={"displayModeBar": False})
            else:
                st.warning("Không có dữ liệu doanh thu trong khoảng thời gian đã chọn.")
        except Exception as e:
            st.error(f"Lỗi tính toán biểu đồ doanh thu: {e}")

    # ---------------------------------------------------------
    # CỘT PHẢI: BẢNG TOP 10 KHÁCH HÀNG (FULL SỐ DOANH THU)
    # ---------------------------------------------------------
    with c_dt_right:
        st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:8px;">TOP 10 DOANH THU THEO KHÁCH HÀNG</div>', unsafe_allow_html=True)

        try:
            # Lấy đầy đủ số tiền thực tế (SUM tong_cuoc không chia cho 1e6 hay 1e9)
            df_top_kh = con.execute(f"""
                SELECT 
                    CAST(ma_khgui AS VARCHAR) AS "MÃ KH",
                    COALESCE(SUM(tong_cuoc), 0) AS "DOANH THU (VNĐ)"
                FROM orders
                WHERE {where_sql_dt} AND ma_khgui IS NOT NULL
                GROUP BY 1
                ORDER BY "DOANH THU (VNĐ)" DESC
                LIMIT 10
            """).fetchdf()

            if len(df_top_kh) > 0:
                # Định dạng hiển thị bảng chuẩn đẹp, đẩy ra đầy đủ con số kèm dấu phân cách
                st.dataframe(
                    df_top_kh,
                    use_container_width=True,
                    height=410,
                    hide_index=True,
                    column_config={
                        "MÃ KH": st.column_config.TextColumn(
                            "MÃ KHÁCH HÀNG",
                            width="medium",
                        ),
                        "DOANH THU (VNĐ)": st.column_config.NumberColumn(
                            "DOANH THU (VNĐ)",
                            format="%,.0f VNĐ",  # Đẩy full số tiền nguyên bản, có dấu phẩy
                            width="large",
                        ),
                    }
                )
            else:
                st.info("Không có dữ liệu khách hàng trong khoảng thời gian đã chọn.")
        except Exception as e:
            st.error(f"Lỗi truy vấn Top khách hàng: {e}")
    st.divider()
    # ---------------------------------------------------------
    # BÁO CÁO MA TRẬN DOANH THU & SẢN LƯỢNG (LÀM TRÒN DT & FIX BUNG CÂY)
    # ---------------------------------------------------------
    st.markdown('<div style="font-size:20px; font-weight:bold; color:#111; border-left:4px solid #c62828; padding-left:8px; margin-top:5px; margin-bottom:8px;">BÁO CÁO MA TRẬN DOANH THU & SẢN LƯỢNG</div>', unsafe_allow_html=True)

    try:
        from collections import defaultdict

        base_where = f"WHERE {where_sql_dt}" if where_sql_dt else ""

        # 1. LẤY MỐC THỜI GIAN
        days_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as dt, 
                STRFTIME(CAST(tg_ptc AS DATE), '%d/%m') as dt_label
            FROM orders {base_where}
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 7
        """).fetchdf()

        day_cols, day_labels = [], []
        if days_df is not None and not days_df.empty:
            day_cols = days_df["dt"].dropna().tolist()[::-1]
            day_labels = days_df["dt_label"].dropna().tolist()[::-1]

        weeks_df = con.execute(f"""
            SELECT 
                STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as min_date,
                'W' || STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%W') as week_label
            FROM orders {base_where}
            GROUP BY 1, 2 ORDER BY 1 DESC LIMIT 5
        """).fetchdf()

        week_cols, week_labels = [], []
        if weeks_df is not None and not weeks_df.empty:
            week_cols = weeks_df["min_date"].dropna().tolist()[::-1]
            week_labels = weeks_df["week_label"].dropna().tolist()[::-1]

        months_df = con.execute(f"""
            SELECT DISTINCT STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key
            FROM orders {base_where}
            ORDER BY 1 DESC LIMIT 2
        """).fetchdf()

        month_cols = []
        if months_df is not None and not months_df.empty:
            month_cols = months_df["m_key"].dropna().tolist()[::-1]
        while len(month_cols) < 2:
            month_cols.insert(0, f"M_empty_{len(month_cols)}")

        # 2. AGGREGATE BẢNG TỔNG
        df_d = con.execute(f"""
            SELECT STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt
            FROM orders {base_where} GROUP BY 1
        """).fetchdf()

        df_w = con.execute(f"""
            SELECT STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as w_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt
            FROM orders {base_where} GROUP BY 1
        """).fetchdf()

        df_m = con.execute(f"""
            SELECT STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt
            FROM orders {base_where} GROUP BY 1
        """).fetchdf()

        dict_d = {str(row.d_key): row for row in df_d.itertuples()} if df_d is not None and not df_d.empty else {}
        dict_w = {str(row.w_key): row for row in df_w.itertuples()} if df_w is not None and not df_w.empty else {}
        dict_m = {str(row.m_key): row for row in df_m.itertuples()} if df_m is not None and not df_m.empty else {}

        def get_v_fast(d_map, key, field_idx):
            k_str = str(key)
            if k_str in d_map:
                try:
                    val = d_map[k_str][field_idx]
                    if val is not None and val == val: return float(val)
                except Exception:
                    pass
            return 0.0

        v_d_sl = [get_v_fast(dict_d, d, 2) for d in day_cols]
        v_d_dt = [get_v_fast(dict_d, d, 3) for d in day_cols]

        v_w_sl = [get_v_fast(dict_w, w, 2) for w in week_cols]
        v_w_dt = [get_v_fast(dict_w, w, 3) for w in week_cols]

        v_m_sl = [get_v_fast(dict_m, m, 2) for m in month_cols]
        v_m_dt = [get_v_fast(dict_m, m, 3) for m in month_cols]

        def fmt_diff(val):
            color = "text-green" if val >= 0 else "text-red"
            sign = "+" if val >= 0 else ""
            return f'<td class="{color}">{sign}{val:.2f}%</td>'

        dod_sl = ((v_d_sl[-1] - v_d_sl[-2])/v_d_sl[-2]*100) if len(v_d_sl)>1 and v_d_sl[-2]>0 else 0
        wow_sl = ((v_w_sl[-1] - v_w_sl[-2])/v_w_sl[-2]*100) if len(v_w_sl)>1 and v_w_sl[-2]>0 else 0
        mom_sl = ((v_m_sl[1] - v_m_sl[0])/v_m_sl[0]*100) if len(v_m_sl)>1 and v_m_sl[0]>0 else 0

        dod_dt = ((v_d_dt[-1] - v_d_dt[-2])/v_d_dt[-2]*100) if len(v_d_dt)>1 and v_d_dt[-2]>0 else 0
        wow_dt = ((v_w_dt[-1] - v_w_dt[-2])/v_w_dt[-2]*100) if len(v_w_dt)>1 and v_w_dt[-2]>0 else 0
        mom_dt = ((v_m_dt[1] - v_m_dt[0])/v_m_dt[0]*100) if len(v_m_dt)>1 and v_m_dt[0]>0 else 0

        # 3. TRUY VẤN CHI TIẾT
        kh_day_df = con.execute(f"SELECT COALESCE(CAST(ma_khgui AS VARCHAR), 'Chua xác dinh') as kh, STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2").fetchdf()
        kh_week_df = con.execute(f"SELECT COALESCE(CAST(ma_khgui AS VARCHAR), 'Chua xác dinh') as kh, STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as w_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2").fetchdf()
        kh_month_df = con.execute(f"SELECT COALESCE(CAST(ma_khgui AS VARCHAR), 'Chua xác dinh') as kh, STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2").fetchdf()

        tree_day_df = con.execute(f"SELECT COALESCE(CAST(tinh_phat AS VARCHAR), 'Chua xác dinh') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Chua xác dinh') as bc, STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m-%d') as d_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2, 3").fetchdf()
        tree_week_df = con.execute(f"SELECT COALESCE(CAST(tinh_phat AS VARCHAR), 'Chua xác dinh') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Chua xác dinh') as bc, STRFTIME(CAST(DATE_TRUNC('week', CAST(tg_ptc AS DATE)) AS DATE), '%Y-%m-%d') as w_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2, 3").fetchdf()
        tree_month_df = con.execute(f"SELECT COALESCE(CAST(tinh_phat AS VARCHAR), 'Chua xác dinh') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Chua xác dinh') as bc, STRFTIME(CAST(tg_ptc AS DATE), '%Y-%m') as m_key, COUNT(DISTINCT ma_phieugui) as sl, COALESCE(SUM(tong_cuoc), 0) as dt FROM orders {base_where} GROUP BY 1, 2, 3").fetchdf()

        map_kh_d_sl, map_kh_w_sl, map_kh_m_sl = {}, {}, {}
        map_kh_d_dt, map_kh_w_dt, map_kh_m_dt = {}, {}, {}
        
        if kh_day_df is not None and not kh_day_df.empty:
            for r in kh_day_df.itertuples(): 
                map_kh_d_sl[(str(r.kh), str(r.d_key))] = r.sl
                map_kh_d_dt[(str(r.kh), str(r.d_key))] = r.dt
        if kh_week_df is not None and not kh_week_df.empty:
            for r in kh_week_df.itertuples(): 
                map_kh_w_sl[(str(r.kh), str(r.w_key))] = r.sl
                map_kh_w_dt[(str(r.kh), str(r.w_key))] = r.dt
        if kh_month_df is not None and not kh_month_df.empty:
            for r in kh_month_df.itertuples(): 
                map_kh_m_sl[(str(r.kh), str(r.m_key))] = r.sl
                map_kh_m_dt[(str(r.kh), str(r.m_key))] = r.dt

        map_tinh_d_sl, map_bc_d_sl, map_tinh_d_dt, map_bc_d_dt = defaultdict(float), {}, defaultdict(float), {}
        if tree_day_df is not None and not tree_day_df.empty:
            for r in tree_day_df.itertuples():
                map_tinh_d_sl[(str(r.tinh), str(r.d_key))] += r.sl
                map_bc_d_sl[(str(r.tinh), str(r.bc), str(r.d_key))] = r.sl
                map_tinh_d_dt[(str(r.tinh), str(r.d_key))] += r.dt
                map_bc_d_dt[(str(r.tinh), str(r.bc), str(r.d_key))] = r.dt

        map_tinh_w_sl, map_bc_w_sl, map_tinh_w_dt, map_bc_w_dt = defaultdict(float), {}, defaultdict(float), {}
        if tree_week_df is not None and not tree_week_df.empty:
            for r in tree_week_df.itertuples():
                map_tinh_w_sl[(str(r.tinh), str(r.w_key))] += r.sl
                map_bc_w_sl[(str(r.tinh), str(r.bc), str(r.w_key))] = r.sl
                map_tinh_w_dt[(str(r.tinh), str(r.w_key))] += r.dt
                map_bc_w_dt[(str(r.tinh), str(r.bc), str(r.w_key))] = r.dt

        map_tinh_m_sl, map_bc_m_sl, map_tinh_m_dt, map_bc_m_dt = defaultdict(float), {}, defaultdict(float), {}
        if tree_month_df is not None and not tree_month_df.empty:
            for r in tree_month_df.itertuples():
                map_tinh_m_sl[(str(r.tinh), str(r.m_key))] += r.sl
                map_bc_m_sl[(str(r.tinh), str(r.bc), str(r.m_key))] = r.sl
                map_tinh_m_dt[(str(r.tinh), str(r.m_key))] += r.dt
                map_bc_m_dt[(str(r.tinh), str(r.bc), str(r.m_key))] = r.dt

        kh_df_raw = con.execute(f"SELECT DISTINCT COALESCE(CAST(ma_khgui AS VARCHAR), 'Chua xác dinh') as kh FROM orders {base_where} ORDER BY 1").fetchdf()
        kh_list = kh_df_raw["kh"].dropna().tolist() if kh_df_raw is not None and not kh_df_raw.empty else []

        tinh_bc_df = con.execute(f"SELECT DISTINCT COALESCE(CAST(tinh_phat AS VARCHAR), 'Chua xác dinh') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Chua xác dinh') as bc FROM orders {base_where} ORDER BY 1, 2").fetchdf()
        
        tinh_hierarchy = defaultdict(list)
        if tinh_bc_df is not None and not tinh_bc_df.empty:
            for r in tinh_bc_df.itertuples():
                tinh_hierarchy[str(r.tinh)].append(str(r.bc))

        # Helper render cây đa cấp (Fix lỗi bung bưu cục + Làm tròn doanh thu)
        def generate_tree_rows(prefix, map_kh_d, map_kh_w, map_kh_m, map_tinh_d, map_bc_d, map_tinh_w, map_bc_w, map_tinh_m, map_bc_m, is_currency=False):
            rows = []
            def fmt_val(v): return f"{round(v):,.0f}" if is_currency else f"{v:,.0f}"

            # 1. NHÓM THEO MÃ KHÁCH HÀNG
            if kh_list:
                kh_header_id = f"group_{prefix}_kh_header"
                rows.append(f"""
                <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #f0f0f0; font-weight:bold; cursor: pointer;" onclick="toggleRow('{kh_header_id}', event, 'btn_{kh_header_id}')">
                    <td style="padding-left: 15px;" colspan="100%"><span class="toggle-btn" id="btn_{kh_header_id}">[+]</span> Theo mã khách hàng</td>
                </tr>
                """)
                for kh_name in kh_list:
                    d_vals = [map_kh_d.get((kh_name, str(d)), 0) for d in day_cols]
                    w_vals = [map_kh_w.get((kh_name, str(w)), 0) for w in week_cols]
                    m_vals = [map_kh_m.get((kh_name, str(m)), 0) for m in month_cols]

                    dod = ((d_vals[-1] - d_vals[-2])/d_vals[-2]*100) if len(d_vals)>1 and d_vals[-2]>0 else 0
                    wow = ((w_vals[-1] - w_vals[-2])/w_vals[-2]*100) if len(w_vals)>1 and w_vals[-2]>0 else 0
                    mom = ((m_vals[1] - m_vals[0])/m_vals[0]*100) if len(m_vals)>1 and m_vals[0]>0 else 0

                    d_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in d_vals])
                    w_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in w_vals])
                    m0 = m_vals[0] if len(m_vals) > 0 else 0
                    m1 = m_vals[1] if len(m_vals) > 1 else m0

                    rows.append(f"""
                    <tr class="sub-row-2 {kh_header_id}" style="display:none;">
                        <td style="padding-left: 35px;">Mã KH: <b>{kh_name}</b></td>
                        {d_cells}{fmt_diff(dod)}{w_cells}{fmt_diff(wow)}<td>{fmt_val(m0)}</td><td><b>{fmt_val(m1)}</b></td>{fmt_diff(mom)}
                    </tr>
                    """)

            # 2. NHÓM THEO TỈNH PHÁT & BƯU CỤC PHÁT
            if tinh_hierarchy:
                tinh_header_id = f"group_{prefix}_tinh_header"
                rows.append(f"""
                <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #f0f0f0; font-weight:bold; cursor: pointer;" onclick="toggleRow('{tinh_header_id}', event, 'btn_{tinh_header_id}')">
                    <td style="padding-left: 15px;" colspan="100%"><span class="toggle-btn" id="btn_{tinh_header_id}">[+]</span> Theo tỉnh phát & bưu cục phát</td>
                </tr>
                """)
                for idx_tinh, (tinh_name, bcs_list) in enumerate(tinh_hierarchy.items()):
                    tinh_clean_id = f"{prefix}_tinh_{idx_tinh}"
                    
                    d_vals_tinh = [map_tinh_d.get((tinh_name, str(d)), 0) for d in day_cols]
                    w_vals_tinh = [map_tinh_w.get((tinh_name, str(w)), 0) for w in week_cols]
                    m_vals_tinh = [map_tinh_m.get((tinh_name, str(m)), 0) for m in month_cols]

                    dod_tinh = ((d_vals_tinh[-1] - d_vals_tinh[-2])/d_vals_tinh[-2]*100) if len(d_vals_tinh)>1 and d_vals_tinh[-2]>0 else 0
                    wow_tinh = ((w_vals_tinh[-1] - w_vals_tinh[-2])/w_vals_tinh[-2]*100) if len(w_vals_tinh)>1 and w_vals_tinh[-2]>0 else 0
                    mom_tinh = ((m_vals_tinh[1] - m_vals_tinh[0])/m_vals_tinh[0]*100) if len(m_vals_tinh)>1 and m_vals_tinh[0]>0 else 0

                    t_d_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in d_vals_tinh])
                    t_w_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in w_vals_tinh])
                    tm0 = m_vals_tinh[0] if len(m_vals_tinh) > 0 else 0
                    tm1 = m_vals_tinh[1] if len(m_vals_tinh) > 1 else tm0

                    rows.append(f"""
                    <tr class="sub-row-2 {tinh_header_id}" style="display:none; background-color: #fcfcfc; cursor: pointer;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                        <td style="padding-left: 35px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh: <b>{tinh_name}</b></td>
                        {t_d_cells}{fmt_diff(dod_tinh)}{t_w_cells}{fmt_diff(wow_tinh)}<td>{fmt_val(tm0)}</td><td><b>{fmt_val(tm1)}</b></td>{fmt_diff(mom_tinh)}
                    </tr>
                    """)

                    for bc_name in bcs_list:
                        d_vals_bc = [map_bc_d.get((tinh_name, bc_name, str(d)), 0) for d in day_cols]
                        w_vals_bc = [map_bc_w.get((tinh_name, bc_name, str(w)), 0) for w in week_cols]
                        m_vals_bc = [map_bc_m.get((tinh_name, bc_name, str(m)), 0) for m in month_cols]

                        dod_bc = ((d_vals_bc[-1] - d_vals_bc[-2])/d_vals_bc[-2]*100) if len(d_vals_bc)>1 and d_vals_bc[-2]>0 else 0
                        wow_bc = ((w_vals_bc[-1] - w_vals_bc[-2])/w_vals_bc[-2]*100) if len(w_vals_bc)>1 and w_vals_bc[-2]>0 else 0
                        mom_bc = ((m_vals_bc[1] - m_vals_bc[0])/m_vals_bc[0]*100) if len(m_vals_bc)>1 and m_vals_bc[0]>0 else 0

                        b_d_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in d_vals_bc])
                        b_w_cells = "".join([f"<td>{fmt_val(v)}</td>" for v in w_vals_bc])
                        bm0 = m_vals_bc[0] if len(m_vals_bc) > 0 else 0
                        bm1 = m_vals_bc[1] if len(m_vals_bc) > 1 else bm0

                        # SỬA TẠI ĐÂY: Xóa tinh_header_id để Bưu cục không bị bung cùng lúc với Tỉnh
                        rows.append(f"""
                        <tr class="sub-row-3 {tinh_clean_id}" style="display:none; color: #555;">
                            <td style="padding-left: 55px;">- Bưu cục: {bc_name}</td>
                            {b_d_cells}{fmt_diff(dod_bc)}{b_w_cells}{fmt_diff(wow_bc)}<td>{fmt_val(bm0)}</td><td><b>{fmt_val(bm1)}</b></td>{fmt_diff(mom_bc)}
                        </tr>
                        """)
            return "".join(rows)

        sl_rows_html = generate_tree_rows("sl", map_kh_d_sl, map_kh_w_sl, map_kh_m_sl, map_tinh_d_sl, map_bc_d_sl, map_tinh_w_sl, map_bc_w_sl, map_tinh_m_sl, map_bc_m_sl, is_currency=False)
        dt_rows_html = generate_tree_rows("dt", map_kh_d_dt, map_kh_w_dt, map_kh_m_dt, map_tinh_d_dt, map_bc_d_dt, map_tinh_w_dt, map_bc_w_dt, map_tinh_m_dt, map_bc_m_dt, is_currency=True)

        n_day_cols = len(day_labels)
        n_week_cols = len(week_labels)

        m0_sl = v_m_sl[0] if len(v_m_sl) > 0 else 0
        m1_sl = v_m_sl[1] if len(v_m_sl) > 1 else m0_sl

        m0_dt = v_m_dt[0] if len(v_m_dt) > 0 else 0
        m1_dt = v_m_dt[1] if len(v_m_dt) > 1 else m0_dt

        # 4. RENDER HTML 
        matrix_full_html = f"""
        <!DOCTYPE html><html><head><style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }}
            .matrix-table {{ width: 100%; border-collapse: collapse; font-size: 11px; background-color: #ffffff; color: #222222; border: 1px solid #ccc; }}
            .matrix-table th {{ background-color: #333333; color: #ffffff; text-align: center; padding: 5px 3px; border: 1px solid #555; font-weight: 600; }}
            .matrix-table td {{ padding: 5px 6px; border: 1px solid #e0e0e0; vertical-align: middle; text-align: right; }}
            .matrix-table td:first-child {{ text-align: left; }}
            .row-group {{ font-weight: bold; background-color: #f5f5f5; cursor: pointer; }}
            .toggle-btn {{ display: inline-block; width: 15px; height: 15px; line-height: 13px; text-align: center; border: 1px solid #666; background: #fff; color: #333; font-weight: bold; font-size: 10px; cursor: pointer; margin-right: 4px; border-radius: 2px; }}
            .text-green {{ color: #2e7d32; font-weight: bold; }}
            .text-red {{ color: #c62828; font-weight: bold; }}
        </style></head><body>
        <table class="matrix-table">
            <thead>
                <tr>
                    <th rowspan="2" style="width: 25%;">Chỉ tiêu</th>
                    <th colspan="{n_day_cols + 1}">{n_day_cols} ngày gần nhất</th>
                    <th colspan="{n_week_cols + 1}">{n_week_cols} tuần gần nhất</th>
                    <th colspan="3">Tháng</th>
                </tr>
                <tr>
                    {"".join([f"<th>{d}</th>" for d in day_labels])}<th>DoD</th>
                    {"".join([f"<th>{w}</th>" for w in week_labels])}<th>WoW</th>
                    <th>M-1</th><th>M</th><th>MoM</th>
                </tr>
            </thead>
            <tbody>
                <!-- 1. SẢN LƯỢNG PHÁT -->
                <tr class="row-group" onclick="toggleRow('group_sl_root', event, 'btn_sl_root')">
                    <td><span class="toggle-btn" id="btn_sl_root">[+]</span> <b>Sản lượng phát (Đơn)</b></td>
                    {"".join([f"<td>{v:,.0f}</td>" for v in v_d_sl])}
                    {fmt_diff(dod_sl)}
                    {"".join([f"<td>{v:,.0f}</td>" for v in v_w_sl])}
                    {fmt_diff(wow_sl)}
                    <td>{m0_sl:,.0f}</td><td><b>{m1_sl:,.0f}</b></td>
                    {fmt_diff(mom_sl)}
                </tr>
                {sl_rows_html}

                <!-- 2. DOANH THU -->
                <tr class="row-group" onclick="toggleRow('group_dt_root', event, 'btn_dt_root')">
                    <td><span class="toggle-btn" id="btn_dt_root">[+]</span> <b>Doanh thu (VNĐ)</b></td>
                    {"".join([f"<td>{round(v):,.0f}</td>" for v in v_d_dt])}
                    {fmt_diff(dod_dt)}
                    {"".join([f"<td>{round(v):,.0f}</td>" for v in v_w_dt])}
                    {fmt_diff(wow_dt)}
                    <td>{round(m0_dt):,.0f}</td><td><b>{round(m1_dt):,.0f}</b></td>
                    {fmt_diff(mom_dt)}
                </tr>
                {dt_rows_html}
            </tbody>
        </table>

        <script>
            // SỬA TẠI ĐÂY: JS ẩn dây chuyên sâu, khi đóng cấp trên sẽ ẩn toàn bộ cấp dưới
            function toggleRow(className, event, btnId) {{
                if (event) event.stopPropagation();
                var rows = document.getElementsByClassName(className);
                var btn = document.getElementById(btnId);
                if (!rows || rows.length === 0) return;
                
                var isHidden = rows[0].style.display === 'none';
                for (var i = 0; i < rows.length; i++) {{
                    if (isHidden) {{
                        rows[i].style.display = 'table-row';
                    }} else {{
                        rows[i].style.display = 'none';
                        var subBtns = rows[i].getElementsByClassName('toggle-btn');
                        for (var j = 0; j < subBtns.length; j++) {{
                            subBtns[j].innerText = '[+]';
                        }}
                    }}
                }}
                if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
            }}
        </script></body></html>
        """
        components.html(matrix_full_html, height=550, scrolling=True)

    except Exception as e:
        st.error(f"Lỗi tính toán Ma trận Doanh thu & Sản lượng: {e}")

    st.divider()

    
