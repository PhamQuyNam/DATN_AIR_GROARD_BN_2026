import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import ShapBarChart from '../components/Charts/ShapBarChart';

export default function ShapAnalysis() {
  const [selectedVillage, setSelectedVillage] = useState('Đồng Kỵ'); // Default

  // 1. Fetch danh sách làng nghề
  const { data: villages } = useQuery({
    queryKey: ['villages'],
    queryFn: async () => {
      const res = await api.get('/villages');
      return res.data;
    }
  });

  // 2. Fetch dữ liệu SHAP
  const { data: shapResult, isLoading } = useQuery({
    queryKey: ['shap', selectedVillage],
    queryFn: async () => {
      const res = await api.get(`/shap/${encodeURIComponent(selectedVillage)}`);
      return res.data;
    },
    enabled: !!selectedVillage
  });

  // Tìm nguyên nhân lớn nhất làm tăng ô nhiễm
  const getMainCause = () => {
    if (!shapResult?.shap_values) return null;
    let maxFactor = null;
    let maxValue = 0;
    
    Object.entries(shapResult.shap_values).forEach(([key, value]) => {
      if (value > maxValue) {
        maxValue = value;
        maxFactor = key;
      }
    });
    
    return { factor: maxFactor?.toUpperCase(), value: maxValue };
  };

  const mainCause = getMainCause();

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
            Chuẩn đoán Nguyên nhân Ô nhiễm
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Sử dụng XGBoost và công nghệ XAI (Explainable AI - SHAP) để bóc tách yếu tố gây ô nhiễm.
          </p>
        </div>
        
        <div className="min-w-[250px]">
          <select 
            value={selectedVillage}
            onChange={(e) => setSelectedVillage(e.target.value)}
            className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-xl focus:ring-blue-500 focus:border-blue-500 block p-3 shadow-sm outline-none"
          >
            {villages?.map(v => (
              <option key={v.name} value={v.name}>{v.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel Kết luận bằng lời */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
            
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Kết luận AI</h3>
            
            {isLoading ? (
              <div className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-4 py-1">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
                </div>
              </div>
            ) : mainCause?.factor ? (
              <div className="space-y-4 relative z-10">
                <div className="p-4 bg-red-50 dark:bg-red-500/10 rounded-xl border border-red-100 dark:border-red-500/20">
                  <p className="text-sm text-red-800 dark:text-red-400 font-medium">Nguyên nhân chính làm TĂNG ô nhiễm hiện tại là:</p>
                  <p className="text-3xl font-black text-red-600 mt-2">{mainCause.factor}</p>
                  <p className="text-xs text-red-700/70 dark:text-red-400/70 mt-1">Đóng góp +{mainCause.value.toFixed(1)} đơn vị vào chỉ số AQI.</p>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <strong>SHAP (SHapley Additive exPlanations)</strong> bóc tách mức độ tác động của từng thông số (Khí thải, Thời tiết) đến kết quả cuối cùng. Giá trị <span className="text-red-500 font-bold">dương (Đỏ)</span> là tác nhân gây xấu đi, giá trị <span className="text-blue-500 font-bold">âm (Xanh)</span> giúp không khí sạch hơn (Ví dụ: Gió to làm phát tán bụi).
                </p>
              </div>
            ) : (
              <div className="text-gray-500">Chưa có đủ dữ liệu suy luận cho thời điểm này.</div>
            )}
          </div>
        </div>

        {/* Panel Biểu đồ */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm relative overflow-hidden">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
            Mức độ tác động của các chỉ số (Feature Importance)
          </h3>
          
          {isLoading ? (
            <div className="h-[400px] flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-red-500 mb-4"></div>
            </div>
          ) : (
            <ShapBarChart shapData={shapResult?.shap_values} />
          )}
        </div>

      </div>
    </motion.div>
  );
}
