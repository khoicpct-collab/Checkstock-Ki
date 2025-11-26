# pages/2_nhap_xuat_kho.py
import streamlit as st
import pandas as pd
from database import get_conn
from datetime import date

st.title("📦 Nhap / Xuat kho")

conn = get_conn()
df = pd.read_sql_query("SELECT * FROM inventory ORDER BY ngay DESC LIMIT 1000", conn)
conn.close()

materials = sorted(df['nguyen_lieu'].dropna().unique().tolist()) if not df.empty else []
mat = st.selectbox("Chon nguyen lieu hoac nhap ten moi", [""] + materials)

mode = st.radio("Chon che do", ["Nhap moi", "Xuat"])
lo = st.text_input("Lo (ma lo)")
so_bao = st.number_input("So bao", value=0, step=1)
so_kg = st.number_input("So kg", value=0.0, step=0.1)
ngay = st.date_input("Ngay", date.today())
ncc = st.text_input("NCC")

if st.button("Thuc hien"):
    if not mat:
        st.error("Vui long chon hoac nhap ten nguyen lieu")
    else:
        conn = get_conn()
        trung = (so_kg/so_bao) if so_bao>0 else None
        sign_kg = so_kg if mode=="Nhap moi" else -so_kg
        conn.execute("""
            INSERT INTO inventory(ngay, nguyen_lieu, lo, so_bao, so_kg, trung_binh, remain_kg, nhap_kg, xuat_kg, ton_cuoi_kg, ncc, product_date, formula_date, age)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            str(ngay),
            mat,
            lo,
            so_bao,
            sign_kg,
            trung,
            sign_kg,
            so_kg if mode=="Nhap moi" else 0,
            so_kg if mode=="Xuat" else 0,
            None,
            ncc,
            str(ngay),
            None,
            0
        ))
        conn.commit()
        conn.close()
        st.success("Thuc hien thanh cong")
