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
const createCustomIcon = (aqi) => {
  const colorObj = getAQIColor(aqi);
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
      " class="hover:scale-110 hover:shadow-lg">
        ${Math.round(aqi)}
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
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
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
    </div>
  );

  if (error) return (
    <div className="text-red-500 text-center">
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
            icon={createCustomIcon(village.aqi)}
          >
            <Tooltip direction="top" offset={[0, -15]} opacity={1} className="custom-hover-tooltip">
              <div className="p-1 min-w-[200px] font-sans">
                <h3 className="font-extrabold text-[1.1rem] mb-1.5 tracking-tight">{village.village_name}</h3>
                
                <div className="flex items-center gap-2 mb-3">
                  <span 
                    className="px-3 py-1 rounded-full text-[11px] font-bold shadow-sm uppercase tracking-wider" 
                    style={{ backgroundColor: getAQIColor(village.aqi).bg, color: getAQIColor(village.aqi).text }}
                  >
                    AQI: {Math.round(village.aqi)} ({village.level})
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
                  <div className="opacity-70 font-medium">PM2.5:</div>
                  <div className="font-semibold text-right">{village.pm25?.toFixed(1) || '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">CO:</div>
                  <div className="font-semibold text-right">{village.co?.toFixed(1) || '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">SO2:</div>
                  <div className="font-semibold text-right">{village.so2?.toFixed(1) || '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">NO2:</div>
                  <div className="font-semibold text-right">{village.no2?.toFixed(1) || '--'} µg/m³</div>
                  
                  <div className="opacity-70 font-medium">O3:</div>
                  <div className="font-semibold text-right">{village.o3?.toFixed(1) || '--'} µg/m³</div>
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
