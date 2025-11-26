import pandas as pd
from datetime import datetime

def clean_excel(df):
    df = df.rename(columns=lambda x: x.strip())
    df = df.loc[:, df.columns.notna()]

    # Chuyển ngày
    for c in ["product_date", "formula_date", "Ngay"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Tính age = Today – Ngay nhập
    today = pd.Timestamp.today()
    if "Ngay" in df.columns:
        df["age"] = (today - df["Ngay"]).dt.days

    # Trung bình = kg / bao
    if "so_kg" in df.columns and "so_bao" in df.columns:
        df["trung_binh"] = df.apply(
            lambda r: r["so_kg"]/r["so_bao"] if (r["so_bao"] and r["so_bao"]>0) else None,
            axis=1
        )

    return df
