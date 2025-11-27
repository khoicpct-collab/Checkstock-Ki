import streamlit as st

# Configure page
st.set_page_config(
    page_title="Checkstock System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
def local_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    local_css()
    
    st.markdown('<h1 class="main-header">📦 HỆ THỐNG QUẢN LÝ KHO CHECKSTOCK</h1>', unsafe_allow_html=True)
    
    st.sidebar.title("🎯 Điều hướng")
    
    # Navigation
    page_options = {
        "🏠 Trang chủ": "Trang chủ",
        "📤 Upload & Chuẩn hoá": "Upload & Chuẩn hoá", 
        "📊 Dashboard": "Dashboard",
        "📋 Báo cáo tồn kho": "Báo cáo tồn kho",
        "📦 Quản lý kho": "Quản lý kho",
        "🔄 Nhập xuất kho": "Nhập xuất kho"
    }
    
    selected_page = st.sidebar.radio("Chọn trang:", list(page_options.keys()))
    
    # Page routing
    if selected_page == "🏠 Trang chủ":
        show_home_page()
    elif selected_page == "📤 Upload & Chuẩn hoá":
        st.switch_page("pages/upload_chuan_hoa.py")
    elif selected_page == "📊 Dashboard":
        st.switch_page("pages/dashboard.py")
    elif selected_page == "📋 Báo cáo tồn kho":
        st.switch_page("pages/bao_cao_ton_kho.py")
    elif selected_page == "📦 Quản lý kho":
        st.switch_page("pages/quan_ly_kho.py")
    elif selected_page == "🔄 Nhập xuất kho":
        st.switch_page("pages/nhap_xuat_kho.py")

def show_home_page():
    """Hiển thị trang chủ"""
    st.markdown("""
    ## 🚀 Chào mừng đến với Hệ thống Quản lý Kho Checkstock
    
    **Checkstock** là hệ thống quản lý kho thông minh, giúp bạn:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📤 Upload & Chuẩn hoá</h3>
            <p>Upload file Excel và tự động chuẩn hoá dữ liệu tồn kho</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Dashboard</h3>
            <p>Theo dõi tồn kho với biểu đồ trực quan và báo cáo chi tiết</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📦 Quản lý kho</h3>
            <p>Nhập liệu trực tiếp với form thân thiện và tính toán tự động</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats (nếu có dữ liệu)
    st.markdown("---")
    st.subheader("📈 Thống kê nhanh")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tổng nguyên liệu", "50+", "3 mới")
    with col2:
        st.metric("Vị trí kho", "60+", "2 mới")
    with col3:
        st.metric("Giao dịch hôm nay", "12", "5 nhập")
    with col4:
        st.metric("Tổng tồn kho", "1,250", "45 bags")

if __name__ == "__main__":
    main()
