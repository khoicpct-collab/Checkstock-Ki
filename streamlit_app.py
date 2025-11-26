# streamlit_app.py
# He thong quan ly ton kho - Modules 1..9 + Home + Sidebar
# Tieng Viet KHONG DAU

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import os
import io
import tempfile
import base64

# Thu vien tuyen tinh (khong bat buoc)
try:
    import altair as alt
except Exception:
    alt = None

# QR libs
try:
    import qrcode
    from PIL import Image
except Exception:
    qrcode = None
    Image = None

# Try pyzbar for QR decode
try:
    from pyzbar.pyzbar import decode as zbar_decode
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False

# PDF lib
try:
    from fpdf import FPDF
except Exception:
    FPDF = None

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="He thong quan ly ton kho", layout="wide")
DB_PATH = "warehouse.db"

# -----------------------------
# Database init & helpers
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    # main table warehouse
    conn.execute("""
    CREATE TABLE IF NOT EXISTS warehouse (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ten_nguyen_lieu TEXT,
        lo TEXT,
        so_bao REAL,
        khoi_luong_kg REAL,
        trung_binh_kg REAL,
        don_vi TEXT,
        ngay_nhap TEXT,
        product_date TEXT,
        age INTEGER,
        ncc TEXT,
        code_ncc TEXT,
        truck TEXT,
        vendor TEXT
    )
    """)
    # activity log
    conn.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        user TEXT,
        action TEXT,
        details TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(show_spinner=False)
def read_warehouse_df():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM warehouse", conn)
    conn.close()
    return df

def save_activity(action, details="", user="system"):
    conn = get_conn()
    ts = datetime.now().isoformat(sep=' ', timespec='seconds')
    conn.execute("INSERT INTO activity_log (ts, user, action, details) VALUES (?,?,?,?)",
                 (ts, user, action, details))
    conn.commit()
    conn.close()

# -----------------------------
# Utility functions
# -----------------------------
def remove_accents(s):
    import unicodedata
    if pd.isna(s):
        return ""
    s2 = str(s)
    s2 = unicodedata.normalize('NFKD', s2)
    s2 = "".join([c for c in s2 if not unicodedata.combining(c)])
    return s2

def compute_age_from_date(d):
    try:
        dt = pd.to_datetime(d, errors='coerce')
        if pd.isna(dt):
            return None
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

# -----------------------------
# UI: Sidebar navigation
# -----------------------------
st.sidebar.title("Menu")
page = st.sidebar.selectbox("Chon trang",
    ["Home",
     "Upload & Chuan hoa (Module1)",
     "Nhap lieu (Module2)",
     "Luu DB / Module3",
     "Dashboard (Module4)",
     "AI Reorder (Module5)",
     "Xuat phieu lo (Module6)",
     "Mobile (Module7)",
     "QR (Module8)",
     "Bao cao (Module9)",
     "Stream (Live Feed)"
    ])

# -----------------------------
# Home page
# -----------------------------
if page == "Home":
    st.title("He thong quan ly ton kho - Home")
    df = read_warehouse_df()
    if df.empty:
        st.info("Chua co du lieu. Vui long vao 'Upload & Chuan hoa' de nap file.")
    else:
        tong_nguyen_lieu = df["ten_nguyen_lieu"].nunique()
        tong_lo = df["lo"].nunique()
        tong_kg = df["khoi_luong_kg"].sum()
        tong_bao = df["so_bao"].sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("So nguyen lieu", tong_nguyen_lieu)
        col2.metric("So lo", tong_lo)
        col3.metric("Tong khoi luong (kg)", f"{tong_kg:,.2f}")
        col4.metric("Tong so bao", f"{int(tong_bao)}")
        st.markdown("---")
        # small dashboard charts if altair available
        try:
            if alt is not None:
                st.subheader("Top 10 nguyen lieu (theo kg)")
                top = df.groupby("ten_nguyen_lieu")["khoi_luong_kg"].sum().reset_index().sort_values("khoi_luong_kg", ascending=False).head(10)
                chart = alt.Chart(top).mark_bar().encode(x='ten_nguyen_lieu', y='khoi_luong_kg', tooltip=['ten_nguyen_lieu','khoi_luong_kg']).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        except Exception:
            pass

