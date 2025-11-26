# pages/3_bao_cao_ton_kho.py
import streamlit as st
import pandas as pd
from database import get_conn
import io
from fpdf import FPDF
import base64
import tempfile

st.title("📊 Bao cao ton kho")

conn = get_conn()
df = pd.read_sql_query("SELECT * FROM inventory", conn)
conn.close()

if df.empty:
    st.info("Chua co du lieu de bao cao")
else:
    ten = st.selectbox("Chon nguyen lieu (Tat ca de xuat toan bo)", ["Tat ca"] + sorted(df["nguyen_lieu"].dropna().unique().tolist()))
    if ten != "Tat ca":
        dff = df[df["nguyen_lieu"]==ten]
    else:
        dff = df.copy()

    st.dataframe(dff.head(200))

    # xuat excel
    def df_to_bytes(df):
        towrite = io.BytesIO()
        writer = pd.ExcelWriter(towrite, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='BaoCao')
        writer.close()
        towrite.seek(0)
        return towrite.read()

    if st.button("Xuat Excel"):
        data = df_to_bytes(dff)
        st.download_button("Tai Excel", data=data, file_name="baocao_tonkho.xlsx")

    # xuat PDF don gian (A4 ngang)
    if st.button("Xuat PDF nhanh"):
        pdf = FPDF("L","mm","A4")
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(0,10, "Bao cao ton kho", ln=True)
        for i,row in dff.head(100).iterrows():
            line = f"{str(row.get('nguyen_lieu',''))[:30]:30} | {str(row.get('lo','')):8} | {row.get('so_kg',0):10,.2f}"
            pdf.cell(0,6,line,ln=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name
        with open(tmp_path,"rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="baocao.pdf">Tai PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
