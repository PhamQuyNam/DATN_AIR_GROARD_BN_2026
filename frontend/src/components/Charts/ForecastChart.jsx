import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, ReferenceArea
} from 'recharts';
import { format } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-md p-3 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700">
        <p className="font-bold text-gray-900 dark:text-gray-100 mb-2">
          {format(new Date(data.timestamp), 'HH:mm - dd/MM/yyyy')}
        </p>
        <div className="flex flex-col gap-1">
          {data.forecast_aqi !== null ? (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#f59e0b]"></div>
              <span className="text-gray-600 dark:text-gray-300">AQI Dự báo:</span>
              <span className="font-bold text-[#f59e0b]">{Math.round(data.forecast_aqi)}</span>
            </div>
          ) : null}
          
          {data.history_aqi !== null ? (
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#3b82f6]"></div>
              <span className="text-gray-600 dark:text-gray-300">AQI Thực tế:</span>
              <span className="font-bold text-[#3b82f6]">{Math.round(data.history_aqi)}</span>
            </div>
          ) : null}
        </div>
      </div>
    );
  }
  return null;
};

export default function ForecastChart({ historicalData, forecastData }) {
  // Chuẩn bị dữ liệu cho biểu đồ
  const displayData = [];

  // 1. Thêm dữ liệu lịch sử
  (historicalData || []).forEach(d => {
    displayData.push({
      timestamp: d.timestamp,
      history_aqi: d.aqi,
      forecast_aqi: null,
      isForecast: false
    });
  });

  // Nối liền đường: Tại mốc thời gian cuối cùng của lịch sử, gán giá trị cho cả đường dự báo
  if (displayData.length > 0) {
    displayData[displayData.length - 1].forecast_aqi = displayData[displayData.length - 1].history_aqi;
  }

  // 2. Thêm dữ liệu dự báo
  (forecastData || []).forEach(d => {
    displayData.push({
      timestamp: d.timestamp,
      history_aqi: null,
      forecast_aqi: d.predicted_aqi,
      isForecast: true
    });
  });

  return (
    <div className="h-[400px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={displayData} margin={{ top: 20, right: 30, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} vertical={false} />
          
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(timeStr) => format(new Date(timeStr), 'HH:mm')}
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            tickMargin={10}
            minTickGap={20}
          />
          
          <YAxis 
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            domain={[0, dataMax => Math.ceil((dataMax || 150) + 20)]}
            label={{ value: '(AQI)', angle: -90, position: 'insideLeft', fill: '#9ca3af', offset: -5 }}
          />
          
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" height={36} />

          {/* Tham chiếu các dải màu AQI nền */}
          <ReferenceArea y1={0} y2={50} fill="#10b981" fillOpacity={0.05} />
          <ReferenceArea y1={50} y2={100} fill="#eab308" fillOpacity={0.05} />
          <ReferenceArea y1={100} y2={150} fill="#f97316" fillOpacity={0.05} />
          <ReferenceArea y1={150} y2={200} fill="#ef4444" fillOpacity={0.05} />

          {/* Đường thực tế */}
          <Line 
            type="monotone" 
            dataKey="history_aqi"
            name="Thực tế (24h qua)"
            stroke="#3b82f6" 
            strokeWidth={3}
            dot={{ r: 0 }}
            activeDot={{ r: 6, strokeWidth: 0 }}
            connectNulls
          />

          {/* Đường dự báo */}
          <Line 
            type="monotone" 
            dataKey="forecast_aqi"
            name="Dự báo LSTM (6h tới)"
            stroke="#f59e0b" 
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ r: 4, fill: '#f59e0b', strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 8, strokeWidth: 0 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
