import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FileText, Printer, ChevronDown, AlertTriangle, MessageSquare, TrendingUp } from 'lucide-react';
import api from '../services/api';
import { authService } from '../services/authService';

const VILLAGES = [
  'Phong Khê','Văn Môn','Đồng Kỵ','Tràng An','Đại Bái','Xuân Lai',
  'Ninh Xá','Tam Tảo','Vạn Nguyệt','Đông Hồ','Thanh Hoài','Dương Ổ',
  'Phù Khê','Phù Lãng','Quế Cầm','Môn Quảng','Tương Giang','Vọng Nguyệt'
];

const PIE_COLORS = { 'Tốt': '#22c55e', 'Trung bình': '#eab308', 'Kém': '#f97316', 'Xấu': '#ef4444', 'Rất xấu': '#a855f7', 'Nguy hại': '#7f1d1d' };
const getAqiColor = (aqi) => {
  if (aqi <= 50) return '#22c55e'; if (aqi <= 100) return '#eab308';
  if (aqi <= 150) return '#f97316'; if (aqi <= 200) return '#ef4444';
  if (aqi <= 300) return '#a855f7'; return '#7f1d1d';
};

export default function Report() {
  const [village, setVillage] = useState('');
  const [period, setPeriod] = useState('week');
  const [submitted, setSubmitted] = useState(false);
  const [queryParams, setQueryParams] = useState({ village: '', period: 'week' });
  const currentUser = authService.getUser();

  const { data, isLoading, error } = useQuery({
    queryKey: ['report', queryParams],
    queryFn: async () => {
      const params = new URLSearchParams({ period: queryParams.period });
      if (queryParams.village) params.append('village', queryParams.village);
      const res = await api.get(`/report/generate?${params}`);
      return res.data;
    },
    enabled: submitted,
  });

  const handleGenerate = () => {
    setSubmitted(true);
    setQueryParams({ village, period });
  };

  const handlePrint = () => window.print();

  return (
    <>
      {/* Print CSS */}
      <style>{`
        @media print {
          body * { visibility: hidden; }
          #report-content, #report-content * { visibility: visible; }
          #report-content { position: absolute; top: 0; left: 0; width: 100%; padding: 20px; background: white !important; color: black !important; }
          .no-print { display: none !important; }
          .print-break { page-break-before: always; }
        }
      `}</style>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
              Xuất Báo cáo Định kỳ
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Tổng hợp AQI, cảnh báo và khuyến nghị theo kỳ báo cáo.</p>
          </div>
          {data && (
            <button onClick={handlePrint} className="no-print flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white font-semibold rounded-xl shadow-md transition-all">
              <Printer size={18}/> In / Xuất PDF
            </button>
          )}
        </div>

        {/* Bộ lọc — no-print */}
        <div className="no-print bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Làng nghề</label>
              <div className="relative">
                <select value={village} onChange={e => setVillage(e.target.value)}
                  className="w-full px-3 py-2.5 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl text-sm text-gray-900 dark:text-white appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500/40">
                  <option value="">Tất cả 18 làng nghề</option>
                  {VILLAGES.map(v => <option key={v} value={v}>{v}</option>)}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={15}/>
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Kỳ báo cáo</label>
              <div className="flex gap-2">
                {[['week','7 ngày qua'],['month','30 ngày qua']].map(([p, label]) => (
                  <button key={p} onClick={() => setPeriod(p)}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ${period === p ? 'bg-blue-500 border-blue-500 text-white shadow-md' : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-400'}`}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-end">
              <button onClick={handleGenerate}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-semibold rounded-xl shadow-md transition-all text-sm">
                <FileText size={16}/> Tạo báo cáo
              </button>
            </div>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-16 flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"/>
            <p className="text-gray-500">Đang tổng hợp dữ liệu báo cáo...</p>
          </div>
        )}

        {/* Nội dung báo cáo */}
        {data && !isLoading && (
          <div id="report-content" className="space-y-6">

            {/* Tiêu đề báo cáo */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-6 text-white">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🍃</span>
                    <span className="text-blue-200 text-sm font-medium">AirGuard BN — Sở TN&MT Bắc Ninh</span>
                  </div>
                  <h3 className="text-2xl font-bold mb-1">{data.metadata.title}</h3>
                  <p className="text-blue-200">Kỳ: {data.metadata.period_label}</p>
                </div>
                <div className="text-right text-sm text-blue-200">
                  <p>Ngày tạo: {new Date(data.metadata.generated_at).toLocaleDateString('vi-VN')}</p>
                  <p>Người tạo: {data.metadata.generated_by}</p>
                </div>
              </div>
            </div>

            {/* KPI tổng hợp */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Số bản ghi', value: data.aqi_summary.total_records.toLocaleString(), color: '#3b82f6' },
                { label: 'AQI Trung bình', value: data.aqi_summary.overall_avg, color: getAqiColor(data.aqi_summary.overall_avg) },
                { label: 'AQI Cao nhất', value: data.aqi_summary.overall_max, color: '#ef4444' },
                { label: 'Số cảnh báo', value: data.alerts.length, color: '#f97316' },
              ].map((k, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 p-4 shadow-sm text-center">
                  <p className="text-3xl font-bold mb-1" style={{ color: k.color }}>{k.value}</p>
                  <p className="text-xs text-gray-500">{k.label}</p>
                </div>
              ))}
            </div>

            {/* Biểu đồ xu hướng + Phân phối mức độ */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
                <h4 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TrendingUp size={16} className="text-blue-500"/> Xu hướng AQI theo ngày
                </h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={data.daily_data.map(d => ({ ...d, date: new Date(d.date).toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit' }) }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)"/>
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9ca3af' }}/>
                    <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} domain={['auto','auto']}/>
                    <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 12, color: '#f9fafb' }}/>
                    <Line type="monotone" dataKey="avg" stroke="#3b82f6" strokeWidth={2.5} dot={{ r: 3 }} name="TB"/>
                    <Line type="monotone" dataKey="max" stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Max"/>
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
                <h4 className="font-bold text-gray-900 dark:text-white mb-4">Phân phối mức độ ô nhiễm</h4>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie data={data.level_distribution} dataKey="count" nameKey="level" outerRadius={65} label={({ level, percent }) => `${level} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                      {data.level_distribution.map((entry, i) => (
                        <Cell key={i} fill={PIE_COLORS[entry.level] || '#6b7280'}/>
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 12, color: '#f9fafb' }}/>
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 mt-2">
                  {data.level_distribution.map(d => (
                    <div key={d.level} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[d.level] || '#6b7280' }}/>
                        <span className="text-gray-600 dark:text-gray-400">{d.level}</span>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-white">{d.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Xếp hạng làng nghề (chỉ khi query tất cả) */}
            {data.village_ranking.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm p-5">
                <h4 className="font-bold text-gray-900 dark:text-white mb-4">🏭 Top 10 Làng nghề ô nhiễm nhất (AQI trung bình)</h4>
                <div className="space-y-2">
                  {data.village_ranking.map((v, i) => (
                    <div key={v.village} className="flex items-center gap-3">
                      <span className={`w-6 text-center text-xs font-bold ${i < 3 ? 'text-red-500' : 'text-gray-400'}`}>{i + 1}</span>
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">{v.village}</span>
                      <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${(v.avg_aqi / data.aqi_summary.overall_max) * 100}%`, background: getAqiColor(v.avg_aqi) }}/>
                      </div>
                      <span className="w-12 text-right text-sm font-bold" style={{ color: getAqiColor(v.avg_aqi) }}>{v.avg_aqi}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Danh sách cảnh báo */}
            {data.alerts.length > 0 && (
              <div className="print-break bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
                  <AlertTriangle size={16} className="text-orange-500"/>
                  <h4 className="font-bold text-gray-900 dark:text-white">Danh sách sự cố cảnh báo ({data.alerts.length})</h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="text-gray-500 uppercase bg-gray-50 dark:bg-gray-700/40">
                      <tr>{['Thời gian','Làng nghề','AQI','Ngưỡng','Ghi chú'].map(h => <th key={h} className="px-4 py-2.5">{h}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {data.alerts.slice(0, 20).map((a, i) => (
                        <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                          <td className="px-4 py-2.5 text-gray-500">{new Date(a.timestamp).toLocaleString('vi-VN')}</td>
                          <td className="px-4 py-2.5 font-medium text-gray-900 dark:text-white">{a.village}</td>
                          <td className="px-4 py-2.5 font-bold" style={{ color: getAqiColor(a.aqi) }}>{a.aqi}</td>
                          <td className="px-4 py-2.5 text-gray-500">{a.threshold}</td>
                          <td className="px-4 py-2.5 text-gray-500 truncate max-w-xs">{a.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Danh sách khuyến nghị */}
            {data.recommendations.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center gap-2">
                  <MessageSquare size={16} className="text-blue-500"/>
                  <h4 className="font-bold text-gray-900 dark:text-white">Khuyến nghị đã gửi ({data.recommendations.length})</h4>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.recommendations.map((r, i) => (
                    <div key={i} className="px-5 py-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-blue-500 bg-blue-500/10 px-2 py-0.5 rounded-full">{r.village}</span>
                        <span className="text-xs text-gray-400">{new Date(r.created_at).toLocaleString('vi-VN')}</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{r.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Footer báo cáo */}
            <div className="text-center text-xs text-gray-400 py-4 border-t border-gray-100 dark:border-gray-700">
              Báo cáo được tạo bởi hệ thống AirGuard BN — Sở Tài nguyên & Môi trường Bắc Ninh
              <br/>Ngày tạo: {new Date(data.metadata.generated_at).toLocaleString('vi-VN')} | Người tạo: {data.metadata.generated_by}
            </div>
          </div>
        )}
      </motion.div>
    </>
  );
}
