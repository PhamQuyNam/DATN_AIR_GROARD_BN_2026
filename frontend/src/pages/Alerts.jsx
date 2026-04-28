import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function Alerts() {
  const queryClient = useQueryClient();
  const [editingVillage, setEditingVillage] = useState(null);
  const [editThreshold, setEditThreshold] = useState(150);
  const [editActive, setEditActive] = useState(true);

  // Fetch configs
  const { data: configs, isLoading: loadingConfigs } = useQuery({
    queryKey: ['alertConfigs'],
    queryFn: async () => {
      const res = await api.get('/alert/config');
      return res.data;
    }
  });

  // Fetch active alerts
  const { data: activeAlerts, isLoading: loadingAlerts } = useQuery({
    queryKey: ['activeAlerts'],
    queryFn: async () => {
      const res = await api.get('/alert/active');
      return res.data.data;
    }
  });

  // Update Config Mutation
  const updateConfigMutation = useMutation({
    mutationFn: async ({ village_name, data }) => {
      return api.post(`/alert/config/${encodeURIComponent(village_name)}`, data);
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

  const handleSave = () => {
    updateConfigMutation.mutate({
      village_name: editingVillage,
      data: {
        aqi_threshold: editThreshold,
        is_active: editActive
      }
    });
  };

  return (
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
                  <div key={idx} className="bg-white/60 dark:bg-gray-800/60 p-3 rounded-lg border border-red-200 dark:border-red-500/20 shadow-sm backdrop-blur-sm">
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-gray-900 dark:text-gray-100">{alert.village_name}</span>
                      <span className="text-xs text-gray-500">{new Date(alert.timestamp).toLocaleTimeString('vi-VN')}</span>
                    </div>
                    <p className="text-sm text-red-600 mt-1">{alert.message}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 px-2 py-1 rounded">
                        AQI: {alert.aqi_value} (Ngưỡng: {alert.threshold_value})
                      </span>
                    </div>
                  </div>
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
  );
}
