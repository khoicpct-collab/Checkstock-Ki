# ============================
# MODULE 4: UPLOAD & CHUẨN HOÁ
# ============================

import pandas as pd
import streamlit as st

def page_upload_chuan_hoa():
    st.title("📤 Upload & Chuẩn hoá dữ liệu tồn kho")

    uploaded = st.file_uploader("Chọn file Excel (.xlsx)", type=["xlsx"])
    if uploaded is None:
        st.info("Hãy upload file để tiếp tục.")
        return

    # Đọc thử file để lấy danh sách sheet
    try:
        excel_file = pd.ExcelFile(uploaded)
        sheets = excel_file.sheet_names
    except Exception as e:
        st.error(f"Lỗi đọc file Excel: {e}")
        return

    sheet = st.selectbox("Chọn sheet:", sheets)

    if st.button("📥 Đọc & Chuẩn hoá"):
        try:
            df_raw = pd.read_excel(uploaded, sheet_name=sheet)

            st.subheader("📌 Dữ liệu gốc")
            st.dataframe(df_raw.head())

            # ------------------------------
            # CHUẨN HOÁ DỮ LIỆU
            # ------------------------------

            df = df_raw.copy()

            # Chuẩn tên cột
            df.columns = (
                df.columns.str.strip()
                .str.replace("\n", " ")
                .str.replace("  ", " ")
            )

            # Các cột bắt buộc (tùy theo bạn muốn)
            required_cols = ["Mã hàng", "Tên hàng", "Tồn đầu kỳ", "Nhập", "Xuất", "Tồn cuối"]

            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.warning(f"⚠️ Thiếu cột: {missing}")
            
            # ép kiểu số
            numeric_cols = ["Tồn đầu kỳ", "Nhập", "Xuất", "Tồn cuối"]
            for c in numeric_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

            # Lưu vào session_state
            st.session_state["inventory_df"] = df

            # Lưu CSV local (để Dashboard xài)
            df.to_csv("inventory_clean.csv", index=False)

            st.success("🎉 Chuẩn hoá thành công! Dữ liệu đã được lưu.")
            st.subheader("📦 Dữ liệu đã chuẩn hoá")
            st.dataframe(df.head())

        except Exception as e:
            st.error(f"❌ Lỗi xử lý: {e}")
