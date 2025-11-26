import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nhập liệu nguyên liệu")

st.title("📥 Nhập liệu nguyên liệu")

# Kiểm tra dữ liệu có trong session chưa
if "inventory_df" not in st.session_state:
    st.warning("⚠️ Chưa có dữ liệu! Vui lòng vào trang **Upload & Chuẩn hoá** trước.")
    st.stop()

df = st.session_state["inventory_df"]

st.subheader("📌 Danh sách nguyên liệu hiện có")
st.dataframe(df.head())

st.divider()

# Form thêm nguyên liệu mới
st.subheader("➕ Thêm nguyên liệu")

with st.form("add_material"):
    ma = st.text_input("Mã nguyên liệu")
    ten = st.text_input("Tên nguyên liệu")
    ton_dau = st.number_input("Tồn đầu kỳ", 0.0)
    nhap = st.number_input("Nhập", 0.0)
    xuat = st.number_input("Xuất", 0.0)

    submitted = st.form_submit_button("Thêm")

    if submitted:
        new_row = {
            "Mã hàng": ma,
            "Tên hàng": ten,
            "Tồn đầu kỳ": ton_dau,
            "Nhập": nhap,
            "Xuất": xuat,
            "Tồn cuối": ton_dau + nhap - xuat
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["inventory_df"] = df

        df.to_csv("inventory_clean.csv", index=False)

        st.success("🎉 Thêm thành công!")
        st.dataframe(df.tail(5))
