import streamlit as st
import pandas as pd
from utils import clean_inventory_dataframe
from database import init_db, save_dataframe

st.title("📤 Upload & Chuẩn hoá dữ liệu")

st.write("Tải file Excel, chọn sheet, chuẩn hoá và lưu vào database.")

uploaded = st.file_uploader("Chọn file Excel", type=["xlsx", "xls"])

if uploaded:
    try:
        # Load workbook
        xls = pd.ExcelFile(uploaded)
        sheet_name = st.selectbox("Chọn sheet", xls.sheet_names)

        if st.button("Đọc và chuẩn hoá"):
            df_raw = pd.read_excel(uploaded, sheet_name=sheet_name)

            st.subheader("Dữ liệu thô – Raw (20 dòng)")
            st.dataframe(df_raw.head(20))

            df_clean = clean_inventory_dataframe(df_raw)

            st.subheader("Dữ liệu đã chuẩn hoá – Clean (20 dòng)")
            st.dataframe(df_clean.head(20))

            # Lưu database
            init_db()
            save_dataframe(df_clean, "inventory")

            st.success("🎉 Đã chuẩn hoá & lưu vào database thành công!")

    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")
