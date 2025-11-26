# ======================================
# MODULE 4 — DASHBOARD THỐNG KÊ KHO
# ======================================

import altair as alt

dash_tab = st.tabs(["📊 Dashboard"])[0]

with dash_tab:
    st.header("📊 Dashboard Thống Kê Kho")

    df = get_materials()

    if df.empty:
        st.warning("❗Chưa có dữ liệu trong kho.")
    else:

        # ------------------------
        # TÍNH TOÁN SUMMARY
        # ------------------------
        tong_nguyen_lieu = df["ten_nguyen_lieu"].nunique()
        tong_lo = df["lo"].nunique()
        tong_kg = df["khoi_luong_kg"].sum()
        tong_bao = df["so_bao"].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("🧪 Số nguyên liệu", tong_nguyen_lieu)
        col2.metric("📦 Số lô", tong_lo)
        col3.metric("⚖ Tổng khối lượng (kg)", f"{tong_kg:,.2f}")
        col4.metric("🎒 Tổng số bao", int(tong_bao))

        st.divider()

        # ------------------------
        # BIỂU ĐỒ TỒN KHO THEO NGUYÊN LIỆU
        # ------------------------
        st.subheader("📉 Tồn kho theo nguyên liệu")

        df_group = df.groupby("ten_nguyen_lieu")["khoi_luong_kg"].sum().reset_index()

        bar_chart = (
            alt.Chart(df_group)
            .mark_bar()
            .encode(
                x="ten_nguyen_lieu",
                y="khoi_luong_kg",
                tooltip=["ten_nguyen_lieu", "khoi_luong_kg"]
            )
            .properties(height=400)
        )
        st.altair_chart(bar_chart, use_container_width=True)

        st.divider()

        # ------------------------
        # BIỂU ĐỒ NHẬP – XUẤT THEO NGÀY
        # ------------------------
        st.subheader("📆 Biểu đồ nhập – xuất theo ngày")

        df_time = df.copy()
        df_time["ngay_nhap"] = pd.to_datetime(df_time["ngay_nhap"], errors="coerce")
        df_time["date"] = df_time["ngay_nhap"].dt.date

        line_chart = (
            alt.Chart(df_time)
            .mark_line(point=True)
            .encode(
                x="date:T",
                y="khoi_luong_kg:Q",
                color="ten_nguyen_lieu:N",
                tooltip=["ten_nguyen_lieu", "khoi_luong_kg", "date"]
            )
            .properties(height=350)
        )
        st.altair_chart(line_chart, use_container_width=True)

        st.divider()

        # ------------------------
        # CẢNH BÁO HÀNG QUÁ LÂU
        # ------------------------
        st.subheader("🚨 Cảnh báo tồn lâu")

        df_alert = df[df["age"] > 60]   # >60 ngày

        if df_alert.empty:
            st.success("✔ Không có nguyên liệu tồn kho quá lâu (Age > 60 ngày)")
        else:
            st.error("⚠ Có nguyên liệu tồn lâu hơn 60 ngày!")
            st.dataframe(df_alert)

        st.divider()

        # ------------------------
        # LỌC CHI TIẾT
        # ------------------------
        st.subheader("🔎 Lọc chi tiết")

        ten_list = ["Tất cả"] + sorted(df["ten_nguyen_lieu"].unique().tolist())
        pick_ten = st.selectbox("Chọn nguyên liệu", ten_list)

        if pick_ten != "Tất cả":
            df_filter = df[df["ten_nguyen_lieu"] == pick_ten]
        else:
            df_filter = df

        st.dataframe(df_filter)
