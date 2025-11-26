import streamlit as st
import pandas as pd
from utils import clean_dataframe
from database import get_connection

st.title("📤 Upload & Chuẩn hoá")

uploaded = st.file_uploader("Chọn file Excel", type=["xlsx", "xls"])

if uploaded:
    try:
        df = pd.read_excel(uploaded)
        df = clean_dataframe(df)

        st.success("✔ Đọc file thành công!")
        st.dataframe(df)

        if st.button("Lưu vào Database"):
            conn = get_connection()
            df.to_sql("stock", conn, if_exists="append", index=False)
            st.success("✔ Đã lưu dữ liệu vào database!")

    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
