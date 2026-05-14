import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { getAQIColor } from '../../utils/aqiColors';
import { Layers, Map as MapIcon, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import bacninhData from '../../data/bacninh.json';

// Fix icon lỗi mặc định của Leaflet khi dùng với Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component tạo icon HTML tùy chỉnh (để tô màu marker)
const createCustomIcon = (aqi, isActive = true) => {
  const colorObj = isActive ? getAQIColor(aqi) : { bg: '#9ca3af', text: '#ffffff', label: 'Ngừng hoạt động' };
  
  return L.divIcon({
    className: 'custom-icon',
    html: `
      <div style="
        background-color: ${colorObj.bg};
        color: ${colorObj.text};
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        border: 2px solid white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
        filter: ${isActive ? 'none' : 'grayscale(0.5)'};
      " class="hover:scale-110 hover:shadow-lg">
        ${isActive ? Math.round(aqi) : '!'}
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
};

// Component Legend (Chú giải)
const MapLegend = () => {
  const thresholds = [
    { range: '0 - 50', label: 'Tốt', color: '#00E400' },
    { range: '51 - 100', label: 'Trung bình', color: '#FFFF00' },
    { range: '101 - 150', label: 'Kém', color: '#FF7E00' },
    { range: '151 - 200', label: 'Xấu', color: '#FF0000' },
    { range: '201 - 300', label: 'Rất xấu', color: '#8F3F97' },
    { range: '301+', label: 'Nguy hại', color: '#7E0023' },
    { range: '--', label: 'Ngừng hoạt động', color: '#9ca3af' },
  ];

  return (
    <div className="absolute bottom-6 left-6 z-[1000] bg-white/90 dark:bg-gray-800/90 backdrop-blur-md p-4 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl max-w-[200px]">
      <h4 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 px-1">Chỉ số AQI</h4>
      <div className="space-y-2">
        {thresholds.map((t, i) => (
          <div key={i} className="flex items-center gap-3 group">
            <div 
              className="w-3 h-3 rounded-full shadow-sm group-hover:scale-125 transition-transform" 
              style={{ backgroundColor: t.color }} 
            />
            <div className="flex flex-col">
              <span className="text-[11px] font-bold text-gray-900 dark:text-white leading-none">{t.label}</span>
              <span className="text-[9px] text-gray-500 dark:text-gray-400 mt-0.5">{t.range}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function AQIMap() {
  const [mapStyle, setMapStyle] = useState('osm'); // 'osm' or 'dark'
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Đóng menu khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Lấy dữ liệu từ Backend API (Tự động fetch lại mỗi 5 phút)
  const { data, isLoading, error } = useQuery({
    queryKey: ['aqiCurrent'],
    queryFn: async () => {
      const response = await api.get('/aqi/current');
      return response.data.data; // Mảng các làng nghề
    },
    refetchInterval: 5 * 60 * 1000, 
  });

  if (isLoading) return (
    <div className="flex items-center justify-center h-full min-h-[600px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
    </div>
  );

  if (error) return (
    <div className="text-red-500 text-center py-20">
      Lỗi tải dữ liệu bản đồ: {error.message}
    </div>
  );

  // Tọa độ trung tâm tỉnh Bắc Ninh
  const bacNinhCenter = [21.1861, 106.0763];

  return (
    <div className="relative h-[600px] w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-sm z-0">
      
      {/* Custom Map Style Dropdown (Floating) */}
      <div className="absolute top-4 right-4 z-[1000]" ref={menuRef}>
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="w-12 h-12 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 flex items-center justify-center text-gray-700 dark:text-gray-300 hover:text-green-500 dark:hover:text-green-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
          title="Chọn Lớp Bản Đồ"
        >
          <Layers size={24} />
        </button>

        <AnimatePresence>
          {isMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute right-0 mt-3 w-56 bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              <div className="p-3 space-y-1">
                <button
                  onClick={() => { setMapStyle('osm'); setIsMenuOpen(false); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    mapStyle === 'osm' 
                      ? 'bg-green-50 text-green-600 dark:bg-green-500/20 dark:text-green-400' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <MapIcon size={18} className={mapStyle === 'osm' ? 'text-green-500' : 'text-gray-500'} />
                  Bản đồ Tiêu chuẩn
                </button>
                
                <button
                  onClick={() => { setMapStyle('dark'); setIsMenuOpen(false); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                    mapStyle === 'dark' 
                      ? 'bg-blue-50 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Moon size={18} className={mapStyle === 'dark' ? 'text-blue-500' : 'text-gray-500'} />
                  Bản đồ Nền Tối
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Legend Component */}
      <MapLegend />

      <MapContainer 
        center={bacNinhCenter} 
        zoom={11} 
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={false} // Tắt zoom mặc định để tự đặt vị trí
      >
        {/* Tùy chỉnh vị trí nút Zoom (chuyển xuống dưới cùng bên phải) */}
        <div className="leaflet-bottom leaflet-right mb-4 mr-4">
          <div className="leaflet-control-zoom leaflet-bar leaflet-control">
            <a className="leaflet-control-zoom-in" href="#" title="Zoom in" role="button" aria-label="Zoom in">+</a>
            <a className="leaflet-control-zoom-out" href="#" title="Zoom out" role="button" aria-label="Zoom out">−</a>
          </div>
        </div>

        <TileLayer
          key={mapStyle} // Bắt buộc dùng key để Leaflet render lại khi đổi layer
          attribution={mapStyle === 'osm' ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' : '&copy; <a href="https://carto.com/attributions">CARTO</a>'}
          url={mapStyle === 'osm' ? "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"}
        />

        {/* Lớp hiển thị đường viền ranh giới tỉnh Bắc Ninh */}
        <GeoJSON 
          data={bacninhData} 
          style={{
            color: '#3b82f6', // Màu viền xanh dương
            weight: 3,        // Độ dày viền
            opacity: 0.8,
            fillColor: '#3b82f6',
            fillOpacity: 0.05, // Màu nền đổ nhẹ để làm nổi bật tỉnh
            dashArray: '5, 10' // Đường nét đứt
          }}
        />

        {data?.map((village, idx) => (
          <Marker 
            key={idx} 
            position={[village.lat, village.lon]}
            icon={createCustomIcon(village.aqi, village.is_active !== false)}
          >
            <Tooltip direction="top" offset={[0, -15]} opacity={1} className="custom-hover-tooltip">
              <div className="p-1 min-w-[200px] font-sans">
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="font-extrabold text-[1.1rem] tracking-tight">{village.village_name}</h3>
                  {village.is_active === false && (
                    <span className="text-[9px] font-bold bg-gray-500 text-white px-1.5 py-0.5 rounded uppercase">Ngừng hoạt động</span>
                  )}
                </div>
                
                <div className="flex items-center gap-2 mb-3">
                  <span 
                    className="px-3 py-1 rounded-full text-[11px] font-bold shadow-sm uppercase tracking-wider" 
                    style={{ 
                      backgroundColor: village.is_active !== false ? getAQIColor(village.aqi).bg : '#9ca3af', 
                      color: village.is_active !== false ? getAQIColor(village.aqi).text : '#ffffff' 
                    }}
                  >
                    AQI: {village.is_active !== false ? Math.round(village.aqi) : '--'} ({village.is_active !== false ? village.level : 'N/A'})
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
                  <div className="opacity-70 font-medium">PM2.5:</div>
                  <div className="font-semibold text-right">{village.is_active !== false ? village.pm25?.toFixed(1) : '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">CO:</div>
                  <div className="font-semibold text-right">{village.is_active !== false ? village.co?.toFixed(1) : '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">SO2:</div>
                  <div className="font-semibold text-right">{village.is_active !== false ? village.so2?.toFixed(1) : '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">NO2:</div>
                  <div className="font-semibold text-right">{village.is_active !== false ? village.no2?.toFixed(1) : '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">O3:</div>
                  <div className="font-semibold text-right">{village.is_active !== false ? village.o3?.toFixed(1) : '--'} µg/m³</div>
                </div>

                <div className="mt-4 pt-2 border-t border-gray-200 dark:border-gray-700 text-[11px] opacity-50 font-medium text-right italic">
                  Cập nhật: {new Date(village.timestamp).toLocaleTimeString('vi-VN')}
                </div>
              </div>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

