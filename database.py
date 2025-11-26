import sqlite3

def get_conn():
    return sqlite3.connect("inventory.db", check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ngay DATE,
        nguyen_lieu TEXT,
        lo TEXT,
        so_bao INTEGER,
        so_kg REAL,
        trung_binh REAL,
        remain_kg REAL,
        nhap_kg REAL,
        xuat_kg REAL,
        ton_cuoi_kg REAL,
        ncc TEXT,
        product_date DATE,
        formula_date DATE,
        age INTEGER
    );
    """)

    conn.commit()
    conn.close()
