// Cấu hình màu sắc theo chuẩn AQI (Theo frontend_guideline.md)
export const getAQIColor = (aqi) => {
  if (aqi <= 50) return { bg: "#00E400", text: "#000", label: "Tốt" };
  if (aqi <= 100) return { bg: "#FFFF00", text: "#000", label: "Trung bình" };
  if (aqi <= 150) return { bg: "#FF7E00", text: "#fff", label: "Kém" };
  if (aqi <= 200) return { bg: "#FF0000", text: "#fff", label: "Xấu" };
  if (aqi <= 300) return { bg: "#8F3F97", text: "#fff", label: "Rất xấu" };
  return { bg: "#7E0023", text: "#fff", label: "Nguy hại" };
};
