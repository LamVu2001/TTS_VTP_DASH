import streamlit as st
from SPE_tabs.tab_odr.main import render as render_odr
from SPE_tabs.tab_doanhthu.main import render as render_doanhthu
from SPE_tabs.tab_opr.main import render as render_opr

# Đặt cấu hình trang & Tiêu đề chung ở đây để nó hiện trên tất cả các tabs
st.set_page_config(page_title="Shopee", layout="wide")

# Tiêu đề với màu đỏ đồng bộ chuẩn với thanh line phân cách
st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
        <!-- LOGO SHOPEE VECTOR CHUẨN NÉT MẢNH -->
        <svg width="100" height="100" viewBox="0 0 512 512" style="display:block;">
            <!-- Thân túi: Màu cam chuẩn, bo góc mềm mại -->
            <path d="M110,146 L402,146 C428,146 448,166 452,192 L492,408 C498,436 476,462 446,462 L66,462 C36,462 14,436 20,408 L60,192 C64,166 84,146 110,146 Z" fill="#EE4D2D"/>
            <!-- Quai túi: Nét mảnh, tinh tế -->
            <path d="M184,146 L184,104 C184,64 216,32 256,32 C296,32 328,64 328,104 L328,146" fill="none" stroke="#EE4D2D" stroke-width="30" stroke-linecap="round"/>
            <!-- Chữ S: Nét đều, mượt mà, mảnh mai đúng chuẩn -->
            <path d="M288,215 C262,192 228,186 200,198 C172,210 158,235 163,263 C168,291 196,306 232,321 C268,336 305,354 305,401 C305,445 264,472 212,472 C168,472 138,450 118,428" fill="none" stroke="#FFFFFF" stroke-width="32" stroke-linecap="round"/>
        </svg>
        <!-- TEXT SHOPEE: Font chữ tròn trịa, thanh mảnh đi kèm -->
        <div style="margin-top: 15px; font-size: 36px; font-weight: 400; color: #EE4D2D; letter-spacing: -0.5px;">
            Shopee
        </div>
    </div>
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

