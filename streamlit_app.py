# streamlit_app.py
# He thong quan ly ton kho - Full final (Modules 1..9)
# Tieng Viet KHONG DAU
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import io, tempfile, base64, unicodedata
import os

# try optional libs
try:
    from fpdf import FPDF
except:
    FPDF = None

st.set_page_config(page_title="He thong quan ly ton kho", layout="wide")

# ---------------------------
# CSS
# ---------------------------
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: 'Segoe UI', sans-serif; }
section[data-testid="stSidebar"] { background: #1f2a44 !important; color: white !important; }
.stButton>button { background-color:#2e86de; color:white; border-radius:8px; padding:8px 18px; font-size:14px; }
.block-container { padding-top: 1.2rem; }
h1,h2,h3 { color:#1f2a44; font-weight:650; }
.metric-label { font-weight:700; color:#1f2a44; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Database helpers
# ---------------------------
DB_FILE = "inventory.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet TEXT,
        ten_nguyen_lieu TEXT,
        lo TEXT,
        so_bao REAL,
        so_kg REAL,
        nhap_kg REAL,
        xuat_kg REAL,
        ton_cuoi_kg REAL,
        tb_kg_moi_bao REAL,
        ncc TEXT,
        ngay_nhap TEXT,
        product_date TEXT,
        age INTEGER,
        source TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        user TEXT,
        action TEXT,
        details TEXT
    );
    """)
    conn.commit()
    conn.close()

init_db()

def save_activity(action, details="", user="system"):
    conn = get_conn()
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn.execute("INSERT INTO activity_log (ts,user,action,details) VALUES (?,?,?,?)", (ts,user,action,details))
    conn.commit()
    conn.close()

# ---------------------------
# Utilities
# ---------------------------
def remove_accents(s):
    if pd.isna(s): return ""
    s2 = str(s)
    s2 = unicodedata.normalize('NFKD', s2)
    s2 = "".join([c for c in s2 if not unicodedata.combining(c)])
    return s2

def compute_age_from_date(d):
    try:
        dt = pd.to_datetime(d, errors='coerce')
        if pd.isna(dt): return None
        return (pd.Timestamp.today().normalize() - pd.to_datetime(dt).normalize()).days
    except:
        return None

def df_to_excel_bytes(df):
    towrite = io.BytesIO()
    writer = pd.ExcelWriter(towrite, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='data')
    writer.close()
    towrite.seek(0)
    return towrite.read()

# ---------------------------
# Parse heuristic for Check stock KI.xlsx
# ---------------------------
def parse_complex_sheet(df_raw, sheet_name="sheet"):
    dfr = df_raw.copy()
    header_idx = None
    for i in range(0, min(12, len(dfr))):
        rowvals = [str(x).upper().strip() if pd.notna(x) else "" for x in dfr.iloc[i].tolist()]
        if any(v == "LOC" for v in rowvals):
            header_idx = i
            break
    if header_idx is None:
        header_idx = 0

    h1 = dfr.iloc[header_idx].fillna("")
    h2 = dfr.iloc[header_idx+1].fillna("") if header_idx+1 < len(dfr) else dfr.iloc[header_idx].fillna("")

    loc_starts = [idx for idx,val in enumerate(h1) if str(val).strip().upper()=='LOC']
    if not loc_starts:
        loc_starts = [i for i,val in enumerate(h2) if str(val).strip()!=""]

    blocks = []
    for i, start in enumerate(loc_starts):
        end = loc_starts[i+1] if i+1 < len(loc_starts) else dfr.shape[1]
        blocks.append((start, end))

    records = []
    data_start = header_idx + 2

    def cell_val(row, c):
        if c < len(row):
            v = row.iloc[c]
            if pd.isna(v): return None
            return v
        return None

    def to_num(x):
        try:
            if x is None: return 0.0
            return float(str(x).replace(',',''))
        except:
            return 0.0

    for rid in range(data_start, dfr.shape[0]):
        row = dfr.iloc[rid]
        if row.isna().all(): continue
        for (s,e) in blocks:
            item_name = str(h2[s]).strip() if pd.notna(h2[s]) else ""
            loc = cell_val(row, s)
            remain_bag = cell_val(row, s+1)
            remain_kg = cell_val(row, s+2)
            in_bag = cell_val(row, s+3)
            in_kg = cell_val(row, s+4)
            out_bag = cell_val(row, s+5)
            out_kg = cell_val(row, s+6)
            bal_bag = cell_val(row, s+7)
            bal_kg = cell_val(row, s+8)
            avg = cell_val(row, s+9)
            input_date = cell_val(row, s+10)
            supplier = cell_val(row, s+12) if s+12 < dfr.shape[1] else None

            nums = [remain_kg, in_kg, out_kg, bal_kg]
            nums_clean = [to_num(x) for x in nums]
            has_data = (loc is not None and str(loc).strip()!="") or any(abs(n)>1e-9 for n in nums_clean)
            if has_data:
                try:
                    input_date_parsed = pd.to_datetime(input_date, errors='coerce')
                    input_date_str = str(input_date_parsed.date()) if not pd.isna(input_date_parsed) else str(input_date)
                except:
                    input_date_str = str(input_date)
                records.append({
                    "sheet": sheet_name,
                    "ten_nguyen_lieu": item_name,
                    "lo": loc,
                    "so_bao": remain_bag if remain_bag is not None else 0,
                    "so_kg": remain_kg if remain_kg is not None else 0,
                    "nhap_kg": in_kg if in_kg is not None else 0,
                    "xuat_kg": out_kg if out_kg is not None else 0,
                    "ton_cuoi_kg": bal_kg if bal_kg is not None else 0,
                    "tb_kg_moi_bao": avg if avg is not None else None,
                    "ncc": supplier,
                    "ngay_nhap": input_date_str
                })
    df_long = pd.DataFrame.from_records(records)
    if df_long.empty:
        return df_long
    df_long['ten_nguyen_lieu'] = df_long['ten_nguyen_lieu'].astype(str).apply(remove_accents).str.strip().str.upper()
    def compute_avg(r):
        try:
            sb = float(r.get('so_bao') or 0)
            sk = float(r.get('so_kg') or 0)
            if sb != 0:
                return abs(sk)/abs(sb)
            tb = r.get('tb_kg_moi_bao')
            if tb is not None and str(tb).strip()!='':
                return abs(float(tb))
        except:
            return None
        return None
    df_long['trung_binh'] = df_long.apply(compute_avg, axis=1)
    df_long['age'] = df_long['ngay_nhap'].apply(compute_age_from_date)
    # rename to match DB column names
    df_long = df_long.rename(columns={
        'so_bao':'so_bao',
        'so_kg':'so_kg',
        'ton_cuoi_kg':'ton_cuoi_kg',
        'tb_kg_moi_bao':'tb_kg_moi_bao'
    })
    return df_long

# ---------------------------
# Sidebar menu
# ---------------------------
st.sidebar.title("Menu")
page = st.sidebar.selectbox("Chon trang", [
    "Home",
    "Upload & Chuan hoa",
    "Nhap - Xuat",
    "Bao cao",
    "Phieu lo (PDF A5)",
    "Stream (Nhat ky)"
])

# ---------------------------
# Page Home (Dashboard)
# ---------------------------
if page == "Home":
    st.title("🏠 He thong quan ly ton kho - Home")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM inventory ORDER BY id DESC", conn)
    conn.close()
    if df.empty:
        st.info("Chua co du lieu. Vui long vao 'Upload & Chuan hoa' de nap file.")
    else:
        # KPIs
        tong_nguyen_lieu = df["ten_nguyen_lieu"].nunique()
        tong_lo = df["lo"].nunique()
        tong_kg = df["ton_cuoi_kg"].sum()
        tong_bao = df["so_bao"].sum()
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("So nguyen lieu", tong_nguyen_lieu)
        c2.metric("So lo", tong_lo)
        c3.metric("Tong khoi luong (kg)", f"{tong_kg:,.2f}")
        c4.metric("Tong so bao", int(tong_bao))
        st.markdown("---")
        # age groups
        st.subheader("Ton kho theo nhom tuoi")
        df['age'] = df['age'].fillna(0)
        a1 = df[(df['age']>=0)&(df['age']<=30)]['ton_cuoi_kg'].sum()
        a2 = df[(df['age']>=31)&(df['age']<=60)]['ton_cuoi_kg'].sum()
        a3 = df[(df['age']>=61)]['ton_cuoi_kg'].sum()
        total = a1 + a2 + a3
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        col_a1.metric("0-30 (kg)", f"{a1:,.2f}", f"{(a1/total*100):.1f}%" if total>0 else "")
        col_a2.metric("31-60 (kg)", f"{a2:,.2f}", f"{(a2/total*100):.1f}%" if total>0 else "")
        col_a3.metric(">61 (kg)", f"{a3:,.2f}", f"{(a3/total*100):.1f}%" if total>0 else "")
        col_a4.metric("Tong (kg)", f"{total:,.2f}")
        st.markdown("---")
        st.subheader("Top 10 nguyen lieu theo ton cuoi")
        top = df.groupby("ten_nguyen_lieu")['ton_cuoi_kg'].sum().reset_index().sort_values('ton_cuoi_kg', ascending=False).head(10)
        st.dataframe(top)
        st.markdown("---")
        st.subheader("Bang chi tiet (20 dong dau)")
        st.dataframe(df.head(20))

# ---------------------------
# Page Upload & Chuan hoa
# ---------------------------
if page == "Upload & Chuan hoa":
    st.title("📤 Upload & Chuan hoa")
    st.info("Upload file Excel (Check stock KI.xlsx). Chon sheet, parse va luu vao database.")
    uploaded = st.file_uploader("Chon file Excel", type=["xlsx","xls"])
    if uploaded:
        try:
            xls = pd.ExcelFile(uploaded)
            sheets = xls.sheet_names
            sheet = st.selectbox("Chon sheet de parse", sheets)
            raw = pd.read_excel(uploaded, sheet_name=sheet, header=None)
            st.subheader("Preview du lieu raw (20 dong dau)")
            st.dataframe(raw.head(20))
            if st.button("Thuc hien parse & chuan hoa"):
                with st.spinner("Dang parse..."):
                    df_parsed = parse_complex_sheet(raw, sheet_name=sheet)
                if df_parsed.empty:
                    st.error("Khong co ban ghi sau khi parse. Kiem tra sheet hoac file.")
                else:
                    st.success(f"Da parse duoc {len(df_parsed)} ban ghi")
                    st.subheader("Preview du lieu da chuan hoa")
                    st.dataframe(df_parsed.head(50))
                    # download cleaned excel
                    b = df_to_excel_bytes(df_parsed)
                    st.download_button("Tai file da chuan hoa (Excel)", data=b, file_name="cleaned_parsed.xlsx")
                    if st.button("Luu tat ca vao DB"):
                        conn = get_conn()
                        for _, r in df_parsed.iterrows():
                            conn.execute("""
                            INSERT INTO inventory (sheet, ten_nguyen_lieu, lo, so_bao, so_kg, nhap_kg, xuat_kg, ton_cuoi_kg, tb_kg_moi_bao, ncc, ngay_nhap, product_date, age, source)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                            """, (
                                r.get('sheet'),
                                r.get('ten_nguyen_lieu'),
                                r.get('lo'),
                                float(r.get('so_bao') or 0),
                                float(r.get('so_kg') or 0),
                                float(r.get('nhap_kg') or 0),
                                float(r.get('xuat_kg') or 0),
                                float(r.get('ton_cuoi_kg') or 0),
                                r.get('tb_kg_moi_bao'),
                                r.get('ncc'),
                                r.get('ngay_nhap'),
                                r.get('ngay_nhap'),
                                int(r.get('age') or 0),
                                "upload"
                            ))
                        conn.commit()
                        conn.close()
                        save_activity("import_excel", f"import {len(df_parsed)} rows from {sheet}")
                        st.success("Da luu vao DB thanh cong!")
                        st.experimental_rerun()
        except Exception as e:
            st.error(f"Loi khi doc file: {e}")

# ---------------------------
# Page Nhap - Xuat
# ---------------------------
if page == "Nhap - Xuat":
    st.title("📥 / 📤 Nhap - Xuat")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM inventory ORDER BY id DESC", conn)
    conn.close()
    materials = sorted(df['ten_nguyen_lieu'].dropna().unique().tolist()) if not df.empty else []
    mat = st.selectbox("Chon ten nguyen lieu (hoac nhap ten moi)", [""] + materials)
    st.markdown("---")
    st.subheader("Nhap / Xuat nhanh")
    mode = st.radio("Che do", ["Nhap", "Xuat"])
    lo = st.text_input("Ma lo")
    so_bao = st.number_input("So bao", value=0, step=1)
    so_kg = st.number_input("So kg", value=0.0, step=0.1)
    ngay_nhap = st.date_input("Ngay giao dich", value=date.today())
    ncc = st.text_input("NCC")
    if st.button("Thuc hien giao dich"):
        if not mat:
            st.error("Vui long chon hoac nhap ten nguyen lieu")
        else:
            sign = 1 if mode=="Nhap" else -1
            conn = get_conn()
            trung = (so_kg/so_bao) if so_bao>0 else None
            conn.execute("""
            INSERT INTO inventory (sheet, ten_nguyen_lieu, lo, so_bao, so_kg, nhap_kg, xuat_kg, ton_cuoi_kg, tb_kg_moi_bao, ncc, ngay_nhap, product_date, age, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                "manual",
                mat,
                lo,
                float(so_bao),
                float(sign*so_kg),
                float(so_kg) if mode=="Nhap" else 0,
                float(so_kg) if mode=="Xuat" else 0,
                float(sign*so_kg),
                trung,
                ncc,
                str(ngay_nhap),
                str(ngay_nhap),
                0,
                "manual"
            ))
            conn.commit()
            conn.close()
            save_activity("manual_tx", f"{mode} {so_kg}kg - {mat} - lo {lo}")
            st.success("Giao dich da duoc luu")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Lich su giao dich (20 dong)")
    conn = get_conn()
    df_tx = pd.read_sql_query("SELECT id, ts, user, action, details FROM activity_log ORDER BY id DESC LIMIT 20", conn)
    conn.close()
    if not df_tx.empty:
        st.dataframe(df_tx)

# ---------------------------
# Page Bao cao
# ---------------------------
if page == "Bao cao":
    st.title("📊 Bao cao va Xuat")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM inventory ORDER BY id DESC", conn)
    conn.close()
    if df.empty:
        st.info("Chua co du lieu de bao cao")
    else:
        ten = st.selectbox("Chon nguyen lieu (Tat ca de xuat toan bo)", ["Tat ca"] + sorted(df["ten_nguyen_lieu"].dropna().unique().tolist()))
        date_from = st.date_input("Tu ngay (bo trong neu khong loc)", value=None, key="r_from")
        date_to = st.date_input("Den ngay (bo trong neu khong loc)", value=None, key="r_to")
        dff = df.copy()
        if ten != "Tat ca":
            dff = dff[dff["ten_nguyen_lieu"]==ten]
        try:
            if date_from:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors='coerce').dt.date >= date_from]
            if date_to:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors='coerce').dt.date <= date_to]
        except:
            pass
        st.subheader("Kq loc")
        st.dataframe(dff.head(200))
        # xuat excel
        if st.button("Xuat Excel"):
            b = df_to_excel_bytes(dff)
            st.download_button("Tai Excel", data=b, file_name="baocao_tonkho.xlsx")
        # xuat pdf nhanh
        if st.button("Xuat PDF don gian"):
            if FPDF is None:
                st.error("FPDF chua duoc cai tren server")
            else:
                pdf = FPDF("L","mm","A4")
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(0,10,"Bao cao ton kho", ln=True)
                for i,row in dff.head(200).iterrows():
                    txt = f"{str(row.get('ten_nguyen_lieu',''))[:30]:30} | {str(row.get('lo','')):8} | {row.get('ton_cuoi_kg',0):10,.2f}"
                    pdf.cell(0,6,txt,ln=True)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    tmp_path = tmp.name
                data = open(tmp_path,"rb").read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="baocao.pdf">Tai PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

