import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Star, StarOff, MapPin, CheckCircle, Search } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../services/api';

const ALL_VILLAGES = [
  { name: 'Đa Hội', location: 'P. Châu Khê, TP. Từ Sơn' },
  { name: 'Đồng Kỵ', location: 'P. Đồng Kỵ, TP. Từ Sơn' },
  { name: 'Phù Khê', location: 'P. Phù Khê, TP. Từ Sơn' },
  { name: 'Hương Mạc', location: 'P. Hương Mạc, TP. Từ Sơn' },
  { name: 'Đình Bảng', location: 'P. Đình Bảng, TP. Từ Sơn' },
  { name: 'Văn Môn', location: 'X. Văn Môn, H. Yên Phong' },
  { name: 'Vọng Nguyệt', location: 'X. Tam Giang, H. Yên Phong' },
  { name: 'Phong Khê', location: 'P. Phong Khê, TP. Bắc Ninh' },
  { name: 'Khắc Niệm', location: 'P. Khắc Niệm, TP. Bắc Ninh' },
  { name: 'Châm Khê', location: 'P. Phong Khê, TP. Bắc Ninh' },
  { name: 'Phù Lãng', location: 'X. Phù Lãng, TX. Quế Võ' },
  { name: 'Quả Cảm', location: 'P. Hòa Long, TP. Bắc Ninh' },
  { name: 'Đại Bái', location: 'X. Đại Bái, H. Gia Bình' },
  { name: 'Xuân Lai', location: 'X. Xuân Lai, H. Gia Bình' },
  { name: 'Môn Quảng', location: 'X. Quảng Phú, H. Lương Tài' },
  { name: 'Đông Hồ', location: 'X. Song Hồ, TX. Thuận Thành' },
  { name: 'Thanh Hoài', location: 'X. Thanh Khương, Thuận Thành' },
  { name: 'Tam Tảo', location: 'X. Phú Lâm, H. Tiên Du' },
];

export default function CitizenStations() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');

  const { data: favsData } = useQuery({
    queryKey: ['citizenFavorites'],
    queryFn: async () => {
      const res = await api.get('/citizen/favorites');
      return res.data.favorites || [];
    }
  });

  const favorites = favsData || [];

  const addMutation = useMutation({
    mutationFn: (village) => api.post(`/citizen/favorites/${encodeURIComponent(village)}`),
    onSuccess: (_, village) => {
      toast.success(`⭐ Đã thêm ${village} vào danh sách quan tâm`);
      queryClient.invalidateQueries(['citizenFavorites']);
      queryClient.invalidateQueries(['citizenFeed']);
    }
  });

  const removeMutation = useMutation({
    mutationFn: (village) => api.delete(`/citizen/favorites/${encodeURIComponent(village)}`),
    onSuccess: (_, village) => {
      toast.info(`Đã bỏ ${village} khỏi danh sách`);
      queryClient.invalidateQueries(['citizenFavorites']);
      queryClient.invalidateQueries(['citizenFeed']);
    }
  });

  const toggleFavorite = (village) => {
    if (favorites.includes(village)) {
      removeMutation.mutate(village);
    } else {
      addMutation.mutate(village);
    }
  };

  const filtered = ALL_VILLAGES.filter(v =>
    v.name.toLowerCase().includes(search.toLowerCase()) ||
    v.location.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Trạm quan tâm</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
          Chọn các làng nghề gần bạn để nhận thông tin AQI và cảnh báo cá nhân hóa.
        </p>
      </div>

      {/* Thống kê đã chọn */}
      <div className="bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-2xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Star className="text-blue-500" size={20}/>
          <span className="font-semibold text-blue-700 dark:text-blue-300">
            Đang theo dõi {favorites.length} / {ALL_VILLAGES.length} trạm
          </span>
        </div>
        {favorites.length > 0 && (
          <span className="text-xs text-blue-500 bg-blue-100 dark:bg-blue-500/20 px-2.5 py-1 rounded-full font-medium">
            {favorites.join(', ')}
          </span>
        )}
      </div>

      {/* Tìm kiếm */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16}/>
        <input type="text" value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Tìm kiếm làng nghề..."
          className="w-full pl-9 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"/>
      </div>

      {/* Lưới 18 làng */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filtered.map((village, i) => {
          const isFav = favorites.includes(village.name);
          return (
            <motion.div key={village.name} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
              className={`flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer ${
                isFav
                  ? 'bg-blue-50 dark:bg-blue-500/10 border-blue-300 dark:border-blue-500/40'
                  : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-500/30'
              }`}
              onClick={() => toggleFavorite(village.name)}
            >
              <div className="flex items-start gap-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${isFav ? 'bg-blue-500/20' : 'bg-gray-100 dark:bg-gray-700'}`}>
                  <MapPin size={16} className={isFav ? 'text-blue-500' : 'text-gray-400'}/>
                </div>
                <div>
                  <p className={`font-semibold text-sm ${isFav ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'}`}>
                    {village.name}
                  </p>
                  <p className="text-xs text-gray-500">{village.location}</p>
                </div>
              </div>

              <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-all ${
                isFav ? 'bg-blue-500 shadow-md shadow-blue-500/30' : 'bg-gray-100 dark:bg-gray-700'
              }`}>
                {isFav
                  ? <CheckCircle size={16} className="text-white"/>
                  : <Star size={14} className="text-gray-400"/>
                }
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
