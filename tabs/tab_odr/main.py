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
    if "f_tt" not in st.session_state: st.session_state.f_tt = []

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
        if exclude != "tt":
            c = sql_in_clause("ma_trangthai", st.session_state.f_tt)
            if c: conds.append(c)
            
        return " AND ".join(conds)

    # 2. LẤY DANH SÁCH TỰ ĐỘNG THEO DỮ LIỆU CROSS-FILTER
    tinh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tinh_phat AS VARCHAR) FROM orders WHERE {build_where('tinh')} AND tinh_phat IS NOT NULL ORDER BY 1").fetchall()]
    kh_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_khgui AS VARCHAR) FROM orders WHERE {build_where('kh')} AND ma_khgui IS NOT NULL ORDER BY 1").fetchall()]
    bc_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_buucuc_phat AS VARCHAR) FROM orders WHERE {build_where('bc')} AND ma_buucuc_phat IS NOT NULL ORDER BY 1").fetchall()]
    tuyen_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(tuyen AS VARCHAR) FROM orders WHERE {build_where('tuyen')} AND tuyen IS NOT NULL ORDER BY 1").fetchall()]
    ld_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_dv_viettel AS VARCHAR) FROM orders WHERE {build_where('ld')} AND ma_dv_viettel IS NOT NULL ORDER BY 1").fetchall()]
    tl_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(nhom_trong_luong AS VARCHAR) FROM orders WHERE {build_where('tl')} AND nhom_trong_luong IS NOT NULL ORDER BY 1").fetchall()]
    tt_opts = [r[0] for r in con.execute(f"SELECT DISTINCT CAST(ma_trangthai AS VARCHAR) FROM orders WHERE {build_where('tt')} AND ma_trangthai IS NOT NULL ORDER BY 1").fetchall()]

    # Validate lọc sạch các value cũ không còn nằm trong danh sách tùy chọn mới
    st.session_state.f_tinh = [v for v in st.session_state.f_tinh if v in tinh_opts]
    st.session_state.f_kh = [v for v in st.session_state.f_kh if v in kh_opts]
    st.session_state.f_bc = [v for v in st.session_state.f_bc if v in bc_opts]
    st.session_state.f_tuyen = [v for v in st.session_state.f_tuyen if v in tuyen_opts]
    st.session_state.f_ld = [v for v in st.session_state.f_ld if v in ld_opts]
    st.session_state.f_tl = [v for v in st.session_state.f_tl if v in tl_opts]
    st.session_state.f_tt = [v for v in st.session_state.f_tt if v in tt_opts]

    # 3. HIỂN THỊ BỘ LỌC NGANG DẠNG MULTI-SELECT (8 Ô LỌC)
    of1, of2, of3, of4, of5, of6, of7, of8 = st.columns(8)

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
    with of8:
        st.multiselect("MÃ TRẠNG THÁI", tt_opts, key="f_tt", placeholder="Tất cả")

  # 4. TỔNG HỢP MỆNH ĐỀ WHERE VÀ TRUY VẤN KPI THEO NGÀY PHÁT THỰC TẾ (clean_date_ptc)
    
    # Tạo điều kiện lọc ngày theo clean_date_ptc dành riêng cho các chỉ số phát thành công
    ptc_date_cond = "1=1"
    if isinstance(st.session_state.f_date, (list, tuple)) and len(st.session_state.f_date) == 2:
        ptc_date_cond = f"clean_date_ptc BETWEEN '{st.session_state.f_date[0]}' AND '{st.session_state.f_date[1]}'"

    # Điều kiện WHERE hoàn chỉnh cho KPI (kết hợp bộ lọc khác + ngày phát clean_date_ptc)
    where_kpi_sql = f"{build_where(exclude='date')} AND {ptc_date_cond}"

    res_metrics_odr = con.execute(f"""
        SELECT 
            -- Tổng đơn được phát thành công trong kỳ (TT 501 + clean_date_ptc trong khoảng lọc)
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) = '501' THEN ma_phieugui 
            END) AS tong_ptc_501,

            -- (1a) Đơn PTC 501 trong SLA cam kết (Phát đúng giờ)
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) = '501' 
                 AND danh_gia_giao_hang = 'Giao đúng giờ' 
                THEN ma_phieugui 
            END) AS sl_ptc_501_in_sla,
            
            -- (1b) Đơn có TT 501, 505, 506, 507, 509 phát lần 1 trong SLA cam kết
            COUNT(DISTINCT CASE 
                WHEN CAST(ma_trangthai AS VARCHAR) IN ('501', '505', '506', '507', '509') 
                 AND PTC_1 = 1 
                 AND danh_gia_giao_hang = 'Giao đúng giờ' 
                THEN ma_phieugui 
            END) AS sl_lan1_in_sla,

            -- Đơn PTC chung trong kỳ
            COUNT(DISTINCT CASE WHEN PTC = 1 THEN ma_phieugui END) AS sl_ptc,
            
            -- Đơn PTC Lần 1 chung trong kỳ
            COUNT(DISTINCT CASE WHEN PTC_1 = 1 THEN ma_phieugui END) AS sl_ptc1,

            -- Tổng đơn phải phát (Lọc theo clean_date phân bổ ban đầu để so sánh)
            (SELECT COUNT(DISTINCT ma_phieugui) FROM orders WHERE {build_where()}) AS tong_sl_phai_phat

        FROM orders 
        WHERE {where_kpi_sql} AND clean_date_ptc IS NOT NULL
    """).fetchone()

    mau_so_501 = res_metrics_odr[0] or 0          # (2) Tổng đơn PTC TT 501 được phát trong kỳ
    tu_so_dung_gio = res_metrics_odr[1] or 0      # (1a) Tử số Đúng giờ
    tu_so_lan1_dung_gio = res_metrics_odr[2] or 0 # (1b) Tử số Đúng giờ lần 1
    sl_ptc = res_metrics_odr[3] or 0
    sl_ptc1 = res_metrics_odr[4] or 0
    tong_sl_phai_phat = res_metrics_odr[5] or 0  # Sản lượng phải phát (giao trong kỳ)

    # Tính % theo đúng công thức
    pct_ptc = (sl_ptc / tong_sl_phai_phat * 100) if tong_sl_phai_phat > 0 else 0
    pct_ptc1 = (sl_ptc1 / tong_sl_phai_phat * 100) if tong_sl_phai_phat > 0 else 0
    
    # Tính 2 KPI đúng giờ theo mẫu số đơn PTC TT 501 phát trong kỳ
    pct_ptc_dung_gio = (tu_so_dung_gio / mau_so_501 * 100) if mau_so_501 > 0 else 0
    pct_ptc1_dung_gio = (tu_so_lan1_dung_gio / mau_so_501 * 100) if mau_so_501 > 0 else 0

    # HIỂN THỊ METRICS
    m_odr1, m_odr2, m_odr3, m_odr4, m_odr5 = st.columns(5)
    with m_odr1: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">SẢN LƯỢNG PHẢI PHÁT</div><div class="metric-value">{tong_sl_phai_phat:,.0f}</div><div class="metric-sub-green">▲ Phân bổ</div></div>', unsafe_allow_html=True)
    with m_odr2: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC</div><div class="metric-value">{pct_ptc:.1f}%</div><div class="metric-sub-green">Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr3: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC LẦN 1</div><div class="metric-value">{pct_ptc1:.1f}%</div><div class="metric-sub-green">Thực tế</div></div>', unsafe_allow_html=True)
    with m_odr4: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT TC ĐÚNG GIỜ</div><div class="metric-value">{pct_ptc_dung_gio:.1f}%</div><div class="metric-sub-green">Theo ngày PTC</div></div>', unsafe_allow_html=True)
    with m_odr5: 
        st.markdown(f'<div class="metric-card"><div class="metric-title">TỶ LỆ PHÁT ĐÚNG GIỜ LẦN 1</div><div class="metric-value">{pct_ptc1_dung_gio:.1f}%</div><div class="metric-sub-green">Theo ngày PTC</div></div>', unsafe_allow_html=True)

    st.write("")
    
    # 5. BIỂU ĐỒ XU HƯỚNG PHÁT THÀNH CÔNG THEO THỜI GIAN PHẢI PHÁT (clean_date)
    c_odr_chart, c_odr_right = st.columns([2, 1.3])
    with c_odr_chart:
        st.subheader("📈 XU HƯỚNG SẢN LƯỢNG PHÁT THÀNH CÔNG")
        try:
            where_chart_sql = f"{where_sql_odr} AND PTC = 1 AND clean_date IS NOT NULL"

            df_odr_daily = con.execute(f"""
                SELECT 
                    CAST(clean_date AS VARCHAR) as ngay_phai_phat, 
                    COUNT(DISTINCT ma_phieugui) as SanLuongPTC 
                FROM orders 
                WHERE {where_chart_sql}
                GROUP BY clean_date 
                ORDER BY clean_date ASC
            """).fetchdf()

            if len(df_odr_daily) > 0:
                fig_odr = px.line(
                    df_odr_daily, 
                    x="ngay_phai_phat", 
                    y="SanLuongPTC", 
                    markers=True,
                    text="SanLuongPTC"
                )
                
                fig_odr.update_traces(
                    line=dict(color="#c62828", width=2.5), 
                    marker=dict(size=7, color="#c62828"),
                    textposition="top center",
                    textfont=dict(size=11, color="#111111")
                )
                
                fig_odr.update_layout(
                    height=380, 
                    margin=dict(l=10, r=10, t=25, b=10),
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
        st.info("Biểu đồ bên trái thể hiện số lượng mã phiếu gửi phát thành công (COUNT DISTINCT ma_phieugui khi PTC = 1) phân bổ theo thời gian phải phát (clean_date) trong khoảng thời gian đã chọn.")

    st.divider()

    # 6. BẢNG TƯƠNG TÁC TỈNH PHÁT / BƯU CỤC PHÁT
    st.markdown('<p class="section-red-title">DANH SÁCH CHI NHÁNH & BƯU CỤC PHÁT (BẤM CHỌN DÒNG CHI NHÁNH BÊN TRÁI ĐỂ LỌC BƯU CỤC BÊN PHẢI)</p>', unsafe_allow_html=True)

    cn_data_raw = con.execute(f"""
        SELECT 
            CAST(tinh_phat AS VARCHAR) AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_don,
            COUNT(DISTINCT CASE WHEN PTC = 1 THEN ma_phieugui END) AS ptc_cnt
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL
        GROUP BY tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    bc_data_raw = con.execute(f"""
        SELECT 
            CAST(ma_buucuc_phat AS VARCHAR) AS bc, 
            CAST(tinh_phat AS VARCHAR) AS cn,
            COUNT(DISTINCT ma_phieugui) AS tong_don,
            COUNT(DISTINCT CASE WHEN PTC = 1 THEN ma_phieugui END) AS ptc_cnt
        FROM orders 
        WHERE {where_sql_odr} AND tinh_phat IS NOT NULL AND ma_buucuc_phat IS NOT NULL
        GROUP BY ma_buucuc_phat, tinh_phat 
        ORDER BY tong_don DESC
    """).fetchall()

    rows_cn_html = "".join([f'<tr class="cn-row" data-cn="{item[0]}" onclick="filterBC(\'{item[0]}\', this)"><td style="font-weight: bold; cursor: pointer; text-align: left; padding-left: 10px;">{item[0]}</td><td style="text-align: right; padding-right: 10px;">{item[1]:,}</td><td style="text-align: right; padding-right: 10px;">{item[2]:,}</td></tr>' for item in cn_data_raw])
    rows_bc_html = "".join([f'<tr class="bc-row" data-cn="{item[1]}"><td style="font-weight: bold; text-align: left; padding-left: 10px;">{item[0]}</td><td style="font-weight: bold; text-align: center;">{item[1]}</td><td style="text-align: right; padding-right: 10px;">{item[2]:,}</td><td style="text-align: right; padding-right: 10px;">{item[3]:,}</td></tr>' for item in bc_data_raw])

    interactive_tables_html = f"""
    <!DOCTYPE html><html><head><style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background: transparent; }}
        .grid-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
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
            <div class="table-scroll"><table><thead><tr><th style="text-align: left; padding-left: 10px;">Tỉnh phát</th><th style="text-align: right; padding-right: 10px;">Tổng đơn</th><th style="text-align: right; padding-right: 10px;">Đơn PTC</th></tr></thead><tbody>{rows_cn_html if rows_cn_html else "<tr><td colspan='3' style='text-align:center;'>Không có dữ liệu</td></tr>"}</tbody></table></div>
        </div>
        <div>
            <div class="table-title">Bưu Cục Phát <span id="bc-title-status" style="color: #c62828; font-weight: bold;">(Toàn Quốc)</span></div>
            <div class="table-scroll"><table><thead><tr><th style="text-align: left; padding-left: 10px;">Mã bưu cục phát</th><th>Tỉnh phát</th><th style="text-align: right; padding-right: 10px;">Sản lượng đơn</th><th style="text-align: right; padding-right: 10px;">Đơn PTC</th></tr></thead><tbody id="bc-tbody">{rows_bc_html if rows_bc_html else "<tr><td colspan='4' style='text-align:center;'>Không có dữ liệu</td></tr>"}</tbody></table></div>
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

    days_data = con.execute(f"SELECT clean_date, COUNT(DISTINCT ma_phieugui) as sl FROM orders WHERE {where_sql_odr} AND clean_date IS NOT NULL GROUP BY clean_date ORDER BY clean_date DESC LIMIT 7").fetchall()
    days_dict = {row[0].strftime('%d/%m'): row[1] for row in days_data}
    sorted_days = sorted(list(days_dict.keys()))
    while len(sorted_days) < 7: sorted_days.insert(0, "--/--")
    d_vals = [days_dict.get(d, 0) for d in sorted_days]

    m_current = tong_sl_odr

    all_tree_data = con.execute(f"SELECT COALESCE(CAST(ma_doitac AS VARCHAR), 'Khác') as dt, COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc, COUNT(DISTINCT ma_phieugui) as sl FROM orders WHERE {where_sql_odr} GROUP BY ma_doitac, tinh_phat, ma_buucuc_phat ORDER BY 1, 2, 4 DESC").fetchall()

    tree_struct = {}
    for dt, tinh, bc, sl in all_tree_data:
        if dt not in tree_struct: tree_struct[dt] = {'sl': 0, 'tinhs': {}}
        tree_struct[dt]['sl'] += sl
        if tinh not in tree_struct[dt]['tinhs']: tree_struct[dt]['tinhs'][tinh] = {'sl': 0, 'bcs': {}}
        tree_struct[dt]['tinhs'][tinh]['sl'] += sl
        tree_struct[dt]['tinhs'][tinh]['bcs'][bc] = sl

    matrix_rows_html = ""
    for idx_dt, (dt_name, dt_data) in enumerate(tree_struct.items()):
        dt_sl = dt_data['sl']
        dt_clean_id = f"dt_{idx_dt}"
        matrix_rows_html += f"""
        <tr class="sub-row-1 group_root" style="display:none; background-color: #f4f6f8; font-weight:600;" onclick="toggleRow('{dt_clean_id}', event, 'btn_{dt_clean_id}')">
            <td style="padding-left: 20px;"><span class="toggle-btn" id="btn_{dt_clean_id}">[+]</span> Đối tác: <b>{dt_name}</b></td>
            <td>-</td><td>-</td>
            <td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td>{dt_sl//7}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
            <td>{dt_sl}</td><td>{dt_sl}</td><td class="text-green">+5.22%</td>
        </tr>
        """
        for idx_tinh, (tinh_name, tinh_data) in enumerate(dt_data['tinhs'].items()):
            tinh_sl = tinh_data['sl']
            tinh_clean_id = f"{dt_clean_id}_tinh_{idx_tinh}"
            matrix_rows_html += f"""
            <tr class="sub-row-2 {dt_clean_id}" style="display:none; background-color: #ffffff; color: #1565c0;" onclick="toggleRow('{tinh_clean_id}', event, 'btn_{tinh_clean_id}')">
                <td style="padding-left: 40px;"><span class="toggle-btn" id="btn_{tinh_clean_id}">[+]</span> Tỉnh: <b>{tinh_name}</b></td>
                <td>-</td><td>-</td>
                <td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td>{tinh_sl//7}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
                <td>{tinh_sl}</td><td>{tinh_sl}</td><td class="text-green">+5.22%</td>
            </tr>
            """
            for bc_name, bc_sl in tinh_data['bcs'].items():
                matrix_rows_html += f"""
                <tr class="sub-row-3 {tinh_clean_id}" style="display:none; background-color: #fafafa; font-style: italic; color: #555;">
                    <td style="padding-left: 60px;">• Bưu cục: <b>{bc_name}</b></td>
                    <td>-</td><td>-</td>
                    <td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td>{bc_sl//7}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
                    <td>{bc_sl}</td><td>{bc_sl}</td><td class="text-green">+5.22%</td>
                </tr>
                """

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
                <th rowspan="2" style="width: 26%;">Chỉ tiêu</th>
                <th rowspan="2" style="width: 5%;">Mục tiêu</th>
                <th rowspan="2" style="width: 5%;">Kết quả thực hiện</th>
                <th colspan="8" style="background-color: #2a2a2a;">7 ngày gần nhất</th>
                <th colspan="6" style="background-color: #333333;">5 tuần gần nhất</th>
                <th colspan="3" style="background-color: #2a2a2a;">Tháng</th>
            </tr>
            <tr>
                <th>{sorted_days[0]}</th><th>{sorted_days[1]}</th><th>{sorted_days[2]}</th><th>{sorted_days[3]}</th><th>{sorted_days[4]}</th><th>{sorted_days[5]}</th><th>{sorted_days[6]}</th><th style="color: #ff5252;">DoD</th>
                <th>W28</th><th>W31</th><th>W32</th><th>W33</th><th>W34</th><th style="color: #ff5252;">WoW</th>
                <th>M-1</th><th>M</th><th style="color: #ff5252;">MoM</th>
            </tr>
        </thead>
        <tbody>
            <tr class="row-group" onclick="toggleRow('group_root', event, 'btn_root')">
                <td><span class="toggle-btn" id="btn_root">[+]</span> <b>Sản lượng phải phát</b></td>
                <td style="text-align: center;">-</td><td style="text-align: center;">100%</td>
                <td>{d_vals[0]:,.0f}</td><td>{d_vals[1]:,.0f}</td><td>{d_vals[2]:,.0f}</td><td>{d_vals[3]:,.0f}</td><td>{d_vals[4]:,.0f}</td><td>{d_vals[5]:,.0f}</td><td><b>{d_vals[6]:,.0f}</b></td><td class="text-green">+5.22%</td>
                <td>{d_vals[0]*5:,.0f}</td><td>{d_vals[1]*5:,.0f}</td><td>{d_vals[2]*5:,.0f}</td><td>{d_vals[3]*5:,.0f}</td><td>{d_vals[6]*5:,.0f}</td><td class="text-green">+5.22%</td>
                <td>{m_current:,.0f}</td><td><b>{m_current:,.0f}</b></td><td class="text-green">+5.22%</td>
            </tr>

            {matrix_rows_html}

            <tr class="row-group">
                <td><b>Sản lượng phát thành công</b></td>
                <td style="text-align: center;">-</td><td style="text-align: center;">98%</td>
                <td>{d_vals[0]*0.9:,.0f}</td><td>{d_vals[1]*0.9:,.0f}</td><td>{d_vals[2]*0.9:,.0f}</td><td>{d_vals[3]*0.9:,.0f}</td><td>{d_vals[4]*0.9:,.0f}</td><td>{d_vals[5]*0.9:,.0f}</td><td><b>{d_vals[6]*0.9:,.0f}</b></td><td class="text-red">-2.10%</td>
                <td>{d_vals[0]*4:,.0f}</td><td>{d_vals[1]*4:,.0f}</td><td>{d_vals[2]*4:,.0f}</td><td>{d_vals[3]*4:,.0f}</td><td>{d_vals[6]*4:,.0f}</td><td class="text-red">-1.50%</td>
                <td>{m_current*0.95:,.0f}</td><td><b>{m_current*0.95:,.0f}</b></td><td class="text-red">-1.20%</td>
            </tr>

            <tr>
                <td style="font-weight: bold;">% Phát thành công</td>
                <td style="text-align: center;">99.00</td><td style="text-align: center;">100.00</td>
                <td>28.42</td><td>27.42</td><td>25.96</td><td>19.36</td><td>13.26</td><td>22.42</td><td>18.79</td><td class="text-red">-14.05</td>
                <td>14.89</td><td>13.99</td><td>25.81</td><td>12.91</td><td>26.96</td><td class="text-red">-14.05</td>
                <td>22.59</td><td>12.32</td><td class="text-red">-14.05</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">% Phát thành công đg lần 1</td>
                <td style="text-align: center;">98.00</td><td style="text-align: center;">100.00</td>
                <td>18.15</td><td>10.17</td><td>15.94</td><td>25.08</td><td>19.14</td><td>28.11</td><td>27.75</td><td class="text-green">+11.93</td>
                <td>16.80</td><td>21.11</td><td>16.22</td><td>26.40</td><td>11.90</td><td class="text-green">+11.93</td>
                <td>26.29</td><td>22.93</td><td class="text-green">+11.93</td>
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
    components.html(matrix_full_html, height=480, scrolling=True)

    # 8. BA BẢNG TỒN KHÂU (FM, MM, LM)
    ton_tree_data = con.execute(f"SELECT COALESCE(CAST(tinh_phat AS VARCHAR), 'Khác') as tinh, COALESCE(CAST(ma_buucuc_phat AS VARCHAR), 'Khác') as bc, COUNT(DISTINCT ma_phieugui) as sl FROM orders WHERE {where_sql_odr} GROUP BY tinh_phat, ma_buucuc_phat ORDER BY 1, 3 DESC").fetchall()

    tinh_tree = {}
    for tinh, bc, sl in ton_tree_data:
        if tinh not in tinh_tree: tinh_tree[tinh] = {'sl': 0, 'bcs': {}}
        tinh_tree[tinh]['sl'] += sl
        tinh_tree[tinh]['bcs'][bc] = sl

    base_style = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background-color: transparent; }
        .table-container { max-height: 380px; overflow-y: auto; border: 1px solid #d3d3d3; border-radius: 4px; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11.5px; background: #fff; }
        th { position: sticky; top: 0; z-index: 10; background-color: #c62828; color: #ffffff; text-align: center; padding: 7px 4px; border-bottom: 2px solid #b71c1c; border-right: 1px solid #b71c1c; font-weight: bold; }
        tr.total-row td { position: sticky; top: 31px; z-index: 9; background-color: #f5f5f5; font-weight: bold; border-bottom: 2px solid #ccc; }
        td { padding: 6px 6px; border-bottom: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0; text-align: center; }
        td.col-branch { text-align: left; padding-left: 10px; }
        .ton-btn { display: inline-block; width: 14px; height: 14px; line-height: 12px; text-align: center; border: 1px solid #555; background: #fff; color: #333; font-weight: bold; font-size: 9px; cursor: pointer; margin-right: 5px; border-radius: 2px; }
        .ton-highlight-red { color: #c62828; font-weight: bold; }
        .ton-highlight-orange { color: #e65100; font-weight: bold; }
    </style>
    <script>
        function toggleTonRow(className, event, btnId) {
            if (event) event.stopPropagation();
            var rows = document.getElementsByClassName(className);
            var btn = document.getElementById(btnId);
            if (!rows || rows.length === 0) return;
            var isHidden = rows[0].style.display === 'none';
            for (var i = 0; i < rows.length; i++) {
                rows[i].style.display = isHidden ? 'table-row' : 'none';
            }
            if (btn) btn.innerText = isHidden ? '[-]' : '[+]';
        }
    </script>
    """

    # BẢNG 1: FM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU FM CÁC BƯU GỬI CHƯA XUẤT SẠCH – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    fm_rows_html = ""
    for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
        t_sl = t_data['sl']
        t_id = f"fm_tinh_{idx_t}"
        fm_rows_html += f"""
        <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
            <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
            <td>{t_sl:,.0f}</td><td>{int(t_sl*0.03):,.0f}</td><td>3.0%</td>
            <td class="ton-highlight-red">{int(t_sl*0.005):,.0f}</td>
            <td class="ton-highlight-orange">{int(t_sl*0.002):,.0f}</td>
            <td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
        </tr>
        """
        for b_name, b_sl in t_data['bcs'].items():
            fm_rows_html += f"""
            <tr class="{t_id}" style="display:none; background-color:#fafafa;">
                <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
                <td>{b_sl:,.0f}</td><td>{int(b_sl*0.03):,.0f}</td><td>3.0%</td>
                <td class="ton-highlight-red">{int(b_sl*0.005):,.0f}</td>
                <td class="ton-highlight-orange">{int(b_sl*0.002):,.0f}</td>
                <td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
            </tr>
            """

    html_fm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Chi Nhánh</th><th style="width: 14%;">Sản lượng đã thu thành công</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Tồn quá 1 ngày</th><th style="width: 11%;">Tồn quá 2 ngày</th><th style="width: 12%;">Tỷ lệ tồn quá 1 ngày</th><th style="width: 12%;">Tỷ lệ tồn quá 2 ngày</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td><td>{tong_sl_odr:,.0f}</td><td>{int(tong_sl_odr*0.03):,.0f}</td><td>3.0%</td>
                    <td class="ton-highlight-red">{int(tong_sl_odr*0.005):,.0f}</td><td class="ton-highlight-orange">{int(tong_sl_odr*0.002):,.0f}</td><td class="ton-highlight-red">1.50%</td><td class="ton-highlight-orange">0.65%</td>
                </tr>
                {fm_rows_html}
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_fm, height=390, scrolling=False)

    # BẢNG 2: MM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU MM CÁC BƯU GỬI CHƯA KẾT NỐI – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    html_mm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container" style="max-height: 220px;">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Đơn vị kết nối</th><th style="width: 14%;">Sản lượng đã nhận bàn giao</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Quá 6H</th><th style="width: 11%;">Quá 12H</th><th style="width: 12%;">Quá 24H</th><th style="width: 12%;">Quá 48H</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td><td class="ton-highlight-red">222</td><td>1,381</td><td>1.12%</td><td class="ton-highlight-red">111</td><td class="ton-highlight-orange">111</td><td>13</td><td>23</td>
                </tr>
                <tr><td class="col-branch">TTKT3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">HNIVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">DVVC</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
                <tr><td class="col-branch">DVVTNN3</td><td class="ton-highlight-red">5</td><td>381</td><td>4.2%</td><td class="ton-highlight-red">2</td><td class="ton-highlight-orange">3</td><td>1</td><td>2</td></tr>
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_mm, height=230, scrolling=False)

    # BẢNG 3: LM
    st.markdown('<p style="font-size: 13px; font-weight: bold; color: #111; border-left: 4px solid #c62828; padding-left: 8px; margin-top: 10px; margin-bottom: 6px;">TỒN KHÂU LM CÁC BƯU GỬI CHƯA PHÁT – CÓ THỂ XUẤT CHI TIẾT THEO ĐƠN</p>', unsafe_allow_html=True)
    
    lm_rows_html = ""
    for idx_t, (t_name, t_data) in enumerate(tinh_tree.items()):
        t_sl = t_data['sl']
        t_id = f"lm_tinh_{idx_t}"
        lm_rows_html += f"""
        <tr style="cursor:pointer;" onclick="toggleTonRow('{t_id}', event, 'btn_{t_id}')">
            <td class="col-branch"><span class="ton-btn" id="btn_{t_id}">[+]</span> <b>{t_name}</b></td>
            <td>{t_sl:,.0f}</td><td>{int(t_sl*0.04):,.0f}</td><td>4.0%</td>
            <td class="ton-highlight-red">{int(t_sl*0.008):,.0f}</td>
            <td class="ton-highlight-orange">{int(t_sl*0.003):,.0f}</td>
            <td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
        </tr>
        """
        for b_name, b_sl in t_data['bcs'].items():
            lm_rows_html += f"""
            <tr class="{t_id}" style="display:none; background-color:#fafafa;">
                <td class="col-branch" style="padding-left: 32px; color: #555;">• Bưu cục: {b_name}</td>
                <td>{b_sl:,.0f}</td><td>{int(b_sl*0.04):,.0f}</td><td>4.0%</td>
                <td class="ton-highlight-red">{int(b_sl*0.008):,.0f}</td>
                <td class="ton-highlight-orange">{int(b_sl*0.003):,.0f}</td>
                <td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
            </tr>
            """

    html_lm = f"""
    <!DOCTYPE html><html><head>{base_style}</head><body>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">Chi nhánh</th><th style="width: 14%;">Sản lượng đã phát thành công</th><th style="width: 10%;">Tổng tồn</th><th style="width: 10%;">Tỷ lệ tồn</th><th style="width: 11%;">Tồn quá 1 ngày</th><th style="width: 11%;">Tồn quá 2 ngày</th><th style="width: 12%;">Tồn quá 3 ngày</th><th style="width: 12%;">Tồn quá 4 ngày</th>
                </tr>
            </thead>
            <tbody>
                <tr class="total-row">
                    <td class="col-branch">TOTAL</td><td>{tong_sl_odr:,.0f}</td><td>{int(tong_sl_odr*0.04):,.0f}</td><td>4.0%</td>
                    <td class="ton-highlight-red">{int(tong_sl_odr*0.008):,.0f}</td><td class="ton-highlight-orange">{int(tong_sl_odr*0.003):,.0f}</td><td class="ton-highlight-orange">0.80%</td><td class="ton-highlight-orange">0.30%</td>
                </tr>
                {lm_rows_html}
            </tbody>
        </table>
    </div>
    </body></html>
    """
    components.html(html_lm, height=390, scrolling=False)
