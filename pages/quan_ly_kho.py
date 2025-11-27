import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Thêm path để import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.materials import MATERIALS
from data.locks import LOCKS
from utils.calculations import calculate_inventory_fields, calculate_totals

def main():
    st.set_page_config(page_title="Quản lý Kho - Checkstock", layout="wide")
    
    st.title("📦 QUẢN LÝ KHO NGUYÊN LIỆU")
    
    # Khởi tạo session state
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = pd.DataFrame()
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    # Sidebar cho các chức năng
    st.sidebar.header("🎯 Chức năng")
    function_option = st.sidebar.radio(
        "Chọn chức năng:",
        ["Thêm giao dịch mới", "Xem tồn kho", "Báo cáo theo nguyên liệu"]
    )
    
    if function_option == "Thêm giao dịch mới":
        show_transaction_form()
    elif function_option == "Xem tồn kho":
        show_inventory_table()
    else:
        show_material_report()

def show_transaction_form():
    """Hiển thị form thêm giao dịch mới"""
    st.header("➕ Thêm giao dịch mới")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            input_date = st.date_input("Ngày nhập *", value=datetime.now())
            material_name = st.selectbox("Tên nguyên liệu *", [""] + MATERIALS)
            lock_location = st.selectbox("Vị trí kho *", [""] + LOCKS)
            import_bags = st.number_input("Nhập (Bag)", min_value=0, value=0)
            import_weight = st.number_input("Nhập (Weight)", min_value=0.0, value=0.0, step=0.1)
        
        with col2:
            usage_bags = st.number_input("Sử dụng (Bag)", min_value=0, value=0)
            usage_weight = st.number_input("Sử dụng (Weight)", min_value=0.0, value=0.0, step=0.1)
            supplier_code = st.text_input("Code/NCC")
            formula_date = st.date_input("Ngày công thức")
            production_date = st.date_input("Ngày sản xuất")
        
        submitted = st.form_submit_button("💾 Lưu giao dịch")
        
        if submitted:
            if not material_name or not lock_location:
                st.error("Vui lòng nhập Tên nguyên liệu và Vị trí kho!")
            else:
                # Tạo transaction mới
                new_transaction = {
                    "Ngày nhập": input_date,
                    "Name": material_name,
                    "Lock": lock_location,
                    "Tồn đầu (Bag)": 0,  # Sẽ tính sau
                    "Tồn đầu (Weight)": 0,
                    "Nhập (Bag)": import_bags,
                    "Nhập (Weight)": import_weight,
                    "Sử dụng (Bag)": usage_bags,
                    "Sử dụng (Weight)": usage_weight,
                    "Code/NCC": supplier_code,
                    "Ngày công thức": formula_date,
                    "Ngày sản xuất": production_date
                }
                
                # Thêm vào session state
                st.session_state.transactions.append(new_transaction)
                
                # Cập nhật inventory data
                update_inventory_data()
                
                st.success("✅ Giao dịch đã được lưu thành công!")

def update_inventory_data():
    """Cập nhật dữ liệu tồn kho từ transactions"""
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df = calculate_inventory_fields(df)
        st.session_state.inventory_data = df

def show_inventory_table():
    """Hiển thị bảng tồn kho"""
    st.header("📊 Bảng tồn kho tổng hợp")
    
    if st.session_state.inventory_data.empty:
        st.info("📝 Chưa có dữ liệu tồn kho. Hãy thêm giao dịch mới.")
        return
    
    # Hiển thị bảng dữ liệu
    st.dataframe(
        st.session_state.inventory_data,
        use_container_width=True,
        height=400
    )
    
    # Tính tổng
    totals = calculate_totals(st.session_state.inventory_data)
    
    # Hiển thị tổng
    st.subheader("📈 Tổng hợp")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tổng tồn đầu (Bag)", totals.get('Tồn đầu (Bag)', 0))
    with col2:
        st.metric("Tổng nhập (Bag)", totals.get('Nhập (Bag)', 0))
    with col3:
        st.metric("Tổng sử dụng (Bag)", totals.get('Sử dụng (Bag)', 0))
    with col4:
        st.metric("Tổng tồn cuối (Bag)", totals.get('Tồn cuối (Bag)', 0))

def show_material_report():
    """Hiển thị báo cáo theo nguyên liệu"""
    st.header("📋 Báo cáo theo nguyên liệu")
    
    if st.session_state.inventory_data.empty:
        st.info("📝 Chưa có dữ liệu để tạo báo cáo.")
        return
    
    # Chọn nguyên liệu
    selected_material = st.selectbox(
        "Chọn nguyên liệu:",
        [""] + list(st.session_state.inventory_data['Name'].unique())
    )
    
    if selected_material:
        # Lọc dữ liệu theo nguyên liệu
        material_data = st.session_state.inventory_data[
            st.session_state.inventory_data['Name'] == selected_material
        ]
        
        if not material_data.empty:
            st.subheader(f"📦 Báo cáo cho: {selected_material}")
            
            # Hiển thị dữ liệu
            st.dataframe(material_data, use_container_width=True)
            
            # Tính tổng cho nguyên liệu này
            material_totals = calculate_totals(material_data)
            
            # Hiển thị tổng
            st.subheader(f"📊 Tổng hợp - {selected_material}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Tổng nhập (Bag)", material_totals.get('Nhập (Bag)', 0))
                st.metric("Tổng nhập (Weight)", f"{material_totals.get('Nhập (Weight)', 0):.1f}")
            
            with col2:
                st.metric("Tổng sử dụng (Bag)", material_totals.get('Sử dụng (Bag)', 0))
                st.metric("Tổng sử dụng (Weight)", f"{material_totals.get('Sử dụng (Weight)', 0):.1f}")
            
            with col3:
                st.metric("Tổng tồn cuối (Bag)", material_totals.get('Tồn cuối (Bag)', 0))
                st.metric("Tổng tồn cuối (Weight)", f"{material_totals.get('Tồn cuối (Weight)', 0):.1f}")
        else:
            st.warning(f"Không có dữ liệu cho nguyên liệu: {selected_material}")

if __name__ == "__main__":
    main()
