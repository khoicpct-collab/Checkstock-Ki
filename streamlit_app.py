# -----------------------
# MODULE 9 - XUAT BAO CAO (EXCEL + PDF)
# -----------------------
import io
import xlsxwriter
from fpdf import FPDF

with st.expander("MODULE 9 - Xuat bao cao tong hop"):
    st.header("Xuat bao cao: Excel & PDF")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM warehouse", conn)
    conn.close()

    if df.empty:
        st.info("Chua co du lieu de xuat.")
    else:
        # filters
        ten = st.selectbox("Chon nguyen lieu (Tat ca de xuat toan bo)", ["Tat ca"] + sorted(df["ten_nguyen_lieu"].unique().tolist()))
        date_from = st.date_input("Tu ngay", value=None, key="r_from")
        date_to = st.date_input("Den ngay", value=None, key="r_to")

        dff = df.copy()
        if ten != "Tat ca":
            dff = dff[dff["ten_nguyen_lieu"] == ten]
        # optional date filter
        try:
            if date_from:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors="coerce").dt.date >= date_from]
            if date_to:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors="coerce").dt.date <= date_to]
        except:
            pass

        st.dataframe(dff.head(200))

        # Export Excel
        if st.button("Xuat Excel"):
            towrite = io.BytesIO()
            writer = pd.ExcelWriter(towrite, engine='xlsxwriter')
            dff.to_excel(writer, index=False, sheet_name='BaoCao')
            writer.close()
            towrite.seek(0)
            st.download_button("Tai file Excel", data=towrite, file_name="baocao_tonkho.xlsx")

        # Export PDF (simple table)
        if st.button("Xuat PDF"):
            pdf = FPDF("L","mm","A4")
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.cell(0,10, "Bao cao ton kho", ln=True)
            # simple table write (first 30 rows)
            for i,row in dff.head(30).iterrows():
                line = f"{row.get('ten_nguyen_lieu','')[:20]:20} | {str(row.get('lo','')):8} | {row.get('khoi_luong_kg',0):10,.2f}"
                pdf.cell(0,6,line,ln=True)
            # return file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                tmp.seek(0)
                data = open(tmp.name,"rb").read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="baocao.pdf">Tai PDF</a>'
                st.markdown(href, unsafe_allow_html=True)
