# DATN_AIR_GROARD_BN_2026
# 🌫️ AirGuard BN

> **Hệ thống giám sát và cảnh báo chất lượng không khí tại làng nghề tỉnh Bắc Ninh ứng dụng XGBoost-SHAP và LSTM**

---

## 📖 Giới thiệu

Bắc Ninh là tỉnh có hàng chục làng nghề công nghiệp với mức độ ô nhiễm không khí đáng báo động. **AirGuard BN** ra đời nhằm giải quyết bài toán đó — một hệ thống thông minh ứng dụng trí tuệ nhân tạo để:

- 🔮 **Dự báo chỉ số AQI trước 24 giờ**
- 🔍 **Xác định nguồn gây ô nhiễm chính** thông qua phân tích SHAP
- 🔔 **Tự động cảnh báo** khi chất lượng không khí vượt ngưỡng an toàn

Không chỉ hiển thị số liệu, AirGuard BN còn **giải thích vì sao** ô nhiễm xảy ra — giúp người dân và cơ quan chức năng hành động đúng lúc, đúng chỗ.

---

## 🎯 Tính năng chính

| Tính năng | Mô tả |
|---|---|
| 🗺️ **Bản đồ AQI thời gian thực** | Hiển thị chỉ số AQI theo màu sắc tại các làng nghề Bắc Ninh |
| 🔮 **Dự báo 24 giờ** | Dự báo chỉ số AQI trong 24 giờ tới bằng mô hình LSTM |
| 🧠 **Giải thích AI (SHAP)** | Xác định yếu tố nào ảnh hưởng nhiều nhất đến ô nhiễm |
| 🔔 **Cảnh báo tự động** | Thông báo ngay khi AQI vượt ngưỡng QCVN/WHO |
| 📊 **Biểu đồ xu hướng** | Theo dõi diễn biến ô nhiễm theo giờ/ngày/tuần |

---

## 🧠 Mô hình học máy

```
AirGuard BN sử dụng 2 mô hình chính:

┌─────────────────────────────────────────────┐
│  XGBoost + SHAP                             │
│  → Phân loại mức độ AQI                     │
│  → Giải thích yếu tố gây ô nhiễm            │
│  → Độ chính xác: R² ≈ 0.92–0.96            │
├─────────────────────────────────────────────┤
│  LSTM (Long Short-Term Memory)              │
│  → Dự báo chuỗi thời gian 24h tới          │
│  → Nắm bắt xu hướng ô nhiễm dài hạn        │
│  → Độ chính xác: R² ≈ 0.90–0.95            │
└─────────────────────────────────────────────┘
```

---

## 🏗️ Kiến trúc hệ thống

```
📡 Thu thập dữ liệu
├── OpenAQ API          (PM2.5, SO₂, NO₂, CO, O₃)
├── PAMair              (Mạng lưới cảm biến Việt Nam)
├── Open-Meteo API      (Khí tượng: gió, nhiệt độ, độ ẩm)
└── Sở TN&MT Bắc Ninh  (Dữ liệu quan trắc thực địa)

🧠 Xử lý & Học máy
├── Tiền xử lý dữ liệu (chuẩn hóa, xử lý missing)
├── XGBoost + SHAP     (phân loại & giải thích)
└── LSTM               (dự báo chuỗi thời gian)

🌐 Hệ thống Web
├── Backend:   FastAPI (Python)
├── Frontend:  React.js + Leaflet.js
├── Database:  PostgreSQL + TimescaleDB
└── Deploy:    Docker
```

---

## 📊 Thang đo AQI

| Mức AQI | Mức độ | Màu sắc | Khuyến nghị |
|---|---|---|---|
| 0 – 50 | Tốt | 🟢 Xanh lá | Hoạt động bình thường |
| 51 – 100 | Trung bình | 🟡 Vàng | Nhóm nhạy cảm nên hạn chế |
| 101 – 150 | Kém | 🟠 Cam | Hạn chế hoạt động ngoài trời |
| 151 – 200 | Xấu | 🔴 Đỏ | Tránh hoạt động ngoài trời |
| 201 – 300 | Rất xấu | 🟣 Tím | Ở trong nhà |
| > 300 | Nguy hại | 🟤 Nâu | Khẩn cấp — sơ tán nếu cần |

---

## 🗂️ Cấu trúc thư mục

```
AirGuard-BN/
├── backend/                  # FastAPI backend
│   ├── api/                  # REST API endpoints
│   ├── models/               # Mô hình ML (XGBoost, LSTM)
│   ├── services/             # Logic xử lý dữ liệu
│   └── database/             # Kết nối PostgreSQL
├── frontend/                 # React.js frontend
│   ├── components/           # UI components
│   ├── pages/                # Các trang web
│   └── services/             # API calls
├── ml/                       # Notebook huấn luyện mô hình
│   ├── data_preprocessing/   # Tiền xử lý dữ liệu
│   ├── xgboost_shap/         # Mô hình XGBoost + SHAP
│   └── lstm/                 # Mô hình LSTM
├── data/                     # Dữ liệu thô và đã xử lý
├── docker-compose.yml        # Cấu hình Docker
└── README.md
```

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống
- Python >= 3.9
- Node.js >= 18
- Docker & Docker Compose
- PostgreSQL >= 14

### Cài đặt nhanh

```bash
# 1. Clone repository
git clone https://github.com/your-username/airguard-bn.git
cd airguard-bn

# 2. Khởi động toàn bộ hệ thống bằng Docker
docker-compose up -d

# 3. Truy cập hệ thống
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

---

## 📦 Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| **Backend** | FastAPI, Python 3.9+ |
| **Frontend** | React.js, Leaflet.js, Chart.js |
| **Machine Learning** | XGBoost, SHAP, TensorFlow/Keras (LSTM) |
| **Database** | PostgreSQL, TimescaleDB |
| **DevOps** | Docker, Docker Compose |
| **Data Source** | OpenAQ API, PAMair, Open-Meteo |

---

## 📍 Khu vực nghiên cứu — Làng nghề Bắc Ninh

| Làng nghề | Loại hình | Chỉ số đặc trưng |
|---|---|---|
| Phong Khê | Tái chế giấy | SO₂, Bụi PM2.5 |
| Đa Hội (Châu Khê) | Tái chế thép | Bụi kim loại, SO₂ |
| Đại Bái | Đúc đồng | Cu, Pb, Bụi |
| Khắc Niệm | Chế biến bún | BOD, Mùi hữu cơ |
| Đồng Kỵ | Đồ gỗ mỹ nghệ | VOC, Bụi gỗ |

---

## 👨‍💻 Tác giả

> **Đồ án tốt nghiệp — Kỹ thuật phần mềm**
> Trường: SICT - Trường Công Nghệ Thông Tin và Truyền Thông - Đại học Công Nghiệp Hà Nội
> Sinh viên: Phạm Qúy Nam
> GVHD: ThS. Nguyễn Thái Cường
> Năm: 2026

---

## 📄 Tài liệu tham khảo

- OpenAQ Platform: https://openaq.org
- PAMair Vietnam: https://pamair.org
- XGBoost Documentation: https://xgboost.readthedocs.io
- SHAP Library: https://shap.readthedocs.io
- Keras/TensorFlow LSTM: https://keras.io

---

## 📜 Giấy phép

Dự án được phát triển phục vụ mục đích nghiên cứu học thuật.

---

<div align="center">
  <strong>AirGuard BN</strong> — Vì một Bắc Ninh trong lành hơn 🌿
</div>