# -----------------------------
# Module 1: Upload & preview & chuan hoa
# -----------------------------
if page == "Upload & Chuan hoa (Module1)":
    st.title("Module 1 - Upload & Chuan hoa")
    st.write("Tai file Excel (layout phuc tap) - he thong se thuong dong chuan hoa")
    uploaded = st.file_uploader("Chon file Excel", type=["xlsx","xls"])
    if uploaded:
        # read all sheets names
        xls = pd.ExcelFile(uploaded)
        sheets = xls.sheet_names
        st.write("Phat hien sheets:", sheets)
        choose = st.selectbox("Chon sheet de preview", sheets)
        df_raw = pd.read_excel(uploaded, sheet_name=choose, header=None)
        st.subheader("Preview 50 dong dau (raw)")
        st.dataframe(df_raw.head(50))
        st.markdown("**Tu file raw se thuc hien parse sang dang long format va chuan hoa**")
        if st.button("Thuc hien chuan hoa tu sheet hien tai"):
            # attempt parse similar logic we used offline
            # heuristics: find header row where 'LOC' appears
            dfr = df_raw.copy()
            header_idx = None
            for i in range(0, min(12, len(dfr))):
                rowvals = [str(x).upper().strip() if pd.notna(x) else "" for x in dfr.iloc[i].tolist()]
                if any(v == "LOC" for v in rowvals):
                    header_idx = i
                    break
            if header_idx is None:
                st.error("Khong tim thay dong header co 'LOC'. Vui long chon dung sheet hoac gui file khac.")
            else:
                st.info(f"Tim header o dong index {header_idx}. Bat dau parse...")
                # perform parsing: use same heuristics as offline
                h1 = dfr.iloc[header_idx].fillna("")
                h2 = dfr.iloc[header_idx+1].fillna("")
                loc_starts = [idx for idx,val in enumerate(h1) if str(val).strip().upper()=='LOC']
                blocks = []
                for i, start in enumerate(loc_starts):
                    end = loc_starts[i+1] if i+1 < len(loc_starts) else dfr.shape[1]
                    blocks.append((start,end))
                records = []
                data_start = header_idx+2
                for rid in range(data_start, dfr.shape[0]):
                    row = dfr.iloc[rid]
                    if row.isna().all():
                        continue
                    for (s,e) in blocks:
                        item_name = str(h2[s]).strip() if pd.notna(h2[s]) else ""
                        def cell(c):
                            if c < dfr.shape[1]:
                                val = row.iloc[c]
                                if pd.isna(val): return None
                                return val
                            return None
                        loc = cell(s)
                        remain_bag = cell(s+1)
                        remain_kg = cell(s+2)
                        in_bag = cell(s+3)
                        in_kg = cell(s+4)
                        out_bag = cell(s+5)
                        out_kg = cell(s+6)
                        bal_bag = cell(s+7)
                        bal_kg = cell(s+8)
                        avg = cell(s+9)
                        input_date = cell(s+10)
                        supplier = cell(s+12) if s+12 < dfr.shape[1] else None
                        # numeric cleaner
                        def to_num(x):
                            try:
                                if x is None: return 0.0
                                return float(str(x).replace(',',''))
                            except:
                                return 0.0
                        nums = [remain_kg, in_kg, out_kg, bal_kg]
                        nums_clean = [to_num(x) for x in nums]
                        has_data = (loc is not None and str(loc).strip()!="") or any(abs(n)>1e-9 for n in nums_clean)
                        if has_data:
                            records.append({
                                "sheet": choose,
                                "item_raw": item_name,
                                "ten_nguyen_lieu": item_name,
                                "vi_tri": loc,
                                "so_bao": remain_bag,
                                "khoi_luong_kg": remain_kg,
                                "nhap_bao": in_bag,
                                "nhap_kg": in_kg,
                                "xuat_bao": out_bag,
                                "xuat_kg": out_kg,
                                "ton_cuoi_bao": bal_bag,
                                "ton_cuoi_kg": bal_kg,
                                "tb_kg_moi_bao": avg,
                                "ncc": supplier,
                                "ngay_nhap": input_date
                            })
                if len(records) == 0:
                    st.error("Khong tao duoc ban ghi. Kiem tra lai sheet.")
                else:
                    df_parsed = pd.DataFrame.from_records(records)
                    st.success(f"Da parse duoc {len(df_parsed)} ban ghi")
                    st.dataframe(df_parsed.head(50))
                    # try clean: infer loai_bao, avg, age
                    df_parsed['material_name'] = df_parsed['ten_nguyen_lieu'].astype(str).apply(remove_accents).str.strip().str.upper()
                    # infer loai_bao & avg
                    def infer(row):
                        name = row['material_name']
                        avg_v = row.get('tb_kg_moi_bao', None)
                        # try to parse numeric avg
                        try:
                            if pd.notna(avg_v) and float(avg_v) != 0:
                                w = abs(float(avg_v))
                                loai = 'bigbag' if w>=100 else 'bao'
                                return loai, w
                        except:
                            pass
                        import re
                        m = re.search(r'(\d{2,4})\s*(KG)?', str(name))
                        if m:
                            val = float(m.group(1))
                            loai = 'bigbag' if val>=100 else 'bao'
                            return loai, val
                        # detect xa or chat_long keywords
                        if any(k in name for k in ['XA','XÁ','DAU','OIL','SAUCE','FISH','PASTE','NUOC']):
                            if 'XA' in name or 'X A' in name:
                                return 'xa', None
                            return 'chat_long', None
                        return 'bao', None
                    recs = []
                    for _,r in df_parsed.iterrows():
                        loai, w = infer(r)
                        age = compute_age_from_date(r.get('ngay_nhap'))
                        recs.append({
                            "ten_nguyen_lieu": r.get('ten_nguyen_lieu'),
                            "lo": r.get('vi_tri'),
                            "so_bao": r.get('so_bao') if r.get('so_bao') is not None else 0,
                            "khoi_luong_kg": r.get('khoi_luong_kg') if r.get('khoi_luong_kg') is not None else 0,
                            "trung_binh_kg": w,
                            "don_vi": "kg",
                            "ngay_nhap": str(r.get('ngay_nhap')),
                            "product_date": str(r.get('ngay_nhap')),
                            "age": age,
                            "ncc": r.get('ncc')
                        })
                    df_clean = pd.DataFrame.from_records(recs)
                    st.subheader("Preview du lieu da chuan hoa (20 dong)")
                    st.dataframe(df_clean.head(20))
                    # allow user to download or save
                    b = df_to_excel_bytes(df_clean)
                    st.download_button("Tai Excel da chuan hoa", data=b, file_name="cleaned_preview.xlsx")
                    if st.button("Luu vao DB (append)"):
                        conn = get_conn()
                        df_clean.to_sql("warehouse", conn, if_exists="append", index=False)
                        conn.close()
                        save_activity("import_excel", f"import {len(df_clean)} rows from {choose}")
                        st.success("Luu thanh cong vao DB")
                        st.experimental_rerun()

