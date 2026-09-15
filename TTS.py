import streamlit as st
from tabs.tab_odr.main import render as render_odr
from tabs.tab_doanhthu.main import render as render_doanhthu
from tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Tiktoks Dashboard", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 10px; font-weight: bold;">
        <!-- Icon SVG chuẩn của TikTok / TikTok Shop -->
        <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor" style="display:inline-block; vertical-align:middle;">
            <path d="M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-5.201 1.743l-.002-.001.002.001a2.895 2.895 0 0 1 3.144-4.53v-3.46a6.342 6.342 0 0 0-5.32 6.275 6.343 6.343 0 0 0 10.25 4.951 6.335 6.335 0 0 0 2.152-4.802V9.45a8.196 8.196 0 0 0 4.79 1.528V7.532a4.836 4.836 0 0 1-1.354-.846z"/>
        </svg>
        TIKTOK SHOP DASHBOARD
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
TTS_PHAT_FILE_ID = "1BCn1CH_VNWMslHxe1MQ4q9F2bJhbhY0o"
DOANHTHU_FILE_ID = "1BCn1CH_VNWMslHxe1MQ4q9F2bJhbhY0o"  # Điền File ID của dữ liệu doanh thu nếu dùng riêng
TTS_THU_FILE_ID = "1OUeMwfOHuI1sOMU2ilQySYK2IOl8Xx4n" 

# Khai báo 2 tab
tab_doanhthu, tab_odr, tab_opr = st.tabs(["💰 TAB DOANH THU","🚚 TAB ODR","⚡ TAB OPR"])

with tab_doanhthu:
    render_doanhthu(DOANHTHU_FILE_ID)

with tab_odr:
    render_odr(TTS_PHAT_FILE_ID)

with tab_opr:
    render_opr(TTS_THU_FILE_ID)


