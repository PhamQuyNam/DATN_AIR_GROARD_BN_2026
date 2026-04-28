import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import ForecastChart from '../components/Charts/ForecastChart';

export default function Forecast() {
  const [selectedVillage, setSelectedVillage] = useState('Đồng Kỵ'); // Default

  // 1. Fetch danh sách làng nghề
  const { data: villages, isLoading: loadingVillages } = useQuery({
    queryKey: ['villages'],
    queryFn: async () => {
      const res = await api.get('/villages');
      return res.data;
    }
  });

  // 2. Fetch lịch sử 24 điểm gần nhất
  const { data: historyData, isLoading: loadingHistory } = useQuery({
    queryKey: ['aqiHistory', selectedVillage],
    queryFn: async () => {
      const res = await api.get(`/aqi/history/${encodeURIComponent(selectedVillage)}?limit=24`);
      return res.data.data;
    },
    enabled: !!selectedVillage
  });

  // 3. Fetch dự báo 6h từ LSTM
  const { data: forecastData, isLoading: loadingForecast } = useQuery({
    queryKey: ['aqiForecast', selectedVillage],
    queryFn: async () => {
      const res = await api.get(`/forecast/${encodeURIComponent(selectedVillage)}`);
      return res.data.forecasts;
    },
    enabled: !!selectedVillage
  });

  const isLoading = loadingVillages || loadingHistory || loadingForecast;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            Dự báo Chất lượng Không khí (AI)
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Sử dụng mô hình học sâu LSTM_Attention dự báo AQI 6 giờ tới.
          </p>
        </div>
        
        {/* Dropdown Chọn làng nghề */}
        <div className="min-w-[250px]">
          <select 
            value={selectedVillage}
            onChange={(e) => setSelectedVillage(e.target.value)}
            className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-xl focus:ring-blue-500 focus:border-blue-500 block p-3 shadow-sm transition-all outline-none"
          >
            {villages?.map(v => (
              <option key={v.name} value={v.name}>{v.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm relative overflow-hidden">
        
        {/* Trang trí nền */}
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-orange-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              Biểu đồ xu hướng tại {selectedVillage}
            </h3>
            <span className="px-3 py-1 bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold rounded-full uppercase tracking-wider">
              LSTM Forecast
            </span>
          </div>

          {isLoading ? (
            <div className="h-[400px] flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
              <p className="text-gray-500">Đang chạy nội suy AI...</p>
            </div>
          ) : (
            <ForecastChart historicalData={historyData} forecastData={forecastData} />
          )}
        </div>
      </div>

      {/* Grid hiển thị số liệu dự báo cụ thể */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mt-6">
        {forecastData?.map((f, idx) => (
          <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm flex flex-col items-center justify-center hover:-translate-y-1 transition-transform">
            <span className="text-gray-500 dark:text-gray-400 text-xs font-medium uppercase tracking-wider mb-2">
              +{f.forecast_hour} Giờ
            </span>
            <span className={`text-2xl font-black ${f.predicted_aqi > 100 ? 'text-orange-500' : 'text-blue-500'}`}>
              {Math.round(f.predicted_aqi)}
            </span>
            <span className="text-gray-400 text-xs mt-1">
              {new Date(f.timestamp).getHours()}:00
            </span>
          </div>
        ))}
      </div>

    </motion.div>
  );
}
