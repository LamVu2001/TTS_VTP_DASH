import streamlit as st
from SPE_tabs.tab_odr.main import render as render_odr
from SPE_tabs.tab_doanhthu.main import render as render_doanhthu
from SPE_tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Shopee", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 14px; font-weight: bold; font-family: sans-serif;">
        <!-- ICON SHOPEE SVG -->
        <svg width="38" height="38" viewBox="0 0 512 512" style="display:inline-block; vertical-align:middle; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.15));">
            <!-- Nền túi màu cam đặc trưng của Shopee -->
            <path d="M120,136 L392,136 C410,136 424,150 428,168 L472,392 C478,422 454,448 424,448 L88,448 C58,448 34,422 40,392 L84,168 C88,150 102,136 120,136 Z" fill="#EE4D2D"/>
            <!-- Quai túi màu cam đậm -->
            <path d="M180,136 L180,88 C180,48 212,16 256,16 C300,16 332,48 332,88 L332,136" fill="none" stroke="#D73211" stroke-width="32" stroke-linecap="round"/>
            <!-- Chữ 'S' trắng cách điệu biểu tượng Shopee ở giữa túi -->
            <path d="M220,210 C180,210 160,235 160,270 C160,305 190,320 230,335 C275,350 300,370 300,410 C300,455 260,475 210,475 C160,475 135,445 130,415 L175,395 C180,420 200,435 215,435 C240,435 255,420 255,400 C255,375 235,360 195,345 C150,330 115,305 115,260 C115,200 165,175 220,175 C275,175 305,200 315,225 L275,245 C265,225 245,210 220,210 Z" fill="#FFFFFF"/>
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

