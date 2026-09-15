import streamlit as st
from tabs.tab_odr.main import render as render_odr
from tabs.tab_doanhthu.main import render as render_doanhthu
from tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Tiktoks Dashboard", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 12px; font-weight: bold;">
        <!-- Icon TikTok Shop SVG chuẩn -->
        <svg width="32" height="32" viewBox="0 0 512 512" style="display:inline-block; vertical-align:middle;">
            <!-- Hiệu ứng bóng/viền màu xanh Cyan bên trái -->
            <path d="M128,96 C128,96 112,240 118,360 C124,450 160,480 220,480 C180,440 160,380 160,320 C160,220 200,140 256,96 Z" fill="#25F4EE" opacity="0.9"/>
            <!-- Hiệu ứng bóng/viền màu Hồng/Đỏ bên phải -->
            <path d="M384,96 C384,96 400,240 394,360 C388,450 352,480 292,480 C332,440 352,380 352,320 C352,220 312,140 256,96 Z" fill="#FE2C55" opacity="0.9"/>
            <!-- Phần thân túi chính màu đen -->
            <path d="M120,136 L392,136 C410,136 424,150 428,168 L472,392 C478,422 454,448 424,448 L88,448 C58,448 34,422 40,392 L84,168 C88,150 102,136 120,136 Z" fill="#010101"/>
            <!-- Quai túi màu đen/trắng -->
            <path d="M180,136 L180,88 C180,48 212,16 256,16 C300,16 332,48 332,88 L332,136" fill="none" stroke="#010101" stroke-width="32" stroke-linecap="round"/>
            <!-- Biểu tượng nốt nhạc TikTok màu trắng ở giữa túi -->
            <path d="M296,192 C296,224 320,244 348,248 L348,292 C324,292 300,284 280,268 L280,356 C280,404 240,444 192,444 C144,444 104,404 104,356 C104,308 144,268 192,268 C200,268 208,270 216,274 L216,318 C210,316 202,314 192,314 C168,314 148,334 148,358 C148,382 168,402 192,402 C216,402 236,382 236,358 L236,192 L296,192 Z" fill="#FFFFFF"/>
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


