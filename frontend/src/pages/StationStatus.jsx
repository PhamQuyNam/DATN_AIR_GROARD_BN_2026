import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Wifi, WifiOff, Clock, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

const AQI_COLORS = {
  'Tốt':       { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/30' },
  'Trung bình':{ bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  'Kém':       { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
  'Xấu':       { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30' },
  'Rất xấu':   { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/30' },
  'Nguy hại':  { bg: 'bg-rose-900/40', text: 'text-rose-300', border: 'border-rose-500/30' },
};

export default function StationStatus() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['stationStatus'],
    queryFn: async () => {
      const res = await api.get('/map/status');
      return res.data;
    },
    refetchInterval: 30000, // Tự cập nhật mỗi 30 giây
  });

  const stations = data?.stations || [];
  const onlineCount = data?.online_count || 0;
  const offlineCount = data?.offline_count || 0;
  const total = data?.total || 0;
  const onlinePct = total > 0 ? Math.round((onlineCount / total) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            Giám sát Trạng thái Trạm
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Theo dõi tình trạng kết nối và dữ liệu của 18 làng nghề Bắc Ninh
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-400 rounded-xl text-sm font-medium transition-colors"
        >
          <Activity size={16} />
          Làm mới
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-500/15 flex items-center justify-center">
              <CheckCircle className="text-green-500" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{onlineCount}</p>
              <p className="text-sm text-gray-500">Trạm Online</p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 rounded-full transition-all duration-700" style={{ width: `${onlinePct}%` }} />
          </div>
          <p className="text-xs text-gray-400 mt-1">{onlinePct}% hoạt động bình thường</p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center">
              <WifiOff className="text-red-500" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{offlineCount}</p>
              <p className="text-sm text-gray-500">Trạm Offline</p>
            </div>
          </div>
          {offlineCount > 0 && (
            <div className="mt-3 flex items-center gap-1.5 text-xs text-red-400">
              <AlertTriangle size={12} />
              Cần kiểm tra ngay
            </div>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center">
              <Wifi className="text-blue-500" size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{total}</p>
              <p className="text-sm text-gray-500">Tổng số Trạm</p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3">Tự cập nhật mỗi 30 giây</p>
        </div>
      </div>

      {/* Bảng trạng thái */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h3 className="font-bold text-gray-900 dark:text-white">Chi tiết từng trạm</h3>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-10 text-center text-gray-500">Đang tải dữ liệu...</div>
          ) : (
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 dark:text-gray-400 uppercase bg-gray-50 dark:bg-gray-700/40">
                <tr>
                  <th className="px-5 py-3">Trạm</th>
                  <th className="px-5 py-3">Trạng thái</th>
                  <th className="px-5 py-3">AQI hiện tại</th>
                  <th className="px-5 py-3">Mức độ</th>
                  <th className="px-5 py-3">Cập nhật lần cuối</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {stations.map((s, idx) => {
                  const aqiColor = AQI_COLORS[s.current_level] || AQI_COLORS['Trung bình'];
                  return (
                    <motion.tr
                      key={s.village_name}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      {/* Tên trạm */}
                      <td className="px-5 py-4">
                        <div className="font-semibold text-gray-900 dark:text-white">{s.village_name}</div>
                        <div className="text-xs text-gray-400">{s.location}</div>
                      </td>

                      {/* Trạng thái */}
                      <td className="px-5 py-4">
                        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
                          s.is_online
                            ? 'bg-green-500/15 text-green-500 border border-green-500/30'
                            : 'bg-red-500/15 text-red-400 border border-red-500/30'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${s.is_online ? 'bg-green-500 animate-pulse' : 'bg-red-400'}`} />
                          {s.is_online ? 'Online' : 'Offline'}
                        </div>
                      </td>

                      {/* AQI */}
                      <td className="px-5 py-4">
                        {s.current_aqi != null ? (
                          <span className={`text-lg font-bold ${aqiColor.text}`}>{s.current_aqi}</span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>

                      {/* Mức độ */}
                      <td className="px-5 py-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium border ${aqiColor.bg} ${aqiColor.text} ${aqiColor.border}`}>
                          {s.current_level}
                        </span>
                      </td>

                      {/* Thời gian */}
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
                          <Clock size={13} />
                          <span className="text-xs">{s.time_ago}</span>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </motion.div>
  );
}
