# ============================
# STREAMLIT APP - MODULE 3
# QUẢN LÝ KHO NGUYÊN LIỆU (Chuẩn hoá + Nhập/Xuất + Nhóm)
# ============================

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ------------------------------
# KẾT NỐI DATABASE SQLITE
# ------------------------------
DB_PATH = "warehouse.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS warehouse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_nguyen_lieu TEXT,
            lo TEXT,
            so_bao INTEGER,
            khoi_luong_kg REAL,
            trung_binh_kg REAL,
            ngay_nhap TEXT,
            age INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------------------
# HÀM CHUẨN HOÁ DỮ LIỆU
# ------------------------------
def clean_data(df):
    df = df.copy()

    # Chuẩn hoá tên cột
    df.columns = df.columns.str.strip().str.lower()

    # Đổi tên cột theo chuẩn
    rename_map = {
        "ten": "ten_nguyen_lieu",
        "ten nguyen lieu": "ten_nguyen_lieu",
        "lo": "lo",
        "ngay": "ngay_nhap",
        "ngay nhap": "ngay_nhap",
        "kg": "khoi_luong_kg",
        "so bao": "so_bao",
        "so_bao": "so_bao"
    }
    df = df.rename(columns=rename_map)

    # Xử lý ngày nhập
    df["ngay_nhap"] = pd.to_datetime(df["ngay_nhap"], errors="coerce")

    # Tính Age
    today = pd.to_datetime(datetime.now().date())
    df["age"] = (today - df["ngay_nhap"]).dt.days

    # Xử lý trung bình bao (các dòng có số âm là trung bình)
    df["trung_binh_kg"] = None
    mask_bao = df["so_bao"].astype(float) > 0

    df.loc[mask_bao, "trung_binh_kg"] = (
        df.loc[mask_bao, "khoi_luong_kg"] / df.loc[mask_bao, "so_bao"]
    )

    # Nguyên liệu xá hoặc chất lỏng — không tính trung bình
    df.loc[~mask_bao, "trung_binh_kg"] = df.loc[~mask_bao, "khoi_luong_kg"]

    return df

# ------------------------------
# LƯU DỮ LIỆU VÀO DATABASE
# ------------------------------
def save_to_db(df):
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("warehouse", conn, if_exists="append", index=False)
    conn.close()

# ------------------------------
# LẤY DANH SÁCH NGUYÊN LIỆU
# ------------------------------
def get_materials():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM warehouse", conn)
    conn.close()
    return df

# ------------------------------
# GIAO DIỆN APP
# ------------------------------
st.title("📦 Quản Lý Kho Nguyên Liệu — Module 3 (FULL)")

tabs = st.tabs(["1. Upload & Chuẩn hoá", "2. Nhóm nguyên liệu", "3. Nhập thêm / Xuất"])

# ======================================
# TAB 1 — UPLOAD & CHUẨN HOÁ
# ======================================
with tabs[0]:
    st.header("📤 Tải file Excel gốc để chuẩn hoá")

    uploaded = st.file_uploader("Chọn file Excel", type=["xlsx", "xls"])

    if uploaded:
        raw_df = pd.read_excel(uploaded)
        st.subheader("🔍 20 dòng đầu (dữ liệu gốc)")
        st.dataframe(raw_df.head(20))

        st.info("➡ Nhấn nút bên dưới để chuẩn hoá")

        if st.button("Chuẩn hoá dữ liệu"):
            clean_df = clean_data(raw_df)

            st.success("✅ Đã chuẩn hoá xong!")
            st.dataframe(clean_df.head(20))

            st.download_button("📥 Download file đã chuẩn hoá",
                               clean_df.to_excel("cleaned.xlsx", index=False),
                               "cleaned.xlsx")

            if st.button("Lưu vào database"):
                save_to_db(clean_df)
                st.success("✅ Lưu thành công vào database!")

# ======================================
# TAB 2 — NHÓM NGUYÊN LIỆU
# ======================================
with tabs[1]:
    st.header("📚 Nhóm nguyên liệu")

    df = get_materials()

    if df.empty:
        st.warning("❗Chưa có dữ liệu trong kho. Hãy nhập từ Tab 1.")
    else:
        materials = sorted(df["ten_nguyen_lieu"].unique())
        selected = st.selectbox("Chọn tên nguyên liệu", materials)

        group_df = df[df["ten_nguyen_lieu"] == selected]

        st.subheader(f"📌 Nhóm: {selected}")
        st.dataframe(group_df)

        st.download_button(
            label="📥 Xuất nhóm này ra Excel",
            data=group_df.to_excel(f"{selected}.xlsx", index=False),
            file_name=f"{selected}.xlsx"
        )

# ======================================
# TAB 3 — NHẬP THÊM / XUẤT
# ======================================
with tabs[2]:
    st.header("➕ Nhập thêm / ➖ Xuất nguyên liệu")

    df = get_materials()

    if df.empty:
        st.warning("❗Chưa có dữ liệu trong kho.")
    else:
        mode = st.selectbox("Chọn chế độ", ["Nhập thêm", "Xuất sử dụng"])

        ten = st.text_input("Tên nguyên liệu")
        lo = st.text_input("Lô")
        so_bao = st.number_input("Số bao", min_value=0, value=0)
        kg = st.number_input("Khối lượng (kg)", min_value=0.0, step=0.1)
        ngay = st.date_input("Ngày thực hiện")

        if st.button("Lưu lại"):
            new_df = pd.DataFrame([{
                "ten_nguyen_lieu": ten,
                "lo": lo,
                "so_bao": so_bao,
                "khoi_luong_kg": kg if mode == "Nhập thêm" else -kg,
                "trung_binh_kg": (kg / so_bao) if so_bao > 0 else kg,
                "ngay_nhap": ngay,
                "age": 0
            }])

            save_to_db(new_df)
            st.success("✅ Lưu thành công!")

