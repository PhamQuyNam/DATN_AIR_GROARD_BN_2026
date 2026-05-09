import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from 'recharts';
import api from '../services/api';
import { getAQIColor } from '../utils/aqiColors';

export default function Analytics() {
  const { data: currentAqi, isLoading } = useQuery({
    queryKey: ['currentAqiAll'],
    queryFn: async () => {
      const res = await api.get('/aqi/current');
      return res.data.data;
    }
  });

  // Xử lý dữ liệu cho biểu đồ xếp hạng AQI
  const rankingData = currentAqi ? [...currentAqi].sort((a, b) => b.aqi - a.aqi) : [];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
          Thống kê Tổng quan (Analytics)
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Bảng xếp hạng mức độ ô nhiễm tại 18 làng nghề toàn tỉnh Bắc Ninh.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
          Xếp hạng Mức độ Ô nhiễm (AQI) Hiện tại
        </h3>
        
        {isLoading ? (
          <div className="h-[400px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="h-[500px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={rankingData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.1} vertical={false} />
                <XAxis 
                  dataKey="village_name" 
                  angle={-45} 
                  textAnchor="end" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }} 
                  interval={0}
                  height={80}
                />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <RechartsTooltip 
                  cursor={{ fill: 'transparent' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const color = getAQIColor(data.aqi);
                      return (
                        <div className="bg-white/95 dark:bg-gray-800/95 p-3 rounded shadow-xl border dark:border-gray-700">
                          <p className="font-bold dark:text-white">{data.village_name}</p>
                          <p className="font-bold mt-1" style={{ color: color.bg }}>
                            AQI: {Math.round(data.aqi)} ({data.level})
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">PM2.5: {data.pm25} µg/m³</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="aqi" radius={[4, 4, 0, 0]}>
                  {rankingData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getAQIColor(entry.aqi).bg} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      
      {/* Thống kê Tổng quan (Summary Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex flex-col items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400 font-medium">Làng nghề ô nhiễm nhất</p>
          <p className="text-2xl font-black text-red-500 mt-2">{rankingData[0]?.village_name || '--'}</p>
          <p className="text-sm font-bold mt-1 text-gray-400">AQI: {Math.round(rankingData[0]?.aqi || 0)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex flex-col items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400 font-medium">Làng nghề sạch nhất</p>
          <p className="text-2xl font-black text-green-500 mt-2">{rankingData[rankingData.length - 1]?.village_name || '--'}</p>
          <p className="text-sm font-bold mt-1 text-gray-400">AQI: {Math.round(rankingData[rankingData.length - 1]?.aqi || 0)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm flex flex-col items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400 font-medium">Chỉ số Trung bình toàn tỉnh</p>
          <p className="text-2xl font-black text-blue-500 mt-2">
            {rankingData.length > 0 ? Math.round(rankingData.reduce((acc, curr) => acc + curr.aqi, 0) / rankingData.length) : '--'}
          </p>
          <p className="text-sm font-bold mt-1 text-gray-400">AQI</p>
        </div>
      </div>
    </motion.div>
  );
}
