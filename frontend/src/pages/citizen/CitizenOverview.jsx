import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Star, AlertTriangle, MessageSquare, Wind, Thermometer, Droplets, ArrowRight } from 'lucide-react';
import api from '../../services/api';

const getAqiColor = (aqi) => {
  if (!aqi) return '#6b7280';
  if (aqi <= 50) return '#22c55e'; if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316'; if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#a855f7'; return '#7f1d1d';
};
const getAqiBg = (aqi) => {
  if (!aqi) return 'bg-gray-500/10';
  if (aqi <= 50) return 'bg-green-500/10'; if (aqi <= 100) return 'bg-yellow-500/10';
  if (aqi <= 150) return 'bg-orange-500/10'; if (aqi <= 200) return 'bg-red-500/10';
  if (aqi <= 300) return 'bg-purple-500/10'; return 'bg-rose-900/20';
};
const getAdvice = (level) => {
  const advice = {
    'Tốt': 'Không khí trong lành. Tận hưởng các hoạt động ngoài trời!',
    'Trung bình': 'Chất lượng khá. Người nhạy cảm nên hạn chế thời gian ở ngoài.',
    'Kém': 'Hạn chế ra ngoài. Đeo khẩu trang nếu cần thiết.',
    'Xấu': 'Tránh ra ngoài. Đóng cửa sổ, dùng máy lọc không khí.',
    'Rất xấu': 'Nguy hiểm! Ở trong nhà, tránh mọi hoạt động ngoài trời.',
    'Nguy hại': 'Khẩn cấp! Không ra ngoài, liên hệ cơ quan y tế nếu cần.',
  };
  return advice[level] || 'Không có dữ liệu.';
};

export default function CitizenOverview() {
  const { data, isLoading } = useQuery({
    queryKey: ['citizenFeed'],
    queryFn: async () => {
      const res = await api.get('/citizen/feed');
      return res.data;
    },
    refetchInterval: 60000,
  });

  const stations = data?.stations || [];
  const alertStations = stations.filter(s => s.all_alerts && s.all_alerts.length > 0);

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Chào mừng */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-1">
          Xin chào, {data?.user?.full_name || '...'}! 👋
        </h1>
        <p className="text-blue-200 text-sm">
          Theo dõi {data?.favorite_count || 0} trạm quan trắc yêu thích của bạn.
        </p>
        {data?.favorite_count === 0 && (
          <Link to="/citizen/stations"
            className="mt-3 inline-flex items-center gap-1.5 bg-white/20 hover:bg-white/30 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors">
            <Star size={15}/> Chọn trạm quan tâm ngay <ArrowRight size={14}/>
          </Link>
        )}
      </div>

      {/* Cảnh báo nổi bật */}
      {alertStations.length > 0 && (
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="text-red-500 animate-pulse" size={20}/>
            <h3 className="font-bold text-red-700 dark:text-red-400">Cảnh báo ô nhiễm tại {alertStations.length} trạm</h3>
          </div>
          <div className="space-y-2">
            {alertStations.map(s => (
              <div key={s.village_name} className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0"/>
                <div>
                  <span className="font-semibold">{s.village_name}:</span> {s.alert_message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Danh sách trạm */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Đang tải dữ liệu...</div>
      ) : stations.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
          <Star size={48} className="mx-auto text-gray-300 mb-4"/>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">Chưa chọn trạm quan tâm</h3>
          <p className="text-gray-500 text-sm mb-4">Hãy chọn các làng nghề gần bạn để nhận thông tin AQI và cảnh báo.</p>
          <Link to="/citizen/stations"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-medium transition-colors">
            <Star size={16}/> Chọn trạm ngay
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stations.map((s, i) => (
            <motion.div key={s.village_name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
              className={`rounded-2xl border p-5 shadow-sm ${s.has_alert ? 'border-red-300 dark:border-red-500/40 bg-red-50/50 dark:bg-red-500/5' : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800'}`}>

              {/* Header card */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white">{s.village_name}</h3>
                  {s.last_updated && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(s.last_updated).toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}
                    </p>
                  )}
                </div>
                {/* AQI Badge lớn */}
                <div className={`${getAqiBg(s.aqi)} rounded-2xl px-4 py-2 text-center min-w-[80px]`}>
                  <p className="text-2xl font-black" style={{ color: getAqiColor(s.aqi) }}>{s.aqi ?? '—'}</p>
                  <p className="text-xs font-semibold" style={{ color: getAqiColor(s.aqi) }}>{s.level}</p>
                </div>
              </div>

              {/* Chỉ số phụ */}
              <div className="flex gap-4 mb-4">
                {s.pm25 != null && (
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Wind size={12}/> PM2.5: <span className="font-semibold text-gray-700 dark:text-gray-300">{s.pm25.toFixed(1)}</span>
                  </div>
                )}
                {s.temperature != null && (
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Thermometer size={12}/> <span className="font-semibold text-gray-700 dark:text-gray-300">{s.temperature.toFixed(1)}°C</span>
                  </div>
                )}
              </div>

              {/* Lời khuyên */}
              <div className={`rounded-xl p-3 text-xs ${getAqiBg(s.aqi)}`}>
                <p style={{ color: getAqiColor(s.aqi) }}>{getAdvice(s.level)}</p>
              </div>

              {/* Khuyến nghị từ cơ quan */}
              {s.recommendation && (
                <div className="mt-3 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-xl p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <MessageSquare size={12} className="text-blue-500"/>
                    <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Khuyến nghị từ Sở TN&MT</span>
                  </div>
                  <p className="text-xs text-blue-700 dark:text-blue-300">{s.recommendation}</p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