# -----------------------------
# Module 2: Nhap lieu theo nguyen lieu
# -----------------------------
if page == "Nhap lieu (Module2)":
    st.title("Module 2 - Nhap lieu theo ten nguyen lieu")
    df_all = read_warehouse_df()
    materials = sorted(df_all["ten_nguyen_lieu"].dropna().unique().tolist()) if not df_all.empty else []
    mat = st.selectbox("Chon nguyen lieu (hoac go de tim)", [""] + materials)
    if mat:
        st.subheader(f"Cac lo hien co cua {mat}")
        df_mat = df_all[df_all["ten_nguyen_lieu"] == mat]
        st.dataframe(df_mat)
        st.markdown("---")
        st.subheader("Nhap them / Cap nhat")
        lo = st.text_input("Ma lo (nhap lo neu tao lo moi)")
        so_bao = st.number_input("So bao", value=0, step=1)
        so_kg = st.number_input("So kg", value=0.0, step=0.1)
        ngay_nhap = st.date_input("Ngay nhap", value=date.today())
        ngay_sx = st.date_input("Ngay san xuat", value=date.today())
        ncc = st.text_input("NCC")
        code_ncc = st.text_input("Code NCC")
        if st.button("Luu nhap moi"):
            age = compute_age_from_date(ngay_nhap)
            new = pd.DataFrame([{
                "ten_nguyen_lieu": mat,
                "lo": lo,
                "so_bao": so_bao,
                "khoi_luong_kg": so_kg,
                "trung_binh_kg": (so_kg/so_bao) if so_bao>0 else None,
                "don_vi": "kg",
                "ngay_nhap": str(ngay_nhap),
                "product_date": str(ngay_sx),
                "age": age,
                "ncc": ncc,
                "code_ncc": code_ncc
            }])
            conn = get_conn()
            new.to_sql("warehouse", conn, if_exists="append", index=False)
            conn.close()
            save_activity("nhap_moi", f"{mat} lo {lo} so_kg {so_kg}")
            st.success("Da luu nhap moi")
            st.experimental_rerun()

