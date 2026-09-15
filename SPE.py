import streamlit as st
from SPE_tabs.tab_odr.main import render as render_odr
from SPE_tabs.tab_doanhthu.main import render as render_doanhthu
from SPE_tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Shopee", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 14px; font-weight: bold; font-family: sans-serif;">
        <!-- ICON SHOPEE ĐÚNG CHUẨN MẪU TỐI GIẢN -->
        <svg width="38" height="38" viewBox="0 0 512 512" style="display:inline-block; vertical-align:middle;">
            <!-- Thân túi màu cam -->
            <path d="M120,136 L392,136 C410,136 424,150 428,168 L472,392 C478,422 454,448 424,448 L88,448 C58,448 34,422 40,392 L84,168 C88,150 102,136 120,136 Z" fill="#EE4D2D"/>
            <!-- Quai túi -->
            <path d="M184,136 L184,92 C184,52 216,20 256,20 C296,20 328,52 328,92 L328,136" fill="none" stroke="#EE4D2D" stroke-width="28" stroke-linecap="round"/>
            <!-- Chữ 'S' trắng tối giản ở giữa -->
            <path d="M290,210 C265,190 230,185 200,195 C170,205 155,230 160,260 C165,290 195,305 235,320 C275,335 315,355 315,405 C315,450 270,480 215,480 C170,480 135,460 115,435" fill="none" stroke="#FFFFFF" stroke-width="32" stroke-linecap="round"/>
        </svg>
        SHOPEE DASHBOARD
    </h2>
""", unsafe_allow_html=True)

# CSS Định dạng Metric Card
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px;
        padding: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); height: 95px;
    }
    .metric-title { font-size: 10px; font-weight: bold; color: #555555; text-transform: uppercase; height: 26px; line-height: 13px; }
    .metric-value { font-size: 22px; font-weight: bold; color: #111111; margin: 2px 0; }
    .metric-sub-green { font-size: 10px; color: #2e7d32; font-weight: bold; }
    .metric-sub-red { font-size: 10px; color: #c62828; font-weight: bold; }
    .section-red-title {
        font-size: 14px; font-weight: bold; color: #111; 
        border-left: 4px solid #c62828; padding-left: 8px; 
        margin-top: 5px; margin-bottom: 10px; text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ID File Data
TTS_PHAT_FILE_ID = "19WK4CnUH70ftLi1bwbAB-LwMTGUDs19P"
DOANHTHU_FILE_ID = "19WK4CnUH70ftLi1bwbAB-LwMTGUDs19P"  # Điền File ID của dữ liệu doanh thu nếu dùng riêng
TTS_THU_FILE_ID = "1xEEvCjDTBp-GihkUiBTEygM_7Bwm71ZC" 

# Khai báo 2 tab
tab_doanhthu, tab_odr, tab_opr = st.tabs(["💰 TAB DOANH THU","🚚 TAB ODR","⚡ TAB OPR"])

with tab_doanhthu:
    render_doanhthu(DOANHTHU_FILE_ID)

with tab_odr:
    render_odr(TTS_PHAT_FILE_ID)

with tab_opr:
    render_opr(TTS_THU_FILE_ID)

