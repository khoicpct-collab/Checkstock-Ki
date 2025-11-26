import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# -----------------------------
# CSS giao dien chuyen nghiep
# -----------------------------
st.markdown("""
<style>

html, body, [class*="css"]  { font-family: 'Segoe UI', sans-serif; }

.sidebar .sidebar-content {
    background: #1f2a44 !important;
    color: white !important;
}

.stButton>button {
    background-color:#2e86de;
    color:white;
    border-radius:8px;
    padding:8px 20px;
    font-size:16px;
}

.stButton>button:hover {
    background-color:#1b4f72;
}

.block-container { padding-top: 2rem; }

.dataframe {
    background:white;
    border-radius:8px;
    padding:10px;
}

h1,h2,h3 { color:#1f2a44; font-weight:650; }

</style>
""", unsafe_allow_html=True)

# -----------------------------
# KET NOI DATABASE SQLITE
# -----------------------------
def get_conn():
    return sqlite3.connect("inventory.db", check_same_thread=False)

conn = get_conn()

# Tao bang neu chua co
conn.execute("""
CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ngay TEXT,
    ten_nguyen_lieu TEXT,
    lo TEXT,
    so_bao REAL,
    so_kg REAL,
    remain_bao REAL,
    remain_kg REAL,
    nhap_bao REAL,
    nhap_kg REAL,
    xuat_bao REAL,
    xuat_kg REAL,
    ton_cuoi_bao REAL,
    ton_cuoi_kg REAL,
    age INTEGER,
    code TEXT,
    product_date TEXT
)
""")

conn.commit()


# -----------------------------
# CAC MODULE (SHELL)
# -----------------------------
def page_home():
    st.title("🏠 Hệ thống quản lý tồn kho – Dashboard")
    st.info("Trang này sẽ hiển thị KPI, tồn kho theo nhóm tuổi, biểu đồ, tổng hợp.")
    st.warning("⛔ Chưa có dữ liệu hoặc đang trong bước xây dựng Module 4–7.")


def page_upload():
    st.title("📤 Upload & Chuẩn hoá dữ liệu")
    st.info("Module này sẽ cho phép bạn upload file Excel, chuẩn hoá và lưu vào SQLite.")
    
    uploaded = st.file_uploader("Tải file Excel", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded, sheet_name=None)
        st.success("Đã tải file thành công!")
        st.write("📄 Các sheet tìm thấy:", list(df.keys()))

        if st.checkbox("Xem trước 20 dòng đầu của sheet đầu tiên"):
            first_sheet = list(df.keys())[0]
            st.dataframe(df[first_sheet].head(20))


def page_nhap_xuat():
    st.title("📥📤 Nhập – Xuất kho")
    st.info("Module để nhập thêm, xuất, tính tồn cuối.")
    st.warning("⛔ Module đang được xây tiếp trong Version 2.")


def page_report():
    st.title("📊 Báo cáo – Tra cứu tồn kho")
    st.info("Lọc dữ liệu, xem tồn theo nhóm tuổi, xuất Excel/PDF.")
    st.warning("⛔ Module đang được xây tiếp trong Version 3–4.")


# -----------------------------
# MENU DA TRANG
# -----------------------------
menu = st.sidebar.radio(
    "Điều hướng",
    [
        "Home",
        "Upload & Chuẩn hoá",
        "Nhập – Xuất kho",
        "Báo cáo tồn kho"
    ]
)

if menu == "Home":
    page_home()
elif menu == "Upload & Chuẩn hoá":
    page_upload()
elif menu == "Nhập – Xuất kho":
    page_nhap_xuat()
elif menu == "Báo cáo tồn kho":
    page_report()
