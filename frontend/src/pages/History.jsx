import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import { Calendar, BarChart2, Search, Download, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import api from '../services/api';

const VILLAGES = [
  'Phong Khê','Văn Môn','Đồng Kỵ','Tràng An','Đại Bái','Xuân Lai',
  'Ninh Xá','Tam Tảo','Vạn Nguyệt','Đông Hồ','Thanh Hoài','Dương Ổ',
  'Phù Khê','Phù Lãng','Quế Cầm','Môn Quảng','Tương Giang','Vọng Nguyệt'
];

const getAqiColor = (aqi) => {
  if (aqi <= 50) return '#22c55e';
  if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316';
  if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#a855f7';
  return '#7f1d1d';
};

export default function History() {
  const today = new Date().toISOString().split('T')[0];
  const sevenDaysAgo = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0];

  const [village, setVillage] = useState('');
  const [startDate, setStartDate] = useState(sevenDaysAgo);
  const [endDate, setEndDate] = useState(today);
  const [period, setPeriod] = useState('week');
  const [activeTab, setActiveTab] = useState('chart');
  const [searchParams, setSearchParams] = useState({ village: '', start: sevenDaysAgo, end: today });

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['historySummary', searchParams.village, period],
    queryFn: async () => {
      const params = new URLSearchParams({ period });
      if (searchParams.village) params.append('village', searchParams.village);
      const res = await api.get(`/history/summary?${params}`);
      return res.data;
    }
  });

  const { data: rawData, isLoading: rawLoading } = useQuery({
    queryKey: ['historyQuery', searchParams],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: 200 });
      if (searchParams.village) params.append('village', searchParams.village);
      if (searchParams.start) params.append('start', searchParams.start);
      if (searchParams.end) params.append('end', searchParams.end);
      const res = await api.get(`/history/query?${params}`);
      return res.data;
    }
  });

  const handleSearch = () => setSearchParams({ village, start: startDate, end: endDate });

  const summary = summaryData?.summary;
  const dailyData = (summaryData?.daily || []).map(d => ({
    ...d,
    date: new Date(d.date).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }),
  }));
  const rawRecords = rawData?.data || [];

  const exportCSV = () => {
    const headers = ['Làng nghề','Thời gian','AQI','Mức độ','PM2.5','PM10','Nhiệt độ','Độ ẩm'];
    const rows = rawRecords.map(r => [
      r.village_name, new Date(r.timestamp).toLocaleString('vi-VN'),
      r.aqi, r.level, r.pm25, r.pm10, r.temperature, r.humidity
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `lich_su_aqi_${today}.csv`;
    link.click();
  };

  const kpiItems = [
    { label: 'AQI Trung bình', value: summary?.overall_avg ?? '—', icon: <Minus size={18}/>, color: '#3b82f6' },
    { label: 'AQI Cao nhất', value: summary?.overall_max ?? '—', icon: <TrendingUp size={18}/>, color: '#ef4444' },
    { label: 'AQI Thấp nhất', value: summary?.overall_min ?? '—', icon: <TrendingDown size={18}/>, color: '#22c55e' },
    { label: 'Số bản ghi', value: summary?.total_records?.toLocaleString() ?? '—', icon: <BarChart2 size={18}/>, color: '#8b5cf6' },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
          Tra cứu Lịch sử AQI
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Truy vấn và phân tích dữ liệu chất lượng không khí theo khoảng thời gian.</p>
      </div>

      {/* Bộ lọc */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Làng nghề</label>
            <select value={village} onChange={e => setVillage(e.target.value)}
              className="w-full px-3 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40">
              <option value="">Tất cả làng nghề</option>
              {VILLAGES.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Từ ngày</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={15}/>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 [color-scheme:dark]"/>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Đến ngày</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={15}/>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 [color-scheme:dark]"/>
            </div>
          </div>
          <div className="flex items-end">
            <button onClick={handleSearch}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-semibold rounded-xl text-sm transition-all">
              <Search size={16}/> Tra cứu
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpiItems.map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.07 }}
            className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-4 shadow-sm">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ background: kpi.color + '20', color: kpi.color }}>
              {kpi.icon}
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{kpi.value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{kpi.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex gap-1">
            {[{ key: 'chart', label: '📊 Biểu đồ xu hướng' }, { key: 'table', label: '📋 Dữ liệu thô' }].map(tab => (
              <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 pb-3 text-sm font-medium transition-colors ${activeTab === tab.key ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-500' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>
                {tab.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 pb-2">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5 text-xs">
              {[['week','7 ngày'],['month','30 ngày']].map(([p, label]) => (
                <button key={p} onClick={() => setPeriod(p)}
                  className={`px-3 py-1.5 rounded-md font-medium transition-all ${period === p ? 'bg-white dark:bg-gray-600 shadow text-gray-900 dark:text-white' : 'text-gray-500'}`}>
                  {label}
                </button>
              ))}
            </div>
            <button onClick={exportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-600 dark:text-green-400 border border-green-500/30 rounded-lg text-xs font-medium transition-colors">
              <Download size={13}/> Xuất CSV
            </button>
          </div>
        </div>

        <div className="p-5">
          {activeTab === 'chart' ? (
            summaryLoading ? (
              <div className="h-64 flex items-center justify-center text-gray-400">Đang tải biểu đồ...</div>
            ) : dailyData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-gray-400">Không có dữ liệu</div>
            ) : (
              <div className="space-y-6">
                <div>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">AQI theo ngày (TB / Max / Min)</p>
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={dailyData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)"/>
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }}/>
                      <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} domain={['auto', 'auto']}/>
                      <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 12, color: '#f9fafb' }}
                        formatter={(val, name) => [val, { avg_aqi: 'Trung bình', max_aqi: 'Cao nhất', min_aqi: 'Thấp nhất' }[name] || name]}/>
                      <Legend formatter={v => ({ avg_aqi: 'Trung bình', max_aqi: 'Cao nhất', min_aqi: 'Thấp nhất' })[v] || v}/>
                      <Line type="monotone" dataKey="avg_aqi" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }}/>
                      <Line type="monotone" dataKey="max_aqi" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 2" dot={false}/>
                      <Line type="monotone" dataKey="min_aqi" stroke="#22c55e" strokeWidth={1.5} strokeDasharray="4 2" dot={false}/>
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Số lượng bản ghi mỗi ngày</p>
                  <ResponsiveContainer width="100%" height={140}>
                    <BarChart data={dailyData} margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)"/>
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }}/>
                      <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }}/>
                      <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 12, color: '#f9fafb' }}/>
                      <Bar dataKey="count" fill="#6366f1" radius={[4,4,0,0]} maxBarSize={40}/>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )
          ) : (
            <div className="overflow-x-auto">
              {rawLoading ? (
                <div className="h-48 flex items-center justify-center text-gray-400">Đang tải...</div>
              ) : (
                <>
                  <p className="text-xs text-gray-500 mb-3">Hiển thị {Math.min(rawRecords.length, 100)} / {rawRecords.length} bản ghi</p>
                  <table className="w-full text-xs text-left">
                    <thead className="text-gray-500 uppercase bg-gray-50 dark:bg-gray-700/40">
                      <tr>{['Làng nghề','Thời gian','AQI','Mức độ','PM2.5','PM10','Nhiệt độ (°C)','Độ ẩm (%)'].map(h => <th key={h} className="px-4 py-2.5">{h}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {rawRecords.slice(0, 100).map((r, i) => (
                        <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                          <td className="px-4 py-2.5 font-medium text-gray-900 dark:text-white">{r.village_name}</td>
                          <td className="px-4 py-2.5 text-gray-500">{new Date(r.timestamp).toLocaleString('vi-VN')}</td>
                          <td className="px-4 py-2.5 font-bold" style={{ color: getAqiColor(r.aqi) }}>{r.aqi}</td>
                          <td className="px-4 py-2.5">
                            <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ background: getAqiColor(r.aqi)+'25', color: getAqiColor(r.aqi) }}>{r.level}</span>
                          </td>
                          <td className="px-4 py-2.5 text-gray-500">{r.pm25?.toFixed(1) ?? '—'}</td>
                          <td className="px-4 py-2.5 text-gray-500">{r.pm10?.toFixed(1) ?? '—'}</td>
                          <td className="px-4 py-2.5 text-gray-500">{r.temperature?.toFixed(1) ?? '—'}</td>
                          <td className="px-4 py-2.5 text-gray-500">{r.humidity?.toFixed(0) ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {rawRecords.length > 100 && <p className="text-xs text-gray-400 text-center mt-3">Xuất CSV để xem đầy đủ {rawRecords.length} bản ghi.</p>}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
