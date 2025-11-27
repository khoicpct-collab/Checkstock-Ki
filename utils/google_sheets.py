import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime
import os

class GoogleSheetsManager:
    def __init__(self):
        self.credentials_file = "google_credentials.json"
        self.sheet_id = None  # Will be set from Streamlit secrets
        self.client = None
        self.sheet = None
        
    def initialize_client(self):
        """Khởi tạo client Google Sheets"""
        try:
            # Cách 1: Dùng Streamlit secrets (recommended for deployment)
            if 'GOOGLE_CREDENTIALS' in st.secrets and 'SHEET_ID' in st.secrets:
                credentials_dict = st.secrets['GOOGLE_CREDENTIALS']
                self.sheet_id = st.secrets['SHEET_ID']
                
                # Tạo credentials từ secrets
                creds = Credentials.from_service_account_info(credentials_dict)
                self.client = gspread.authorize(creds)
            
            # Cách 2: Dùng file JSON local (for development)
            elif os.path.exists(self.credentials_file):
                creds = Credentials.from_service_account_file(self.credentials_file)
                self.client = gspread.authorize(creds)
                
                # Sheet ID từ environment variable hoặc config
                self.sheet_id = os.getenv('SHEET_ID', 'your_sheet_id_here')
            
            else:
                st.error("❌ Không tìm thấy Google Sheets credentials")
                return False
                
            # Mở sheet
            self.sheet = self.client.open_by_key(self.sheet_id)
            st.success("✅ Đã kết nối Google Sheets thành công!")
            return True
            
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
            return False
    
    def get_worksheet(self, worksheet_name="Inventory"):
        """Lấy worksheet theo tên"""
        try:
            if not self.sheet:
                if not self.initialize_client():
                    return None
            
            # Thử lấy worksheet có sẵn
            try:
                worksheet = self.sheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                # Nếu không tồn tại, tạo mới
                worksheet = self.sheet.add_worksheet(
                    title=worksheet_name, 
                    rows="1000", 
                    cols="20"
                )
                # Tạo headers
                headers = [
                    "ID", "Ngày nhập", "Name", "Lock", 
                    "Tồn đầu (Bag)", "Tồn đầu (Weight)",
                    "Nhập (Bag)", "Nhập (Weight)", 
                    "Sử dụng (Bag)", "Sử dụng (Weight)",
                    "Tồn cuối (Bag)", "Tồn cuối (Weight)",
                    "Trung bình", "Tuổi lưu kho",
                    "Code/NCC", "Ngày công thức", "Ngày sản xuất",
                    "Created_At", "Updated_At"
                ]
                worksheet.append_row(headers)
            
            return worksheet
            
        except Exception as e:
            st.error(f"❌ Lỗi khi lấy worksheet: {e}")
            return None
    
    def append_transaction(self, transaction_data, worksheet_name="Inventory"):
        """Thêm transaction mới vào Google Sheets"""
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return False
            
            # Chuẩn bị dữ liệu row
            row_data = [
                str(datetime.now().timestamp()),  # ID unique
                transaction_data.get('Ngày nhập', ''),
                transaction_data.get('Name', ''),
                transaction_data.get('Lock', ''),
                transaction_data.get('Tồn đầu (Bag)', 0),
                transaction_data.get('Tồn đầu (Weight)', 0),
                transaction_data.get('Nhập (Bag)', 0),
                transaction_data.get('Nhập (Weight)', 0),
                transaction_data.get('Sử dụng (Bag)', 0),
                transaction_data.get('Sử dụng (Weight)', 0),
                transaction_data.get('Tồn cuối (Bag)', 0),
                transaction_data.get('Tồn cuối (Weight)', 0),
                transaction_data.get('Trung bình', ''),
                transaction_data.get('Tuổi lưu kho', ''),
                transaction_data.get('Code/NCC', ''),
                transaction_data.get('Ngày công thức', ''),
                transaction_data.get('Ngày sản xuất', ''),
                datetime.now().isoformat(),  # Created_At
                datetime.now().isoformat()   # Updated_At
            ]
            
            # Thêm row mới
            worksheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"❌ Lỗi khi thêm transaction: {e}")
            return False
    
    def get_all_data(self, worksheet_name="Inventory"):
        """Lấy tất cả dữ liệu từ Google Sheets"""
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return pd.DataFrame()
            
            # Lấy tất cả records
            records = worksheet.get_all_records()
            
            if not records:
                return pd.DataFrame()
            
            # Chuyển thành DataFrame
            df = pd.DataFrame(records)
            
            # Xử lý datetime columns
            date_columns = ['Ngày nhập', 'Ngày công thức', 'Ngày sản xuất']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            st.error(f"❌ Lỗi khi lấy dữ liệu: {e}")
            return pd.DataFrame()
    
    def update_inventory_data(self, df, worksheet_name="Inventory"):
        """Cập nhật toàn bộ dữ liệu inventory"""
        try:
            worksheet = self.get_worksheet(worksheet_name)
            if not worksheet:
                return False
            
            # Clear worksheet
            worksheet.clear()
            
            # Thêm headers
            headers = df.columns.tolist()
            worksheet.append_row(headers)
            
            # Thêm dữ liệu
            for _, row in df.iterrows():
                worksheet.append_row(row.fillna('').tolist())
            
            return True
            
        except Exception as e:
            st.error(f"❌ Lỗi khi cập nhật dữ liệu: {e}")
            return False

# Singleton instance
google_sheets_manager = GoogleSheetsManager()
