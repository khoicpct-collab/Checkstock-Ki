import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.title("NHAP LIEU NGUYEN LIEU")

def get_conn():
    return sqlite3.connect("stock.db", check_same_thread=False)

conn = get_conn()

# Lay danh sach nguyen lieu
@st.cache_data
def load_materials():
    df = pd.read_sql("SELECT DISTINCT material_name FROM stock_detailed ORDER BY material_name", conn)
    return df["material_name"].tolist()

materials = load_materials()

# AUTOCOMPLETE
material = st.selectbox("Chon nguyen lieu", materials)

if material:
    st.subheader(f"Thong tin cac lo cua: {material}")

    query = """
    SELECT * FROM stock_detailed
    WHERE material_name = ?
    ORDER BY location
    """
    df = pd.read_sql(query, conn, params=[material])
    st.dataframe(df)

    st.markdown("---")
    st.subheader("NHAP THEM LO HOAC THEM TON")

    # Chon lo
    list_lo = ["TAO LO MOI"] + sorted(df["location"].unique().tolist())
    lo = st.selectbox("Chon lo", list_lo)

    so_bao = st.number_input("So bao nhap", value=0, step=1)
    so_kg = st.number_input("So kg nhap", value=0.0, step=1.0)

    ngay_nhap = st.date_input("Ngay nhap", datetime.today())
    ngay_sx = st.date_input("Ngay san xuat", datetime.today())

    ncc = st.text_input("Nha cung cap")
    code = st.text_input("Code")
    ghi_chu = st.text_area("Ghi chu")

    # Tinh avg
    avg = None
    if so_bao != 0:
        avg = so_kg / so_bao

    # Tuoi
    age_days = (datetime.today().date() - ngay_nhap).days

    if st.button("Luu du lieu"):
        new_row = pd.DataFrame([{
            "material_name": material,
            "group_name": None,
            "loai_bao": None,
            "trong_luong_bao": None,
            "don_vi": "kg",
            "location": lo,
            "so_bao": so_bao,
            "so_kg": so_kg,
            "avg_kg_per_bao": avg,
            "ngay_nhap": str(ngay_nhap),
            "product_date": str(ngay_sx),
            "age_days": age_days
        }])

        new_row.to_sql("stock_detailed", conn, if_exists="append", index=False)
        st.success("Da luu thanh cong!")
        st.balloons()
