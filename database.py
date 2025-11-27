import sqlite3
import pandas as pd

DB = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay_nhap TEXT,
            ten_nguyen_lieu TEXT,
            lo TEXT,
            so_bao REAL,
            khoiluong REAL,
            age INTEGER
        )
    """)
    conn.close()

def save_dataframe(df, table):
    conn = sqlite3.connect(DB)
    df.to_sql(table, conn, if_exists="replace", index=False)
    conn.close()

def load_table(table):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    conn.close()
    return df
