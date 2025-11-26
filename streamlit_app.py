import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Quan Ly Ton Kho", layout="wide")

# Tao ket noi SQLite
def init_db():
    conn = sqlite3.connect("stock.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stock_detailed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_name TEXT,
        group_name TEXT,
        loai_bao TEXT,
        trong_luong_bao REAL,
        don_vi TEXT,
        location TEXT,
        so_bao INTEGER,
        so_kg REAL,
        avg_kg_per_bao REAL,
        ngay_nhap TEXT,
        product_date TEXT,
        age_days INTEGER
    )
    """)
    conn.commit()
    return conn

conn = init_db()

st.title("HE THONG QUAN LY TON KHO - MODULE 1")
st.subheader("UPLOAD FILE - PREVIEW - CHUAN HOA - LUU DATABASE")

uploaded = st.file_uploader("Tai file Excel", type=["xlsx"])

def clean_material_name(name):
    if pd.isna(name):
        return ""
    name = str(name).strip().upper()
    name = name.replace("  ", " ")
    return name

def tinh_age(ngay_nhap):
    try:
        d = pd.to_datetime(ngay_nhap, errors="coerce")
        if pd.isna(d):
            return None
        return (pd.Timestamp.today() - d).days
    except:
        return None

if uploaded:
    df = pd.read_excel(uploaded)
    st.write("Xem truoc 30 dong:")
    st.dataframe(df.head(30))

    st.subheader("Tien hanh chuan hoa du lieu")

    # Bo sung ten nguyen lieu
    if "material_name" not in df.columns:
        st.error("File Excel chua co cot material_name. Ban can gui file mau dung.")
    else:
        df["material_name"] = df["material_name"].apply(clean_material_name)

    # Tinh tuoi ton kho
    if "ngay_nhap" in df.columns:
        df["age_days"] = df["ngay_nhap"].apply(tinh_age)
    else:
        df["age_days"] = None

    st.success("Da chuan hoa truoc khi luu")

    st.write("Xem lai du lieu da chuan hoa:")
    st.dataframe(df.head(20))

    # Nut luu
    if st.button("Luu vao SQLite"):
        df_to_save = df[[
            "material_name", "group_name", "loai_bao", "trong_luong_bao",
            "don_vi", "location", "so_bao", "so_kg",
            "avg_kg_per_bao", "ngay_nhap", "product_date", "age_days"
        ]]

        df_to_save.to_sql("stock_detailed", conn, if_exists="append", index=False)

        st.success("Da luu vao database SQLite thanh cong!")
        st.balloons()

st.markdown("---")
st.info("Module 1 hoan tat. Nhan tin de bat dau Module 2 – Nhap lieu theo ten nguyen lieu.")