# -----------------------------
# Module 3: Luu DB / chuc nang them
# (Basic admin & xem toan bo)
# -----------------------------
if page == "Luu DB / Module3":
    st.title("Module 3 - Quan ly DB")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM warehouse ORDER BY ngay_nhap DESC", conn)
    st.dataframe(df.head(200))
    st.markdown("---")
    if st.button("Xoa tat ca du lieu (CANH BAO)"):
        conn.execute("DELETE FROM warehouse")
        conn.commit()
        conn.close()
        save_activity("delete_all", "delete all warehouse")
        st.success("Da xoa toan bo du lieu")
        st.experimental_rerun()
    # export full db
    if st.button("Xuat Excel toan bo"):
        b = df_to_excel_bytes(df)
        st.download_button("Tai file Excel", data=b, file_name="warehouse_full.xlsx")

# -----------------------------
# Module 4: Dashboard
# -----------------------------
if page == "Dashboard (Module4)":
    st.title("Module 4 - Dashboard thong ke")
    df = read_warehouse_df()
    if df.empty:
        st.info("Chua co du lieu")
    else:
        # summary
        tong_nguyen_lieu = df["ten_nguyen_lieu"].nunique()
        tong_lo = df["lo"].nunique()
        tong_kg = df["khoi_luong_kg"].sum()
        tong_bao = int(df["so_bao"].sum())
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Nguyen lieu", tong_nguyen_lieu)
        c2.metric("Lo", tong_lo)
        c3.metric("Tong kg", f"{tong_kg:,.2f}")
        c4.metric("Tong bao", f"{tong_bao}")
        st.markdown("---")
        # bar chart top
        try:
            top = df.groupby("ten_nguyen_lieu")["khoi_luong_kg"].sum().reset_index().sort_values("khoi_luong_kg", ascending=False).head(15)
            if alt is not None:
                ch = alt.Chart(top).mark_bar().encode(x='ten_nguyen_lieu', y='khoi_luong_kg', tooltip=['ten_nguyen_lieu','khoi_luong_kg']).properties(height=400)
                st.altair_chart(ch, use_container_width=True)
        except Exception:
            pass
        st.markdown("---")
        # age alert
        st.subheader("Canh bao lo qua han (Age > 60)")
        df_alert = df[df["age"].fillna(0) > 60]
        if df_alert.empty:
            st.success("Khong co lo qua han")
        else:
            st.dataframe(df_alert)

