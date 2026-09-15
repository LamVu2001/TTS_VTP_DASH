import streamlit as st
from SPE_tabs.tab_odr.main import render as render_odr
from SPE_tabs.tab_doanhthu.main import render as render_doanhthu
from SPE_tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Shopee", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 14px; font-weight: bold; font-family: sans-serif;">
        <!-- ICON SHOPEE CHUẨN MẪU GỐC -->
        <svg width="38" height="38" viewBox="0 0 512 512" style="display:inline-block; vertical-align:middle;">
            <!-- Quai túi (Vẽ trước để nằm phía sau hoặc vừa vặn phía trên thân) -->
            <path d="M176,140 L176,96 C176,52 212,16 256,16 C300,16 336,52 336,96 L336,140" fill="none" stroke="#EE4D2D" stroke-width="32" stroke-linecap="round"/>
            <!-- Thân túi màu cam (Bo góc mềm) -->
            <path d="M100,140 L412,140 C434,140 452,158 456,180 L492,396 C498,430 470,456 436,456 L76,456 C42,456 14,430 20,396 L56,180 C60,158 78,140 100,140 Z" fill="#EE4D2D"/>
            <!-- Chữ 'S' trắng nét đều, mượt mà chính giữa túi -->
            <path d="M310,210 C280,185 240,180 205,192 C170,204 152,235 156,268 C160,298 190,315 235,332 C280,349 315,370 315,415 C315,462 265,490 210,490 C160,490 120,465 100,435" fill="none" stroke="#FFFFFF" stroke-width="32" stroke-linecap="round"/>
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

