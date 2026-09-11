import streamlit as st

st.set_page_config(
    page_title="Multi-Page App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thêm CSS để phóng to chữ và làm gọn sidebar
st.markdown("""
<style>
    /* Phóng to chữ của các nút chuyển trang trên sidebar */
    [data-testid="stSidebarNav"] span {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    
    /* Khoảng cách giữa các mục cho thoáng */
    [data-testid="stSidebarNav"] li {
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Khai báo các trang (đã bỏ icon và phân nhóm)
pg = st.navigation([
    st.Page("TTS.py", title="Tiktoks Dashboard"),
    st.Page("SPE.py", title="Shopee Dashboard"),
    st.Page("Others.py", title="Others KA Dashboard")
])

pg.run()