# -----------------------------
# Module 5: AI Reorder
# -----------------------------
if page == "AI Reorder (Module5)":
    st.title("Module 5 - AI goi y dat hang")
    df = read_warehouse_df()
    if df.empty:
        st.info("Chua co du lieu de phan tich")
    else:
        df['ngay_nhap'] = pd.to_datetime(df['ngay_nhap'], errors='coerce')
        lead_time = st.number_input("Lead time (ngay)", min_value=1, max_value=120, value=7)
        forecast_days = st.number_input("So ngay du bao", min_value=7, max_value=365, value=30)
        # compute naive daily usage per material by summing negative changes (xuats)
        df_sorted = df.sort_values(['ten_nguyen_lieu','ngay_nhap'])
        df_sorted['khoi_luong_kg_shift'] = df_sorted.groupby('ten_nguyen_lieu')['khoi_luong_kg'].shift(-1)
        df_sorted['xuat_tinh'] = (df_sorted['khoi_luong_kg'] - df_sorted['khoi_luong_kg_shift']).apply(lambda x: x if x>0 else 0)
        daily_usage = df_sorted.groupby('ten_nguyen_lieu')['xuat_tinh'].mean().reset_index().rename(columns={'xuat_tinh':'daily_usage'})
        ton = df.groupby('ten_nguyen_lieu')['khoi_luong_kg'].sum().reset_index().rename(columns={'khoi_luong_kg':'ton_cuoi'})
        result = ton.merge(daily_usage, on='ten_nguyen_lieu', how='left')
        result['daily_usage'] = result['daily_usage'].fillna(0.01)
        result['remaining_days'] = result['ton_cuoi'] / result['daily_usage']
        result['reorder_qty'] = (result['daily_usage'] * forecast_days - result['ton_cuoi']).apply(lambda x: x if x>0 else 0)
        def warn_level(x):
            if x < lead_time:
                return "DAT NGAY"
            elif x < lead_time*1.5:
                return "THEO DOI"
            else:
                return "AN TOAN"
        result['status'] = result['remaining_days'].apply(warn_level)
        st.dataframe(result.sort_values('remaining_days'))
        st.markdown("---")
        st.subheader("Nguyen lieu can dat ngay")
        st.dataframe(result[result['status']=="DAT NGAY"])

# -----------------------------
# Module 6: Xuat phieu lo (PDF A5)
# -----------------------------
if page == "Xuat phieu lo (Module6)":
    st.title("Module 6 - Xuat phieu lo (PDF A5)")
    df = read_warehouse_df()
    if df.empty:
        st.info("Chua co du lieu")
    else:
        lots = sorted(df['lo'].dropna().unique().tolist())
        chosen = st.selectbox("Chon lo", [""] + lots)
        if chosen:
            df_l = df[df['lo']==chosen]
            st.dataframe(df_l)
            if st.button("Tao PDF (A5)"):
                # use FPDF if available, else provide simple CSV
                row = df_l.iloc[0]
                if FPDF is None:
                    st.warning("FPDF chua duoc cai tren server. Xuat CSV thay the.")
                    b = df_to_excel_bytes(df_l)
                    st.download_button("Tai CSV", data=b, file_name=f"phieu_{chosen}.xlsx")
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
                        pdf.cell(40,6,str(k)+":")
                        pdf.set_font("Arial","",10)
                        pdf.multi_cell(0,6,str(v))
                    line("Ten nguyen lieu", row.get('ten_nguyen_lieu',''))
                    line("Ma lo", row.get('lo',''))
                    line("Ngay nhap", row.get('ngay_nhap',''))
                    line("So bao", row.get('so_bao',''))
                    line("Khoi luong (kg)", row.get('khoi_luong_kg',''))
                    line("Trung binh (kg/bao)", row.get('trung_binh_kg',''))
                    line("NCC/Code", f"{row.get('ncc','')} / {row.get('code_ncc','')}")
                    line("Tuoi (ngay)", row.get('age',''))
                    # save temp
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf.output(tmp.name)
                        tmp_path = tmp.name
                    with open(tmp_path,"rb") as f:
                        data = f.read()
                    b64 = base64.b64encode(data).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="phieu_{chosen}.pdf">Tai phieu PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)

