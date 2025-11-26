# ======================================
# MODULE 5 — AI GỢI Ý ĐẶT HÀNG
# ======================================

ai_tab = st.tabs(["🧠 AI Gợi ý đặt hàng"])[0]

with ai_tab:
    st.header("🧠 AI Gợi Ý Đặt Hàng Tự Động")

    df = get_materials()

    if df.empty:
        st.warning("❗Chưa có dữ liệu để phân tích.")
    else:
        st.write("Hệ thống AI sẽ tính toán tốc độ tiêu thụ, dự báo tồn kho và đề xuất mức đặt hàng.")

        # Chuẩn hoá ngày
        df["ngay_nhap"] = pd.to_datetime(df["ngay_nhap"], errors="coerce")

        # Cho chọn lead time
        lead_time = st.number_input("⏱ Lead-time (ngày giao hàng)", 1, 60, 7)

        # Tính Daily Usage theo nguyên liệu
        usage = (
            df.groupby("ten_nguyen_lieu")["khoi_luong_kg"]
            .diff(periods=-1) * -1  # tự tính xuất (nếu xuất nằm trong dòng sau)
        )

        df["xuat_tinh"] = usage
        df["xuat_tinh"] = df["xuat_tinh"].apply(lambda x: x if x > 0 else 0)

        daily_usage = df.groupby("ten_nguyen_lieu")["xuat_tinh"].mean().reset_index()
        daily_usage.rename(columns={"xuat_tinh": "daily_usage"}, inplace=True)

        # Lấy tồn kho hiện tại
        ton = df.groupby("ten_nguyen_lieu")["khoi_luong_kg"].sum().reset_index()
        ton.rename(columns={"khoi_luong_kg": "ton_cuoi"}, inplace=True)

        # Gộp
        result = ton.merge(daily_usage, on="ten_nguyen_lieu", how="left")

        # Xử lý khi thiếu dữ liệu
        result["daily_usage"] = result["daily_usage"].fillna(0.01)

        # Tính số ngày còn
        result["remaining_days"] = result["ton_cuoi"] / result["daily_usage"]

        # Dự đoán số ngày cần tính
        forecast_days = st.number_input("🔮 Số ngày dự báo nhu cầu", 1, 120, 30)

        # Tính gợi ý đặt hàng
        result["reorder_qty"] = result["daily_usage"] * forecast_days - result["ton_cuoi"]
        result["reorder_qty"] = result["reorder_qty"].apply(lambda x: x if x > 0 else 0)

        # Cảnh báo
        def warning_level(days):
            if days < lead_time:
                return "🔴 Đặt ngay"
            elif days < lead_time * 1.5:
                return "🟠 Theo dõi"
            else:
                return "🟢 An toàn"

        result["status"] = result["remaining_days"].apply(warning_level)

        st.subheader("📌 Kết quả phân tích")

        st.dataframe(result)

        # Lọc nhanh
        st.subheader("🔎 Lọc nguyên liệu cần đặt ngay")
        st.dataframe(result[result["status"] == "🔴 Đặt ngay"])
