import streamlit as st
import pandas as pd
from database import get_connection

st.title("📦 Nhập – Xuất kho")

conn = get_connection()
df = pd.read_sql("SELECT * FROM stock", conn)

st.subheader("Dữ liệu trong kho")
st.dataframe(df)
