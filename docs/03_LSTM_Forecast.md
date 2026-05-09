# 3. Dự báo AQI 6 giờ (LSTM Forecast)

## 1. Mục đích
Dự đoán mức độ ô nhiễm không khí trong 1 đến 6 giờ tương lai để cơ quan chức năng có khả năng ra quyết định phòng ngừa (vd: gửi cảnh báo sớm, yêu cầu giảm phát thải) thay vì chỉ phản ứng thụ động với ô nhiễm đã xảy ra.

## 2. Cách hoạt động
- **Thu thập dữ liệu chuỗi thời gian:** Hệ thống gom các bản ghi chỉ số môi trường (PM2.5, Nhiệt độ, Gió...) trong 24 giờ gần nhất của mỗi trạm.
- **Tiền xử lý:** Các dữ liệu này được đưa qua hàm chuẩn hóa (StandardScaler) để đưa về cùng một tỷ lệ tính toán.
- **Chạy suy luận (Inference):** Dữ liệu được đưa vào mô hình học sâu LSTM (Long Short-Term Memory).
- **Kết quả trả về:** LSTM trả về các giá trị dự báo chỉ số AQI cho các mốc +1h, +2h, ..., +6h.
- **Hiển thị:** Dữ liệu dự báo được vẽ lên biểu đồ đường nối tiếp với dữ liệu quá khứ.

## 3. Kỹ thuật & Công nghệ sử dụng
- **Machine Learning (Học sâu):**
  - **Thuật toán LSTM (Long Short-Term Memory):** Là mạng nơ-ron hồi quy (RNN) cực kỳ mạnh mẽ trong việc ghi nhớ và học các mẫu hình chuỗi thời gian (Time-series forecasting).
  - **PyTorch:** Framework mã nguồn mở của Python dùng để build, train và load trọng số (weights) của mô hình LSTM.
- **Backend:**
  - Lớp `InferenceService` (Python) chịu trách nhiệm load mô hình `.pt` vào RAM, nhận dữ liệu chuỗi 24h từ DB, chạy Tensor computation qua GPU/CPU để xuất ra mảng kết quả.
- **Frontend:**
  - **Recharts:** Thư viện vẽ biểu đồ của React, được dùng để render các mốc thời gian liên tục kết nối từ "Quá khứ" đến "Dự báo" trên cùng một LineChart.

## 4. Tệp mã nguồn tham khảo
- ML Training: `ml_training/models/lstm/`
- Backend: `backend/app/services/inference_service.py`
- Frontend: `frontend/src/pages/Forecast.jsx`
