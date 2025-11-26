import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection

st.title("📊 Báo cáo tồn kho")

conn = get_connection()

try:
    df = pd.read_sql("SELECT * FROM stock", conn)

    st.subheader("Biểu đồ tồn kho")
    fig = px.bar(df, x="ten_hang", y="so_luong")
    st.plotly_chart(fig, use_container_width=True)

except Exception:
    st.warning("Chưa có dữ liệu để tạo báo cáo.")
