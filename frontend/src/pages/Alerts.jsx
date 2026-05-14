import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { toast } from 'react-toastify';
import { SendHorizonal, CheckCircle2, Loader2, Trash2, AlertTriangle, X } from 'lucide-react';

export default function Alerts() {
  const queryClient = useQueryClient();
  const [editingVillage, setEditingVillage] = useState(null);
  const [editThreshold, setEditThreshold] = useState(150);
  const [editActive, setEditActive] = useState(true);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null); // dialog chi tiết

  // Fetch configs
  const { data: configs, isLoading: loadingConfigs } = useQuery({
    queryKey: ['alertConfigs'],
    queryFn: async () => {
      const res = await api.get('/alerts/config');
      return res.data;
    }
  });

  // Fetch active alerts
  const { data: activeAlerts, isLoading: loadingAlerts } = useQuery({
    queryKey: ['activeAlerts'],
    queryFn: async () => {
      const res = await api.get('/alerts/active');
      return res.data.data;
    }
  });

  // Approve Mutation
  const approveMutation = useMutation({
    mutationFn: async (alertId) => {
      return api.post(`/alerts/approve/${alertId}`);
    },
    onSuccess: (_, alertId) => {
      toast.success('✅ Đã phê duyệt và gửi cảnh báo đến người dân!');
      queryClient.invalidateQueries(['activeAlerts']);
    },
    onError: (err) => {
      toast.error('Lỗi khi phê duyệt: ' + (err.response?.data?.detail || err.message));
    }
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (alertId) => api.delete(`/alerts/${alertId}`),
    onSuccess: () => {
      toast.success('🗑️ Đã xóa cảnh báo thành công');
      setConfirmDeleteId(null);
      queryClient.invalidateQueries(['activeAlerts']);
    },
    onError: (err) => {
      toast.error('Lỗi khi xóa: ' + (err.response?.data?.detail || err.message));
    }
  });

  // Update Config Mutation
  const updateConfigMutation = useMutation({
    mutationFn: async ({ village_name, data }) => {
      return api.post(`/alerts/config/${encodeURIComponent(village_name)}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['alertConfigs']);
      toast.success('Cập nhật cấu hình cảnh báo thành công!');
      setEditingVillage(null);
    },
    onError: (error) => {
      toast.error('Lỗi khi cập nhật cấu hình: ' + error.message);
    }
  });

  const handleEditClick = (config) => {
    setEditingVillage(config.village_name);
    setEditThreshold(config.aqi_threshold);
    setEditActive(config.is_active);
  };

  const handleSave = async () => {
    // 1. Cập nhật cấu hình cảnh báo (ngưỡng AQI, bật/tắt alert)
    updateConfigMutation.mutate({
      village_name: editingVillage,
      data: {
        aqi_threshold: editThreshold,
        is_active: editActive
      }
    });

    // 2. Đồng bộ trạng thái hoạt động của trạm trên bản đồ
    // Tìm config hiện tại để so sánh xem người dùng có vừa thay đổi trạng thái không
    const currentConfig = configs.find(c => c.village_name === editingVillage);
    if (currentConfig && currentConfig.is_active !== editActive) {
      try {
        await api.patch(`/villages/${editingVillage}/toggle`);
        // Refresh lại dữ liệu bản đồ nếu cần (tùy vào các component khác dùng chung cache)
        queryClient.invalidateQueries(['aqiCurrent']);
      } catch (err) {
        console.error("Lỗi khi đồng bộ trạng thái trạm:", err);
      }
    }
  };

  return (
    <>
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
          Hệ thống Cảnh báo tự động
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Quản lý các ngưỡng cảnh báo ô nhiễm không khí cho 18 làng nghề.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Cột 1: Cảnh báo đang kích hoạt (Lịch sử gần đây) */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-500/30 rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-500 animate-ping"></div>
              <h3 className="text-lg font-bold text-red-700 dark:text-red-400">Cảnh báo gần đây</h3>
            </div>
            
            <div className="space-y-3">
              {loadingAlerts ? (
                <div className="text-sm text-gray-500">Đang tải...</div>
              ) : activeAlerts?.length > 0 ? (
                activeAlerts.map((alert, idx) => (
                  <motion.div
                    key={alert.id ?? idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`p-3 rounded-xl border shadow-sm backdrop-blur-sm cursor-pointer hover:shadow-md transition-shadow ${
                      alert.is_approved
                        ? 'bg-green-50/80 dark:bg-green-900/20 border-green-200 dark:border-green-500/30'
                        : 'bg-white/60 dark:bg-gray-800/60 border-red-200 dark:border-red-500/20'
                    }`}
                    onClick={() => setSelectedAlert(alert)}
                  >
                    {/* Header card */}
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-bold text-gray-900 dark:text-gray-100">{alert.village_name}</span>
                      <span className="text-xs text-gray-400">
                        {new Date(alert.timestamp).toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })}
                      </span>
                    </div>

                    {/* Nội dung cảnh báo */}
                    <p className="text-sm text-red-600 dark:text-red-400 mb-2">{alert.message}</p>

                    {/* AQI Badge */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="text-xs bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 px-2 py-1 rounded-lg font-medium">
                        AQI: {alert.aqi_value} / Ngưỡng: {alert.threshold_value}
                      </span>

                      <div className="flex items-center gap-1.5">
                        {/* Nút Phê duyệt */}
                        {alert.is_approved ? (
                          <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-semibold bg-green-100 dark:bg-green-500/20 px-2.5 py-1 rounded-lg">
                            <CheckCircle2 size={13}/> Đã gửi dân
                          </span>
                        ) : (
                          <button
                            onClick={() => approveMutation.mutate(alert.id)}
                            disabled={approveMutation.isPending}
                            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 disabled:opacity-60 text-white transition-all shadow-sm shadow-blue-500/30"
                          >
                            {approveMutation.isPending ? (
                              <Loader2 size={12} className="animate-spin"/>
                            ) : (
                              <SendHorizonal size={12}/>
                            )}
                            Phê duyệt & Gửi
                          </button>
                        )}

                        {/* Nút Xóa */}
                        <button
                          onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(alert.id); }}
                          title="Xóa cảnh báo"
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                        >
                          <Trash2 size={14}/>
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="text-sm text-green-600 dark:text-green-400 flex items-center gap-2 p-3 bg-green-50 dark:bg-green-500/10 rounded-lg">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Hiện tại không có cảnh báo nào.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Cột 2: Bảng cấu hình */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">Cấu hình Ngưỡng (Admin)</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700/50 dark:text-gray-400">
                <tr>
                  <th scope="col" className="px-6 py-3">Làng nghề</th>
                  <th scope="col" className="px-6 py-3">Ngưỡng AQI Báo động</th>
                  <th scope="col" className="px-6 py-3">Trạng thái</th>
                  <th scope="col" className="px-6 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {loadingConfigs ? (
                  <tr><td colSpan="4" className="px-6 py-4 text-center">Đang tải...</td></tr>
                ) : (
                  configs?.map((config) => (
                    <tr key={config.village_name} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/30">
                      <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                        {config.village_name}
                      </td>
                      
                      <td className="px-6 py-4">
                        {editingVillage === config.village_name ? (
                          <input 
                            type="number" 
                            value={editThreshold} 
                            onChange={(e) => setEditThreshold(Number(e.target.value))}
                            className="w-24 px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-blue-500 outline-none"
                          />
                        ) : (
                          <span className={`px-2 py-1 rounded font-bold ${config.aqi_threshold >= 150 ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600'}`}>
                            {config.aqi_threshold}
                          </span>
                        )}
                      </td>
                      
                      <td className="px-6 py-4">
                        {editingVillage === config.village_name ? (
                          <select 
                            value={editActive ? "true" : "false"}
                            onChange={(e) => setEditActive(e.target.value === "true")}
                            className="px-2 py-1 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white outline-none"
                          >
                            <option value="true">Bật</option>
                            <option value="false">Tắt</option>
                          </select>
                        ) : (
                          <span className={`flex items-center gap-1 ${config.is_active ? 'text-green-500' : 'text-gray-400'}`}>
                            <div className={`w-2 h-2 rounded-full ${config.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                            {config.is_active ? 'Đang bật' : 'Đã tắt'}
                          </span>
                        )}
                      </td>
                      
                      <td className="px-6 py-4 text-right">
                        {editingVillage === config.village_name ? (
                          <div className="flex justify-end gap-2">
                            <button onClick={handleSave} className="font-medium text-blue-600 dark:text-blue-500 hover:underline">Lưu</button>
                            <button onClick={() => setEditingVillage(null)} className="font-medium text-gray-500 hover:underline">Hủy</button>
                          </div>
                        ) : (
                          <button onClick={() => handleEditClick(config)} className="font-medium text-blue-600 dark:text-blue-500 hover:underline">
                            Chỉnh sửa
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </motion.div>

    {/* ── Dialog Chi tiết Cảnh báo ───────────────────────────────────────── */}
    <AnimatePresence>
      {selectedAlert && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4"
          onClick={() => setSelectedAlert(null)}
        >
          <motion.div
            initial={{ scale: 0.92, opacity: 0, y: 15 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.92, opacity: 0, y: 15 }}
            transition={{ type: 'spring', damping: 22 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md border border-gray-100 dark:border-gray-700 overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className={`px-6 py-5 flex items-start justify-between ${
              selectedAlert.is_approved
                ? 'bg-green-50 dark:bg-green-900/30 border-b border-green-100 dark:border-green-700'
                : 'bg-red-50 dark:bg-red-900/30 border-b border-red-100 dark:border-red-700'
            }`}>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">{selectedAlert.village_name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Ghi nhận lúc {new Date(selectedAlert.timestamp).toLocaleString('vi-VN', { weekday:'long', day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })}
                </p>
              </div>
              <button onClick={() => setSelectedAlert(null)}
                className="p-1.5 rounded-full hover:bg-black/10 text-gray-400 hover:text-gray-600 transition-colors">
                <X size={18}/>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4">
              {/* AQI lớn */}
              <div className="flex items-center gap-4">
                <div className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center font-black shadow-sm ${
                  selectedAlert.aqi_value > 300 ? 'bg-rose-100 text-rose-700' :
                  selectedAlert.aqi_value > 200 ? 'bg-purple-100 text-purple-700' :
                  selectedAlert.aqi_value > 150 ? 'bg-red-100 text-red-700' :
                  selectedAlert.aqi_value > 100 ? 'bg-orange-100 text-orange-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  <span className="text-3xl leading-none">{Math.round(selectedAlert.aqi_value)}</span>
                  <span className="text-xs font-medium opacity-70">AQI</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Ngưỡng kích hoạt</p>
                  <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">{selectedAlert.threshold_value}</p>
                  <p className="text-xs text-gray-400">Vượt {(selectedAlert.aqi_value - selectedAlert.threshold_value).toFixed(1)} đơn vị</p>
                </div>
              </div>

              {/* Nội dung cảnh báo */}
              <div className="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-xl p-4">
                <p className="text-sm font-medium text-red-600 dark:text-red-400 leading-relaxed">{selectedAlert.message}</p>
              </div>

              {/* Trạng thái */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3">
                  <p className="text-xs text-gray-400 mb-1">Trạng thái</p>
                  {selectedAlert.is_approved ? (
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-green-600 dark:text-green-400">
                      <CheckCircle2 size={15}/> Đã phê duyệt
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-orange-500">
                      <Loader2 size={15}/> Chờ duyệt
                    </span>
                  )}
                </div>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3">
                  <p className="text-xs text-gray-400 mb-1">Thời gian duyệt</p>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {selectedAlert.approved_at
                      ? new Date(selectedAlert.approved_at).toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' })
                      : '—'}
                  </p>
                </div>
              </div>
            </div>

            {/* Footer actions */}
            <div className="px-6 pb-5 flex gap-2">
              {!selectedAlert.is_approved && (
                <button
                  onClick={() => { approveMutation.mutate(selectedAlert.id); setSelectedAlert(null); }}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold transition-colors shadow-sm shadow-blue-500/30"
                >
                  <SendHorizonal size={15}/> Phê duyệt & Gửi dân
                </button>
              )}
              <button
                onClick={() => { setSelectedAlert(null); setConfirmDeleteId(selectedAlert.id); }}
                className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 text-sm font-medium transition-colors"
              >
                <Trash2 size={15}/> Xóa
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>

    {/* ── Dialog xác nhận xóa ─────────────────────────────────────────── */}
    <AnimatePresence>
      {confirmDeleteId && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm px-4"
          onClick={() => setConfirmDeleteId(null)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 10 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 10 }}
            transition={{ type: 'spring', damping: 20 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-sm w-full border border-gray-100 dark:border-gray-700"
            onClick={e => e.stopPropagation()}
          >
            {/* Icon */}
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-500/20 mx-auto mb-4">
              <AlertTriangle className="text-red-500" size={24}/>
            </div>

            {/* Nội dung */}
            <h3 className="text-lg font-bold text-gray-900 dark:text-white text-center mb-2">
              Xác nhận xóa cảnh báo?
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-6">
              Cảnh báo này sẽ bị xóa vĩnh viễn khỏi hệ thống và không thể khôi phục.
              Nếu đã gửi đến người dân, họ sẽ không còn thấy cảnh báo này nữa.
            </p>

            {/* Nút hành động */}
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Hủy
              </button>
              <button
                onClick={() => deleteMutation.mutate(confirmDeleteId)}
                disabled={deleteMutation.isPending}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 disabled:opacity-60 text-white text-sm font-semibold transition-colors shadow-sm shadow-red-500/30"
              >
                {deleteMutation.isPending ? (
                  <Loader2 size={15} className="animate-spin"/>
                ) : (
                  <Trash2 size={15}/>
                )}
                Xóa cảnh báo
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
    </>
  );
}
