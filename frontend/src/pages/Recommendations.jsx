import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { toast } from 'react-toastify';
import { Send, MessageSquare, MapPin, Clock, ChevronDown } from 'lucide-react';

const SUGGESTION_TEMPLATES = [
  "⚠️ AQI đang ở mức báo động. Người dân không nên ra ngoài, đặc biệt trẻ em và người cao tuổi. Các cơ sở sản xuất cần tạm dừng hoặc giảm công suất.",
  "😷 Không khí ô nhiễm. Khuyến nghị đeo khẩu trang N95 khi ra ngoài. Đóng cửa sổ để giảm thiểu bụi mịn PM2.5 vào nhà.",
  "🏭 Yêu cầu các lò nung, xưởng sản xuất giảm 50% công suất trong 24 giờ tới để cải thiện chất lượng không khí.",
  "🌬️ Gió thuận lợi giúp phát tán ô nhiễm. Tuy nhiên, vẫn cần theo dõi chỉ số AQI trong vòng 6 giờ tới.",
  "✅ Chất lượng không khí đã cải thiện. Người dân có thể hoạt động bình thường nhưng cần tiếp tục theo dõi.",
];

export default function Recommendations() {
  const queryClient = useQueryClient();
  const [selectedVillage, setSelectedVillage] = useState('');
  const [content, setContent] = useState('');

  // Fetch danh sách làng nghề
  const { data: villagesData } = useQuery({
    queryKey: ['villages'],
    queryFn: async () => {
      const res = await api.get('/villages');
      return res.data;
    }
  });

  // Fetch lịch sử khuyến nghị
  const { data: recsData } = useQuery({
    queryKey: ['allRecommendations'],
    queryFn: async () => {
      const res = await api.get('/alerts/recommend');
      return res.data.data || [];
    },
    refetchInterval: 30000,
  });

  // Mutation gửi khuyến nghị
  const sendMutation = useMutation({
    mutationFn: async () => {
      return api.post('/alerts/recommend', {
        village_name: selectedVillage,
        content: content
      });
    },
    onSuccess: () => {
      toast.success(`✅ Đã gửi khuyến nghị đến ${selectedVillage}!`);
      setContent('');
      setSelectedVillage('');
      queryClient.invalidateQueries(['allRecommendations']);
    },
    onError: (err) => {
      toast.error('Lỗi: ' + (err.response?.data?.detail || err.message));
    }
  });

  const villages = villagesData || [];
  const recommendations = recsData || [];

  const handleSend = () => {
    if (!selectedVillage) { toast.warning('Vui lòng chọn làng nghề'); return; }
    if (!content.trim()) { toast.warning('Vui lòng nhập nội dung khuyến nghị'); return; }
    sendMutation.mutate();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
          Phê duyệt & Gửi Khuyến nghị
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Soạn thảo và gửi thông điệp bảo vệ sức khỏe đến người dân các làng nghề.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* === Cột trái: Form soạn thảo === */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Send size={18} className="text-blue-500" />
              Soạn khuyến nghị mới
            </h3>

            {/* Chọn làng nghề */}
            <div className="space-y-1.5 mb-4">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Làng nghề mục tiêu</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <select
                  value={selectedVillage}
                  onChange={e => setSelectedVillage(e.target.value)}
                  className="w-full pl-9 pr-10 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                >
                  <option value="">— Chọn làng nghề —</option>
                  {villages.map(v => (
                    <option key={v.name} value={v.name}>{v.name}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
              </div>
            </div>

            {/* Nội dung khuyến nghị */}
            <div className="space-y-1.5 mb-4">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Nội dung</label>
              <textarea
                value={content}
                onChange={e => setContent(e.target.value)}
                rows={5}
                placeholder="Soạn thảo nội dung khuyến nghị tại đây..."
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              />
              <p className="text-xs text-gray-400 text-right">{content.length} ký tự</p>
            </div>

            {/* Nút gửi */}
            <button
              onClick={handleSend}
              disabled={sendMutation.isPending}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
            >
              {sendMutation.isPending ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Send size={16} />
              )}
              Gửi Khuyến nghị
            </button>
          </div>

          {/* Template nhanh */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
            <h4 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-3">💡 Mẫu khuyến nghị nhanh</h4>
            <div className="space-y-2">
              {SUGGESTION_TEMPLATES.map((tpl, i) => (
                <button
                  key={i}
                  onClick={() => setContent(tpl)}
                  className="w-full text-left text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 hover:bg-blue-50 dark:hover:bg-blue-500/10 hover:text-blue-600 dark:hover:text-blue-400 p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-blue-300 transition-all line-clamp-2"
                >
                  {tpl}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* === Cột phải: Lịch sử gửi === */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
            <MessageSquare size={18} className="text-green-500" />
            <h3 className="font-bold text-gray-900 dark:text-white">Lịch sử đã gửi</h3>
            <span className="ml-auto text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-0.5 rounded-full">
              {recommendations.length} khuyến nghị
            </span>
          </div>

          <div className="overflow-y-auto max-h-[550px] divide-y divide-gray-100 dark:divide-gray-700">
            {recommendations.length === 0 ? (
              <div className="p-10 text-center text-gray-400">
                <MessageSquare size={40} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Chưa có khuyến nghị nào được gửi.</p>
              </div>
            ) : (
              recommendations.map((rec, idx) => (
                <motion.div
                  key={rec.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="p-5 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-blue-500/10 text-blue-500 px-2.5 py-1 rounded-full border border-blue-500/20">
                      <MapPin size={11} />
                      {rec.village_name}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <Clock size={11} />
                      {new Date(rec.created_at).toLocaleString('vi-VN', {
                        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{rec.content}</p>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
