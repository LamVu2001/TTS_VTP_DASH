import streamlit as st
from healthscore_page import render as render_healthscore
from trang_moi_page import render as render_trang_moi

st.set_page_config(
    page_title="Multi-Page App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cấu hình menu sidebar bên trái
pg = st.navigation({
    "Báo cáo chính": [
        st.Page(render_healthscore, title="Healthscore Dashboard", icon="📊"),
    ],
    "Chức năng khác": [
        st.Page(render_trang_moi, title="Trang Mới", icon="📁"),
    ]
})

# Chạy trang được chọn
pg.run()
