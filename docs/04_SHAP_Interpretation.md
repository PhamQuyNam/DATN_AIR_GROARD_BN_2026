# 4. Giải thích nguyên nhân (SHAP Interpretation)

## 1. Mục đích
Mở "Hộp đen" (Black-box) của AI. Cung cấp câu trả lời rõ ràng cho quản lý về việc "Tại sao AI lại dự báo mức AQI này?", chỉ đích danh thông số nào đang đóng góp lớn nhất vào tình trạng ô nhiễm.

## 2. Cách hoạt động
- Khi một tập dữ liệu mới đi qua mô hình học máy (XGBoost) để phân loại/đánh giá chỉ số chất lượng không khí.
- Thuật toán SHAP sẽ chạy song song, phân rã kết quả dự đoán thành các giá trị đóng góp thành phần (SHAP Values) cho từng input (PM2.5, Nhiệt độ, Độ ẩm...).
- Cán bộ mở màn hình Giải thích nguyên nhân, chọn Làng nghề.
- Frontend sẽ gọi API lấy mảng `shap_values` mới nhất. Các yếu tố mang giá trị Dương (Màu Đỏ) nghĩa là làm TĂNG ô nhiễm; giá trị Âm (Màu Xanh) làm GIẢM ô nhiễm (ví dụ gió to).
- Hệ thống cũng sinh ra kết luận bằng lời: "Nguyên nhân chính làm tăng ô nhiễm là PM2.5 (+44 đơn vị)".

## 3. Kỹ thuật & Công nghệ sử dụng
- **Explainable AI (XAI):**
  - **SHAP (SHapley Additive exPlanations):** Phương pháp tiếp cận dựa trên lý thuyết trò chơi (Game Theory) để tính toán giá trị đóng góp biên của mỗi tính năng (Feature Importance) trong mô hình ML.
  - **XGBoost:** Mô hình Gradient Boosting Trees được sử dụng để phân loại (Classification) mức độ AQI. SHAP TreeExplainer được tích hợp để giải thích trực tiếp cấu trúc cây của XGBoost.
- **Backend:**
  - Data pipeline tự động tính SHAP values mỗi giờ và lưu trực tiếp vào field JSON `shap_values` trong bảng `AQILog` của PostgreSQL.
- **Frontend:**
  - Vẽ biểu đồ thanh ngang dạng "Waterfall" hoặc BarChart 2 chiều (âm/dương) bằng Recharts hoặc Framer Motion.

## 4. Tệp mã nguồn tham khảo
- Backend: `backend/app/api/routes/shap.py`, `backend/app/seed_shap.py`
- Frontend: `frontend/src/pages/ShapAnalysis.jsx`
