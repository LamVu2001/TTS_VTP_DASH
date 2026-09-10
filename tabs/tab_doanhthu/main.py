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
            value=f"{tong_dt:,.2f} tỷ"
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
        st.subheader("📈 XU HƯỚNG DOANH THU (TỶ ĐỒNG)")

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
        st.subheader("📊 TOP 10 KHÁCH HÀNG DOANH THU")

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


    
