import streamlit as st
# from TTS import render as render_TTS
# from SPE import render as render_SPE

st.set_page_config(
    page_title="Multi-Page App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cấu hình menu sidebar bên trái
pg = st.navigation({
    "Tiktoks": [
        st.Page(render_TTS, title="Tiktoks Dashboard", icon="📊"),
    ],
    "Shopee": [
        st.Page(render_SPE, title="Shopee Dashboard", icon="📁"),
    ]
})

# Chạy trang được chọn
pg.run()