# -----------------------------
# Module 7: Mobile UI
# -----------------------------
if page == "Mobile (Module7)":
    st.title("Module 7 - Mobile (giao dien rut gon)")
    df = read_warehouse_df()
    if df.empty:
        st.info("Chua co du lieu")
    else:
        q = st.text_input("Tim nguyen lieu (go ten hoac chon)", "")
        if q.strip()=="":
            tmp = df.groupby("ten_nguyen_lieu")[["khoi_luong_kg","so_bao"]].sum().reset_index()
        else:
            tmp = df[df["ten_nguyen_lieu"].str.contains(q.upper(), na=False)].groupby("ten_nguyen_lieu")[["khoi_luong_kg","so_bao"]].sum().reset_index()
        for i,row in tmp.iterrows():
            cols = st.columns([4,1])
            with cols[0]:
                st.markdown(f"**{row['ten_nguyen_lieu']}**")
                st.write(f"Kg: {row['khoi_luong_kg']:.2f}  •  Bao: {int(row['so_bao']) if not pd.isna(row['so_bao']) else 0}")
            with cols[1]:
                if st.button("Mo", key=f"open_{i}"):
                    st.session_state['mobile_selected'] = row['ten_nguyen_lieu']
        if 'mobile_selected' in st.session_state:
            st.info(f"Da chon: {st.session_state['mobile_selected']}")
            mode = st.selectbox("Che do", ["Nhap nhanh","Xuat nhanh"])
            sb = st.number_input("So bao", value=0, step=1, key="m_sb")
            sk = st.number_input("So kg", value=0.0, step=0.1, key="m_sk")
            ngay = st.date_input("Ngay", date.today(), key="m_date")
            if st.button("Thuc hien", key="m_do"):
                new = pd.DataFrame([{
                    "ten_nguyen_lieu": st.session_state['mobile_selected'],
                    "lo": "mobile",
                    "so_bao": sb,
                    "khoi_luong_kg": sk if mode=="Nhap nhanh" else -sk,
                    "trung_binh_kg": (sk/sb) if sb>0 else sk,
                    "don_vi": "kg",
                    "ngay_nhap": str(ngay),
                    "product_date": str(ngay),
                    "age": 0
                }])
                conn = get_conn()
                new.to_sql("warehouse", conn, if_exists="append", index=False)
                conn.close()
                save_activity("mobile_tx", f"{mode} {sb} bao {sk}kg")
                st.success("Thuc hien thanh cong")

