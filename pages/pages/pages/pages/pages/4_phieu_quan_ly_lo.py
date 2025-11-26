# pages/4_phieu_quan_ly_lo.py
import streamlit as st
import pandas as pd
from database import get_conn
from fpdf import FPDF
import tempfile, base64

st.title("📝 Phieu quan ly lo (A5)")

conn = get_conn()
df = pd.read_sql_query("SELECT * FROM inventory", conn)
conn.close()

lots = sorted(df['lo'].dropna().unique().tolist()) if not df.empty else []
chosen = st.selectbox("Chon lo can in", [""] + lots)
if chosen:
    df_l = df[df['lo']==chosen]
    st.dataframe(df_l)
    if st.button("Tao phieu PDF (A5)"):
        row = df_l.iloc[0]
        pdf = FPDF("P","mm","A5")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=5)
        pdf.set_font("Arial","B",14)
        pdf.cell(0,10,"PHIEU QUAN LY LO",ln=True,align="C")
        pdf.ln(4)
        pdf.set_font("Arial","",11)
        def line(k,v):
            pdf.set_font("Arial","B",10)
            pdf.cell(45,6,str(k)+":")
            pdf.set_font("Arial","",10)
            pdf.multi_cell(0,6,str(v))
        line("Ten nguyen lieu", row.get('nguyen_lieu',''))
        line("Ma lo", row.get('lo',''))
        line("Ngay nhap", row.get('ngay',''))
        line("So bao", row.get('so_bao',''))
        line("Khoi luong (kg)", row.get('so_kg',''))
        line("Trung binh (kg/bao)", row.get('trung_binh',''))
        line("NCC", row.get('ncc',''))
        line("Tuoi (ngay)", row.get('age',''))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name
        with open(tmp_path,"rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="phieu_{chosen}.pdf">Tai phieu PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
