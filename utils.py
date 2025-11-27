import pandas as pd

def clean_inventory_dataframe(df):
    df = df.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "_")
        .str.lower()
    )

    # Chuẩn hoá cột ngày (nếu có)
    if "ngay_nhap" in df.columns:
        df["ngay_nhap"] = pd.to_datetime(df["ngay_nhap"], errors="coerce")
        df["age"] = (pd.Timestamp.today() - df["ngay_nhap"]).dt.days

    return df
