import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# -----------------------------
# Module 3: CHUẨN HOÁ + LƯU DB
# -----------------------------

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá các cột theo đúng format B bạn yêu cầu."""

    df = df.copy()

    # Strip khoảng trắng
    df.columns = [c.strip() for c in df.columns]

    # Ví dụ chuẩn hóa: các cột nguyên liệu không có đơn vị LIT
    if 'don_vi' in df.columns:
        df['don_vi'] = df['don_vi'].str.replace('lit', '', regex=False)
        df['don_vi'] = df['don_vi'].str.strip()

    # Chuyển chất lỏng & nguyên liệu xá về kg nếu cần
    if 'so_luong' in df.columns:
        df['so_luong'] = df['so_luong'].astype(float)

    return df


def save_to_sqlite(df: pd.DataFrame, table_name: str = 'nguyen_lieu'):
    db_path = Path('data.db')
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()


st.header("Module 3 — Chuẩn hoá & Lưu dữ liệu vào Database")

uploaded_file = st.file_uploader("Tải file Excel sau Module 1 / Module 2", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Dữ liệu gốc:")
    st.dataframe(df)

    # Chuẩn hoá
    df_norm = normalize_dataframe(df)
    st.subheader("Dữ liệu đã chuẩn hoá:")
    st.dataframe(df_norm)

    # Save
    if st.button("Lưu vào SQLite DB"):
        save_to_sqlite(df_norm)
        st.success("Đã lưu thành công vào data.db")
