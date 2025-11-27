import pandas as pd
from datetime import datetime

def calculate_inventory_fields(df):
    """
    Tính toán các trường tự động cho dữ liệu tồn kho
    """
    df_calc = df.copy()
    
    # Đảm bảo các cột số là kiểu số
    numeric_cols = ['Tồn đầu (Bag)', 'Tồn đầu (Weight)', 'Nhập (Bag)', 'Nhập (Weight)', 
                   'Sử dụng (Bag)', 'Sử dụng (Weight)']
    
    for col in numeric_cols:
        if col in df_calc.columns:
            df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)
    
    # Tính tồn cuối
    if all(col in df_calc.columns for col in ['Tồn đầu (Bag)', 'Nhập (Bag)', 'Sử dụng (Bag)']):
        df_calc['Tồn cuối (Bag)'] = df_calc['Tồn đầu (Bag)'] + df_calc['Nhập (Bag)'] - df_calc['Sử dụng (Bag)']
    
    if all(col in df_calc.columns for col in ['Tồn đầu (Weight)', 'Nhập (Weight)', 'Sử dụng (Weight)']):
        df_calc['Tồn cuối (Weight)'] = df_calc['Tồn đầu (Weight)'] + df_calc['Nhập (Weight)'] - df_calc['Sử dụng (Weight)']
    
    # Tính trung bình
    if all(col in df_calc.columns for col in ['Tồn cuối (Bag)', 'Tồn cuối (Weight)']):
        df_calc['Trung bình'] = df_calc.apply(
            lambda x: x['Tồn cuối (Weight)'] / x['Tồn cuối (Bag)'] if x['Tồn cuối (Bag)'] > 0 else 0, 
            axis=1
        ).round(2)
    
    # Tính tuổi lưu kho
    if 'Ngày nhập' in df_calc.columns:
        df_calc['Ngày nhập'] = pd.to_datetime(df_calc['Ngày nhập'], errors='coerce')
        df_calc['Tuổi lưu kho'] = (datetime.now() - df_calc['Ngày nhập']).dt.days
    
    return df_calc

def calculate_totals(df):
    """
    Tính tổng cho các cột số
    """
    numeric_cols = ['Tồn đầu (Bag)', 'Tồn đầu (Weight)', 'Nhập (Bag)', 'Nhập (Weight)',
                   'Sử dụng (Bag)', 'Sử dụng (Weight)', 'Tồn cuối (Bag)', 'Tồn cuối (Weight)']
    
    totals = {}
    for col in numeric_cols:
        if col in df.columns:
            totals[col] = df[col].sum()
    
    return totals