# -----------------------------
# Module 8: QR generate & scan
# -----------------------------
if page == "QR (Module8)":
    st.title("Module 8 - QR tao & quet")
    df = read_warehouse_df()
    lots = sorted(df['lo'].dropna().unique().tolist()) if not df.empty else []
    if not lots:
        st.info("Chua co lo")
    else:
        chosen = st.selectbox("Chon lo de tao QR", [""] + lots)
        if chosen:
            if qrcode is None:
                st.warning("Lib qrcode chua duoc cai. Khong the tao QR.")
            else:
                if st.button("Tao QR"):
                    data = f"LOT:{chosen}"
                    img = qrcode.make(data)
                    st.image(img, caption=f"QR {chosen}", use_column_width=False)
                    tmpfn = f"qr_{chosen}.png"
                    img.save(tmpfn)
                    with open(tmpfn,"rb") as f:
                        st.download_button("Tai QR", data=f, file_name=tmpfn, mime="image/png")
        st.markdown("---")
        st.subheader("Quet QR (upload anh)")
        uploaded_img = st.file_uploader("Upload anh chua QR", type=["png","jpg","jpeg"])
        if uploaded_img:
            try:
                img = Image.open(uploaded_img)
                st.image(img, caption="Anh upload")
            except Exception:
                st.write("Khong the hien thi anh")
            decoded = None
            if HAS_PYZBAR:
                try:
                    codes = zbar_decode(img)
                    if codes:
                        decoded = codes[0].data.decode('utf-8')
                except Exception:
                    decoded = None
            if decoded:
                st.success(f"Phat hien ma: {decoded}")
                if decoded.startswith("LOT:"):
                    lotcode = decoded.split("LOT:")[1]
                    conn = get_conn()
                    df_l = pd.read_sql_query("SELECT * FROM warehouse WHERE lo=?", conn, params=[lotcode])
                    conn.close()
                    st.dataframe(df_l)
            else:
                st.info("Khong the doc QR tu anh. Ban co the nhap ma lo tay")
                manual = st.text_input("Nhap ma lo")
                if manual:
                    conn = get_conn()
                    df_l = pd.read_sql_query("SELECT * FROM warehouse WHERE lo=?", conn, params=[manual])
                    conn.close()
                    st.dataframe(df_l)

# -----------------------------
# Module 9: Bao cao & export
# -----------------------------
if page == "Bao cao (Module9)":
    st.title("Module 9 - Xuat bao cao")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM warehouse", conn)
    conn.close()
    if df.empty:
        st.info("Chua co du lieu")
    else:
        ten = st.selectbox("Chon nguyen lieu (Tat ca de xuat toan bo)", ["Tat ca"] + sorted(df["ten_nguyen_lieu"].unique().tolist()))
        date_from = st.date_input("Tu ngay", value=None, key="r1")
        date_to = st.date_input("Den ngay", value=None, key="r2")
        dff = df.copy()
        if ten != "Tat ca":
            dff = dff[dff["ten_nguyen_lieu"] == ten]
        try:
            if date_from:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors='coerce').dt.date >= date_from]
            if date_to:
                dff = dff[pd.to_datetime(dff["ngay_nhap"], errors='coerce').dt.date <= date_to]
        except Exception:
            pass
        st.dataframe(dff.head(200))
        if st.button("Xuat Excel"):
            b = df_to_excel_bytes(dff)
            st.download_button("Tai Excel", data=b, file_name="baocao_tonkho.xlsx")
        if st.button("Xuat PDF don gian"):
            if FPDF is None:
                st.warning("FPDF khong duoc cai")
            else:
                pdf = FPDF("L","mm","A4")
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(0,10,"Bao cao ton kho", ln=True)
                for i,row in dff.head(50).iterrows():
                    line = f"{str(row.get('ten_nguyen_lieu',''))[:30]:30} | {str(row.get('lo','')):8} | {row.get('khoi_luong_kg',0):10,.2f}"
                    pdf.cell(0,6,line,ln=True)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    tmp_path = tmp.name
                with open(tmp_path,"rb") as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="baocao.pdf">Tai PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

# -----------------------------
# Stream (Live feed) page
# -----------------------------
if page == "Stream (Live Feed)":
    st.title("Stream - Nhat ky hoat dong (live feed)")
    conn = get_conn()
    df_act = pd.read_sql_query("SELECT * FROM activity_log ORDER BY ts DESC LIMIT 200", conn)
    conn.close()
    if df_act.empty:
        st.info("Chua co hoat dong nao")
    else:
        st.dataframe(df_act)
        st.markdown("---")
        st.write("Ban co the loc theo action hoac user")
        q_action = st.text_input("Loc theo action (nhap, xuat, import...)", "")
        if q_action:
            df_f = df_act[df_act["action"].str.contains(q_action, na=False, case=False)]
            st.dataframe(df_f)

# Footer
st.sidebar.markdown("---")
st.sidebar.write("Version: 1.0")
st.sidebar.write("Author: ChatGPT (build for you)")
