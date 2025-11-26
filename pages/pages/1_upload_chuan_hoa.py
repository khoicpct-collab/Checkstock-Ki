import streamlit as st
import pandas as pd

st.set_page_config(page_title="Upload & Chuẩn hoá")

st.title("📤 Upload & Chuẩn hoá dữ liệu")

uploaded_file = st.file_uploader(
    "Chọn file Excel Check stock KI", 
    type=["xlsx", "xls"]
)

if uploaded_file:
    try:
        # Đọc toàn bộ sheets
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names

        st.success("✔️ Đã đọc file. Chọn sheet để xem dữ liệu.")

        sheet = st.selectbox("Chọn sheet:", sheet_names)

        df = pd.read_excel(uploaded_file, sheet_name=sheet)

        st.subheader("📌 20 dòng đầu")
        st.dataframe(df.head(20))

        # Nút chuẩn hóa
        if st.button("Chuẩn hoá & Lưu dữ liệu"):
            df_clean = df.copy()

            # Chuẩn hoá cần thêm tại đây…
            df_clean["Age"] = None  # placeholder

            st.session_state["inventory_df"] = df_clean

            df_clean.to_csv("inventory_clean.csv", index=False)

            st.success("🎉 Đã chuẩn hoá & lưu dữ liệu thành công!")

    except Exception as e:
        st.error(f"Lỗi khi đọc file: {e}")

else:
    st.info("Vui lòng tải file Excel để bắt đầu.")
