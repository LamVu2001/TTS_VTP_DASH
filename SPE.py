# trang_moi.py
import streamlit as st

st.title("🌟 TRANG BÁO CÁO MỚI")
st.write("Đây là nội dung, bộ lọc và các biểu đồ của trang mới hoàn toàn độc lập.")

# Ví dụ thêm một vài thành phần:
metric1, metric2 = st.columns(2)
with metric1:
    st.metric("Chỉ số mới 1", "1,234", "+5%")
with metric2:
    st.metric("Chỉ số mới 2", "567", "-2%")
