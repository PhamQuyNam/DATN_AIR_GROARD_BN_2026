import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from 'recharts';

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isPositive = data.value > 0;
    return (
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-md p-3 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700">
        <p className="font-bold text-gray-900 dark:text-gray-100 mb-1 uppercase">
          Yếu tố: {data.name}
        </p>
        <p className={`font-semibold ${isPositive ? 'text-red-500' : 'text-blue-500'}`}>
          Tác động: {isPositive ? '+' : ''}{data.value.toFixed(2)} đơn vị AQI
        </p>
        <p className="text-xs text-gray-500 mt-2">
          {isPositive 
            ? 'Yếu tố này làm TĂNG ô nhiễm.' 
            : 'Yếu tố này làm GIẢM ô nhiễm.'}
        </p>
      </div>
    );
  }
  return null;
};

export default function ShapBarChart({ shapData }) {
  // Chuyển đổi dữ liệu từ object {"pm25": 12.5, "o3": -2.1} sang mảng cho Recharts
  if (!shapData || Object.keys(shapData).length === 0) {
    return <div className="h-full flex items-center justify-center text-gray-400">Không có dữ liệu phân tích</div>;
  }

  const dataArray = Object.entries(shapData).map(([key, value]) => ({
    name: key.toUpperCase(),
    value: parseFloat(value)
  })).sort((a, b) => Math.abs(b.value) - Math.abs(a.value)); // Sắp xếp theo mức độ ảnh hưởng (trị tuyệt đối)

  return (
    <div className="h-[400px] w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={dataArray}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.1} horizontal={true} vertical={false} />
          <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <YAxis dataKey="name" type="category" tick={{ fill: '#9ca3af', fontSize: 12, fontWeight: 'bold' }} width={80} />
          <RechartsTooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
          
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {dataArray.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#ef4444' : '#3b82f6'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
