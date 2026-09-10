import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
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
    
    c_chart, c_top = st.columns([2, 1.3])
    
    with c_chart:
        st.subheader("XU HƯỚNG DOANH THU 7 NGÀY GẦN NHẤT (TỶ ĐỒNG)")
        try:
            df_daily = con.execute(f"""
                SELECT clean_date as ngay, SUM(tong_cuoc)/1e9 as DoanhThu 
                FROM orders WHERE {where_sql_dt} AND clean_date IS NOT NULL 
                GROUP BY ngay ORDER BY ngay DESC LIMIT 7
            """).fetchdf()
            if len(df_daily) > 0:
                df_daily = df_daily.sort_values("ngay")
                fig = px.line(df_daily, x="ngay", y="DoanhThu", markers=True)
                fig.update_traces(line=dict(color="#c62828", width=2.5), marker=dict(size=6, color="#c62828"))
                fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu theo ngày.")
        except Exception:
            st.info("Không thể tải biểu đồ xu hướng.")

    with c_top:
        st.subheader("TOP 10 KHÁCH HÀNG GIẢM DOANH THU")
        try:
            df_top = con.execute(f"""
                SELECT ma_khgui AS "MÃ KH", ROUND(SUM(tong_cuoc)/1e6, 1) AS "DOANH THU (TR)" 
                FROM orders WHERE {where_sql_dt} AND ma_khgui IS NOT NULL 
                GROUP BY ma_khgui ORDER BY "DOANH THU (TR)" DESC LIMIT 10
            """).fetchdf()
            st.dataframe(df_top, use_container_width=True, hide_index=True, height=380)
        except Exception:
            st.info("Không có dữ liệu hiển thị.")

    st.divider()
    st.subheader("📊 BÁO CÁO MA TRẬN DOANH THU & SẢN LƯỢNG")

    # ---------------------------------------------------------
    # 4. XỬ LÝ DỮ LIỆU BẢNG MA TRẬN
    # ---------------------------------------------------------
    try:
        days_data_dt = con.execute(f"""
            SELECT clean_date, SUM(tong_cuoc)/1e9 as dt, COUNT(ma_phieugui) as sl 
            FROM orders WHERE {where_sql_dt} AND clean_date IS NOT NULL 
            GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7
        """).fetchall()
    except Exception:
        days_data_dt = []

    days_dt_dict = {row[0].strftime('%d/%m'): (row[1] or 0, row[2] or 0) for row in days_data_dt if row[0]}
    sorted_days_dt = sorted(list(days_dt_dict.keys()))
    while len(sorted_days_dt) < 7:
        sorted_days_dt.insert(0, "--/--")
        
    d_dt_vals = [days_dt_dict.get(d, (0, 0))[0] for d in sorted_days_dt]
    d_sl_vals = [days_dt_dict.get(d, (0, 0))[1] for d in sorted_days_dt]

    try:
        tree_raw_data = con.execute(f"""
            SELECT 
               COALESCE(ma_doitac, 'Khác') as dt,
               COALESCE(ma_khgui, 'Khác') as kh,
               COALESCE(tinh_phat, 'Khác') as tinh,
               COALESCE(ma_buucuc_phat, 'Khác') as bc,
               SUM(tong_cuoc)/1e9 as tong_dt,
               COUNT(ma_phieugui) as tong_sl
            FROM orders WHERE {where_sql_dt}
            GROUP BY ma_doitac, ma_khgui, tinh_phat, ma_buucuc_phat
            ORDER BY dt, tong_dt DESC
        """).fetchall()
    except Exception:
        tree_raw_data = []

    dt_structure = {}
    for dt, kh, tinh, bc, dt_val, sl_val in tree_raw_data:
        dt_val = dt_val or 0
        sl_val = sl_val or 0
        if dt not in dt_structure:
            dt_structure[dt] = {'dt': 0, 'sl': 0, 'khs': {}, 'tinhs': {}}
        dt_structure[dt]['dt'] += dt_val
        dt_structure[dt]['sl'] += sl_val

        if kh not in dt_structure[dt]['khs']:
            dt_structure[dt]['khs'][kh] = {'dt': 0, 'sl': 0}
        dt_structure[dt]['khs'][kh]['dt'] += dt_val
        dt_structure[dt]['khs'][kh]['sl'] += sl_val

        if tinh not in dt_structure[dt]['tinhs']:
            dt_structure[dt]['tinhs'][tinh] = {'dt': 0, 'sl': 0, 'bcs': {}}
        dt_structure[dt]['tinhs'][tinh]['dt'] += dt_val
        dt_structure[dt]['tinhs'][tinh]['sl'] += sl_val
        dt_structure[dt]['tinhs'][tinh]['bcs'][bc] = {'dt': dt_val, 'sl': sl_val}

    try:
        tinh_raw_data = con.execute(f"""
            SELECT 
               COALESCE(tinh_phat, 'Khác') as tinh,
               COALESCE(ma_buucuc_phat, 'Khác') as bc,
               SUM(tong_cuoc)/1e9 as tong_dt,
               COUNT(ma_phieugui) as tong_sl
            FROM orders WHERE {where_sql_dt}
            GROUP BY tinh_phat, ma_buucuc_phat
            ORDER BY tong_dt DESC
        """).fetchall()
    except Exception:
        tinh_raw_data = []

    tinh_independent_struct = {}
    for tinh, bc, dt_val, sl_val in tinh_raw_data:
        dt_val = dt_val or 0
        sl_val = sl_val or 0
        if tinh not in tinh_independent_struct:
            tinh_independent_struct[tinh] = {'dt': 0, 'sl': 0, 'bcs': {}}
        tinh_independent_struct[tinh]['dt'] += dt_val
        tinh_independent_struct[tinh]['sl'] += sl_val
        tinh_independent_struct[tinh]['bcs'][bc] = {'dt': dt_val, 'sl': sl_val}

    def generate_matrix_rows(is_doanh_thu=True):
        rows_html = ""
        prefix = "dt_sec" if is_doanh_thu else "sl_sec"
        fmt = lambda v: f"{v:.2f}" if is_doanh_thu else f"{v:,.0f}"

        for idx_dt, (dt_name, dt_data) in enumerate(dt_structure.items()):
            val_dt = dt_data['dt'] if is_doanh_thu else dt_data['sl']
            dt_clean_id = f"{prefix}_{idx_dt}"

            rows_html += f"""
            <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
                <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
                <td>10</td><td>100.00</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
            </tr>
            """

            kh_group_id = f"{dt_clean_id}_kh_grp"
            rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; font-weight:600; color: #1565c0;" onclick="toggleRow('{kh_group_id}', event, 'btn_{kh_group_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{kh_group_id}">[+]</span> <b>THEO MÃ KHÁCH HÀNG</b></td>
                <td>-</td><td>-</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>-</td><td>-</td>
            </tr>
            """
            for kh_name, kh_data in dt_data['khs'].items():
                val_kh = kh_data['dt'] if is_doanh_thu else kh_data['sl']
                rows_html += f"""
                <tr class="sub-row-3 {kh_group_id}" style="display:none; background-color: #ffffff; color: #333;">
                    <td style="padding-left: 60px;">• Mã KH: <b>{kh_name}</b></td>
                    <td>10</td><td>100.00</td>
                    <td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td>{fmt(val_kh/7)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_kh)}</td><td>{fmt(val_kh)}</td><td class="text-green">+6.8%</td>
                    <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """

            tinh_group_id = f"{dt_clean_id}_tinh_grp"
            rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; font-weight:600; color: #2e7d32;" onclick="toggleRow('{tinh_group_id}', event, 'btn_{tinh_group_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_group_id}">[+]</span> <b>THEO TỈNH PHÁT</b></td>
                <td>-</td><td>-</td>
                <td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td>{fmt(val_dt/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_dt)}</td><td>{fmt(val_dt)}</td><td class="text-green">+6.8%</td>
                <td>-</td><td>-</td>
            </tr>
            """
            for idx_tinh, (tinh_name, tinh_data) in enumerate(dt_data['tinhs'].items()):
                val_tinh = tinh_data['dt'] if is_doanh_thu else tinh_data['sl']
                tinh_sub_id = f"{tinh_group_id}_tinh_{idx_tinh}"
                rows_html += f"""
                <tr class="sub-row-3 {tinh_group_id}" style="display:none; background-color: #fcfcfc; color: #2e7d32;" onclick="toggleRow('{tinh_sub_id}', event, 'btn_{tinh_sub_id}')">
                    <td style="padding-left: 60px;"><span class="toggle-btn" id="btn_{tinh_sub_id}">[+]</span> Tỉnh phát: <b>{tinh_name}</b></td>
                    <td>10</td><td>100.00</td>
                    <td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                    <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                    <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """
                for bc_name, bc_data in tinh_data['bcs'].items():
                    val_bc = bc_data['dt'] if is_doanh_thu else bc_data['sl']
                    rows_html += f"""
                    <tr class="sub-row-4 {tinh_sub_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                          <td style="padding-left: 80px;">• Bưu cục phát: <b>{bc_name}</b></td>
                          <td>10</td><td>100.00</td>
                          <td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td class="text-green">+6.8%</td>
                          <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                          <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                          <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                    </tr>
                    """

        tinh_root_id = f"{prefix}_tinh_independent_root"
        tot_tinh_val = sum(t['dt'] if is_doanh_thu else t['sl'] for t in tinh_independent_struct.values())
        rows_html += f"""
        <tr class="sub-row-1 group_{prefix}_root" style="display:none; background-color: #e8f5e9; font-weight:bold; color: #2e7d32;" onclick="toggleRow('{tinh_root_id}', event, 'btn_{tinh_root_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{tinh_root_id}">[+]</span> <b>TỈNH PHÁT</b></td>
            <td>-</td><td>-</td>
            <td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td>{fmt(tot_tinh_val/7)}</td><td class="text-green">+6.8%</td>
            <td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td class="text-green">+6.8%</td>
            <td>{fmt(tot_tinh_val)}</td><td>{fmt(tot_tinh_val)}</td><td class="text-green">+6.8%</td>
            <td>-</td><td>-</td>
        </tr>
        """
        for idx_tinh, (tinh_name, tinh_data) in enumerate(tinh_independent_struct.items()):
            val_tinh = tinh_data['dt'] if is_doanh_thu else tinh_data['sl']
            tinh_ind_clean_id = f"{tinh_root_id}_t_{idx_tinh}"
            rows_html += f"""
            <tr class="sub-row-2 {tinh_root_id}" style="display:none; background-color: #ffffff; color: #2e7d32;" onclick="toggleRow('{tinh_ind_clean_id}', event, 'btn_{tinh_ind_clean_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_ind_clean_id}">[+]</span> Tỉnh phát: <b>{tinh_name}</b></td>
                <td>10</td><td>100.00</td>
                <td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td>{fmt(val_tinh/7)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                <td>{fmt(val_tinh)}</td><td>{fmt(val_tinh)}</td><td class="text-green">+6.8%</td>
                <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
            </tr>
            """
            for bc_name, bc_data in tinh_data['bcs'].items():
                val_bc = bc_data['dt'] if is_doanh_thu else bc_data['sl']
                rows_html += f"""
                <tr class="sub-row-3 {tinh_ind_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                       <td style="padding-left: 60px;">• Bưu cục phát: <b>{bc_name}</b></td>
                       <td>10</td><td>100.00</td>
                       <td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td>{fmt(val_bc/7)}</td><td class="text-green">+6.8%</td>
                       <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                       <td>{fmt(val_bc)}</td><td>{fmt(val_bc)}</td><td class="text-green">+6.8%</td>
                       <td>{"10" if is_doanh_thu else "-"}</td><td class="text-green">{"Wait" if is_doanh_thu else "-"}</td>
                </tr>
                """
        return rows_html

    rows_html_sl_section = generate_matrix_rows(is_doanh_thu=False)
    rows_html_dt_section = generate_matrix_rows(is_doanh_thu=True)

    matrix_dt_html = f"""
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
                <th rowspan="2" style="width: 25%;">Phân loại Đối tác / Tỉnh phát</th>
                <th rowspan="2" style="width: 4%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="5" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days_dt[0]}</th><th>{sorted_days_dt[1]}</th><th>{sorted_days_dt[2]}</th><th>{sorted_days_dt[3]}</th><th>{sorted_days_dt[4]}</th><th>{sorted_days_dt[5]}</th><th>{sorted_days_dt[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W30</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
                <th>Dự kiến FM doanh thu (Tỷ)</th><th>Dự kiến doanh thu (Δ vs Mục tiêu)</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_sl_sec_root', event, 'btn_sl_sec_root')">
                <td><span class="toggle-btn" id="btn_sl_sec_root">[+]</span> <b>SẢN LƯỢNG</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_sl_vals[0]:,.0f}</td><td>{d_sl_vals[1]:,.0f}</td><td>{d_sl_vals[2]:,.0f}</td><td>{d_sl_vals[3]:,.0f}</td><td>{d_sl_vals[4]:,.0f}</td><td>{d_sl_vals[5]:,.0f}</td><td><b>{d_sl_vals[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_sl_vals[0]*5:,.0f}</td><td>{d_sl_vals[1]*5:,.0f}</td><td>{d_sl_vals[2]*5:,.0f}</td><td>{d_sl_vals[3]*5:,.0f}</td><td>{d_sl_vals[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{tong_sl:,.0f}</td><td><b>{tong_sl:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>-</td><td>-</td>
            </tr>
            {rows_html_sl_section}

            <tr class="row-group" onclick="toggleRow('group_dt_sec_root', event, 'btn_dt_sec_root')">
                <td><span class="toggle-btn" id="btn_dt_sec_root">[+]</span> <b>DOANH THU (TỶ ĐỒNG)</b></td>
                <td style="text-align: center;">-</td>
                <td style="text-align: center;">100%</td>
                <td>{d_dt_vals[0]:,.2f}</td><td>{d_dt_vals[1]:,.2f}</td><td>{d_dt_vals[2]:,.2f}</td><td>{d_dt_vals[3]:,.2f}</td><td>{d_dt_vals[4]:,.2f}</td><td>{d_dt_vals[5]:,.2f}</td><td><b>{d_dt_vals[6]:,.2f}</b></td><td class="text-green">+6.81%</td>
                <td>{d_dt_vals[0]*5:,.2f}</td><td>{d_dt_vals[1]*5:,.2f}</td><td>{d_dt_vals[2]*5:,.2f}</td><td>{d_dt_vals[3]*5:,.2f}</td><td>{d_dt_vals[6]*5:,.2f}</td><td class="text-green">+6.81%</td>
                <td>{tong_dt:,.2f}</td><td><b>{tong_dt:,.2f}</b></td><td class="text-green">+6.81%</td>
                <td>{(tong_dt*1.1):,.2f}</td><td class="text-green">+6.81%</td>
            </tr>
            {rows_html_dt_section}
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

    components.html(matrix_dt_html, height=520, scrolling=True)
