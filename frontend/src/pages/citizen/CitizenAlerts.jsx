import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, MessageSquare, Bell, Clock, ShieldCheck } from 'lucide-react';
import api from '../../services/api';

const getAqiColor = (aqi) => {
  if (!aqi) return '#6b7280';
  if (aqi <= 50) return '#22c55e'; if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316'; if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#a855f7'; return '#7f1d1d';
};

export default function CitizenAlerts() {
  const { data, isLoading } = useQuery({
    queryKey: ['citizenFeed'],
    queryFn: async () => {
      const res = await api.get('/citizen/feed');
      return res.data;
    },
    refetchInterval: 60000,
  });

  const stations = data?.stations || [];

  // Tổng hợp tất cả cảnh báo đã duyệt từ mọi trạm
  const allApprovedAlerts = stations.flatMap(s =>
    (s.all_alerts || []).map(a => ({ ...a, village_name: s.village_name }))
  );

  // Tổng hợp khüyến nghị: flatten tất cả all_recommendations từ mọi trạm
  const allRecommendations = stations.flatMap(s =>
    (s.all_recommendations || []).map(r => ({ ...r, village_name: s.village_name }))
  );

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Cảnh báo & Khuyến nghị</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
          Thông tin cảnh báo đã được xác nhận và khuyến nghị sức khỏe từ Sở TN&MT Bắc Ninh.
        </p>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Đang tải...</div>
      ) : stations.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700">
          <Bell size={40} className="mx-auto text-gray-300 mb-3"/>
          <p className="text-gray-500">Chưa theo dõi trạm nào. Hãy chọn trạm quan tâm trước.</p>
        </div>
      ) : (
        <div className="space-y-6">

          {/* ── Cảnh báo ô nhiễm đã được Admin duyệt ───────────────────────────── */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
              <AlertTriangle className="text-red-500" size={18}/>
              <h3 className="font-bold text-gray-900 dark:text-white">Cảnh báo ô nhiễm</h3>
              <span className="ml-1 text-xs text-gray-400">(Đã được Sở TN&MT xác nhận)</span>
              {allApprovedAlerts.length > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {allApprovedAlerts.length}
                </span>
              )}
            </div>

            {allApprovedAlerts.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <ShieldCheck size={36} className="mx-auto mb-2 text-green-400"/>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">Không có cảnh báo nào từ các trạm bạn theo dõi.</p>
                <p className="text-xs mt-1">Cảnh báo chỉ xuất hiện sau khi được Sở TN&MT xác nhận và phê duyệt.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {allApprovedAlerts.map((alert, i) => (
                  <motion.div key={i}
                    initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                    className="p-5">
                    <div className="flex items-start gap-3">
                      {/* AQI badge */}
                      <div className="w-12 h-12 rounded-xl shrink-0 flex flex-col items-center justify-center font-black text-sm shadow-sm"
                        style={{ background: getAqiColor(alert.aqi_value) + '20', color: getAqiColor(alert.aqi_value) }}>
                        <span className="text-lg leading-none">{Math.round(alert.aqi_value)}</span>
                        <span className="text-[10px] leading-none opacity-70">AQI</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2 mb-1">
                          <span className="font-bold text-gray-900 dark:text-white">{alert.village_name}</span>
                          <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{ background: getAqiColor(alert.aqi_value) + '20', color: getAqiColor(alert.aqi_value) }}>
                            Vượt ngưỡng {alert.threshold_value}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{alert.message}</p>
                        {alert.approved_at && (
                          <div className="flex items-center gap-1 mt-2 text-xs text-green-600 dark:text-green-400">
                            <ShieldCheck size={12}/>
                            <span>Sở TN&MT xác nhận lúc {new Date(alert.approved_at).toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          {/* ── Khuyến nghị sức khỏe từ Sở TN&MT ─────────────────────────────────── */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
              <MessageSquare className="text-blue-500" size={18}/>
              <h3 className="font-bold text-gray-900 dark:text-white">Khuyến nghị sức khỏe từ Sở TN&MT</h3>
              {allRecommendations.length > 0 && (
                <span className="ml-auto bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">{allRecommendations.length}</span>
              )}
            </div>
            {allRecommendations.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <MessageSquare size={32} className="mx-auto mb-2 opacity-30"/>
                <p className="text-sm">Chưa có khuyến nghị nào dành cho trạm bạn theo dõi.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {allRecommendations.map((r, i) => (
                  <motion.div key={i}
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                    className="p-5">
                    <div className="flex items-center justify-between mb-2">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-blue-500/10 text-blue-500 px-2.5 py-1 rounded-full border border-blue-500/20">
                        📍 {r.village_name}
                      </span>
                      {r.created_at && (
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <Clock size={11}/>
                          {new Date(r.created_at).toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{r.content}</p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}
    </motion.div>
  );
}