# ---------------------------
# Page Phieu lo (PDF A5)
# ---------------------------
if page == "Phieu lo (PDF A5)":
    st.title("📝 Phieu quan ly lo - PDF A5")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM inventory ORDER BY id DESC", conn)
    conn.close()
    if df.empty:
        st.info("Chua co du lieu")
    else:
        lots = sorted(df['lo'].dropna().unique().tolist())
        chosen = st.selectbox("Chon lo de in", [""] + lots)
        if chosen:
            df_l = df[df['lo']==chosen]
            st.dataframe(df_l)
            if st.button("Tao phieu PDF A5"):
                row = df_l.iloc[0]
                if FPDF is None:
                    st.error("FPDF chua duoc cai tren server")
                else:
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
                    line("Ten nguyen lieu", row.get('ten_nguyen_lieu',''))
                    line("Ma lo", row.get('lo',''))
                    line("Ngay nhap", row.get('ngay_nhap',''))
                    line("So bao", row.get('so_bao',''))
                    line("Khoi luong (kg)", row.get('so_kg',''))
                    line("Trung binh (kg/bao)", row.get('tb_kg_moi_bao',''))
                    line("NCC", row.get('ncc',''))
                    line("Tuoi (ngay)", row.get('age',''))
                    pdf.ln(6)
                    pdf.set_font("Arial","I",9)
                    pdf.cell(0,6,"In tu he thong quan ly ton kho", ln=True, align="C")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        tmp_path = tmp.name
                    data = open(tmp_path,"rb").read()
                    b64 = base64.b64encode(data).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="phieu_{chosen}.pdf">Tai phieu PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)

# ---------------------------
# Page Stream (Nhat ky)
# ---------------------------
if page == "Stream (Nhat ky)":
    st.title("🔔 Nhat ky hoat dong")
    conn = get_conn()
    df_log = pd.read_sql_query("SELECT * FROM activity_log ORDER BY id DESC LIMIT 500", conn)
    conn.close()
    if df_log.empty:
        st.info("Chua co hoat dong")
    else:
        st.dataframe(df_log)
        q = st.text_input("Loc theo action (nhap, xuat, import...)", "")
        if q:
            st.dataframe(df_log[df_log['action'].str.contains(q, case=False, na=False)])

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Version: 1.0")
st.sidebar.write("Author: ChatGPT")
