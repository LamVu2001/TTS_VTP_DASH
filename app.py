import streamlit as st

st.set_page_config(
    page_title="Multi-Page App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cấu hình menu sidebar bên trái
pg = st.navigation({
    "Tiktoks": [
        # Thêm dấu ngoặc kép "..." và đúng tên file của bạn
        st.Page("TTS.py", title="Tiktoks Dashboard", icon="📊"),
    ],
    "Shopee": [
        # Thêm dấu ngoặc kép "..." và đúng tên file của bạn
        st.Page("SPE.py", title="Shopee Dashboard", icon="📁"),
    ]
})

# Chạy trang được chọn
pg.run()
