import streamlit as st
from tabs.tab_odr.main import render as render_odr
from tabs.tab_doanhthu.main import render as render_doanhthu
from tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Tiktoks Dashboard", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <h2 style="color: #c62828; display: flex; align-items: center; gap: 14px; font-weight: bold; font-family: sans-serif;">
        <!-- Icon TikTok Shop SVG chuẩn nét & đẹp -->
        <svg width="38" height="38" viewBox="0 0 512 512" style="display:inline-block; vertical-align:middle; filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.15));">
            <!-- Hiệu ứng viền/bóng Neon Cyan bên trái -->
            <path d="M110,150 C110,150 95,270 105,370 C115,440 150,470 205,470 C170,430 155,380 155,320 C155,230 190,170 235,138 Z" fill="#25F4EE"/>
            <!-- Hiệu ứng viền/bóng Neon Hồng/Đỏ bên phải -->
            <path d="M402,150 C402,150 417,270 407,370 C397,440 362,470 307,470 C342,430 357,380 357,320 C357,230 322,170 277,138 Z" fill="#FE2C55"/>
            <!-- Thân túi mua sắm chính (Đen tuyền, bo góc mềm mại) -->
            <rect x="96" y="144" width="320" height="304" rx="36" fill="#121212"/>
            <!-- Quai túi -->
            <path d="M192,144 L192,100 C192,58 220,24 256,24 C292,24 320,58 320,100 L320,144" fill="none" stroke="#121212" stroke-width="28" stroke-linecap="round"/>
            <path d="M192,144 L192,100 C192,58 220,24 256,24 C292,24 320,58 320,100 L320,144" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" opacity="0.15"/>
            <!-- Biểu tượng nốt nhạc TikTok màu trắng chính giữa -->
            <path d="M312,204 C312,236 336,256 364,260 L364,304 C338,304 314,296 294,280 L294,364 C294,412 254,452 206,452 C158,452 118,412 118,364 C118,316 158,276 206,276 C216,276 225,278 233,282 L233,328 C226,326 218,324 206,324 C182,324 162,344 162,368 C162,392 182,412 206,412 C230,412 250,392 250,368 L250,180 L312,180 Z" fill="#FFFFFF"/>
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


