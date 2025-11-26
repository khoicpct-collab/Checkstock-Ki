# pages/1_upload_chuan_hoa.py
import streamlit as st
import pandas as pd
from database import get_conn
from utils import parse_complex_sheet
import io
import datetime

st.title("📤 Upload & Chuan hoa")

uploaded = st.file_uploader("Chon file Excel (Check stock KI.xlsx)", type=["xlsx","xls"])
if uploaded:
    xls = pd.ExcelFile(uploaded)
    sheets = xls.sheet_names
    sheet = st.selectbox("Chon sheet de parse", sheets)
    st.write("Sheet chon:", sheet)
    df_raw = pd.read_excel(uploaded, sheet_name=sheet, header=None)
    st.subheader("Preview (raw 50 dong)")
    st.dataframe(df_raw.head(50))

    if st.button("Thuc hien parse & chuan hoa"):
        with st.spinner("Dang parse..."):
            df_parsed = parse_complex_sheet(df_raw)
        if df_parsed.empty:
            st.error("Khong tim thay ban ghi sau khi parse. Kiem tra sheet.")
        else:
            st.success(f"Parse xong: {len(df_parsed)} ban ghi")
            st.dataframe(df_parsed.head(50))
            b = io.BytesIO()
            df_parsed.to_excel(b, index=False, sheet_name="cleaned")
            st.download_button("Tai file da chuan hoa (Excel)", data=b.getvalue(), file_name="cleaned_parsed.xlsx")

            if st.button("Luu tat ca vao DB"):
                conn = get_conn()
                df_parsed = df_parsed.where(pd.notnull(df_parsed), None)
                for _, r in df_parsed.iterrows():
                    conn.execute("""
                    INSERT INTO inventory(ngay, nguyen_lieu, lo, so_bao, so_kg, trung_binh, remain_kg, nhap_kg, xuat_kg, ton_cuoi_kg, ncc, product_date, formula_date, age)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        r.get('ngay_nhap'),
                        r.get('ten_nguyen_lieu'),
                        r.get('lo'),
                        r.get('so_bao'),
                        r.get('so_kg'),
                        r.get('trung_binh'),
                        r.get('so_kg'), # remain_kg (khoi dau)
                        r.get('nhap_kg'),
                        r.get('xuat_kg'),
                        r.get('ton_cuoi_kg'),
                        r.get('ncc'),
                        r.get('ngay_nhap'),
                        None,
                        r.get('age')
                    ))
                conn.commit()
                conn.close()
                st.success("Da luu vao DB")
