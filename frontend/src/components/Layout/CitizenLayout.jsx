import { useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Map, Bell, Star, LogOut, Home } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { authService } from '../../services/authService';
import api from '../../services/api';

const LAST_SEEN_KEY = 'citizen_alerts_last_seen';

export default function CitizenLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const user = authService.getUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Khi người dùng VÀO trang cảnh báo → lưu timestamp hiện tại & invalidate badge
  useEffect(() => {
    if (location.pathname === '/citizen/alerts') {
      localStorage.setItem(LAST_SEEN_KEY, new Date().toISOString());
      // Force re-render badge bằng cách update query key
      queryClient.invalidateQueries(['citizenNotifBadge']);
    }
  }, [location.pathname]);

  // Feed data để tính badge — dùng queryKey riêng để không conflict với trang alerts
  const { data: feedData } = useQuery({
    queryKey: ['citizenNotifBadge'],
    queryFn: async () => {
      const res = await api.get('/citizen/feed');
      return res.data;
    },
    refetchInterval: 30000,
    staleTime: 15000,
  });

  const stations = feedData?.stations || [];
  const lastSeenAt = localStorage.getItem(LAST_SEEN_KEY);
  const lastSeenDate = lastSeenAt ? new Date(lastSeenAt) : null;

  // Đếm cảnh báo MỚI HƠN lần xem cuối
  const newAlertCount = stations.reduce((sum, s) => {
    const newAlerts = (s.all_alerts || []).filter(a => {
      if (!lastSeenDate) return true; // chưa xem lần nào → tất cả là mới
      return a.approved_at && new Date(a.approved_at) > lastSeenDate;
    });
    return sum + newAlerts.length;
  }, 0);

  // Đếm khuyến nghị MỚI HƠN lần xem cuối
  const newRecCount = stations.filter(s => {
    if (!s.recommendation || !s.rec_time) return false;
    if (!lastSeenDate) return true;
    return new Date(s.rec_time) > lastSeenDate;
  }).length;

  const notifCount = newAlertCount + newRecCount;
  const hasNotif = notifCount > 0;

  const navItemsDesktop = [
    { to: '/citizen', icon: <Home size={16}/>, label: 'Tổng quan', end: true },
    { to: '/citizen/map', icon: <Map size={16}/>, label: 'Bản đồ AQI' },
    {
      to: '/citizen/alerts',
      label: 'Cảnh báo & Khuyến nghị',
      hasBadge: hasNotif,
      badge: notifCount,
      icon: (
        <span className="relative inline-flex">
          <Bell size={16}/>
          {hasNotif && (
            <span className="absolute -top-1.5 -right-1.5 flex h-3.5 w-3.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"/>
              <span className="relative inline-flex h-3.5 w-3.5 rounded-full bg-red-500 text-[8px] font-bold text-white items-center justify-center">
                {notifCount > 9 ? '9+' : notifCount}
              </span>
            </span>
          )}
        </span>
      ),
    },
    { to: '/citizen/stations', icon: <Star size={16}/>, label: 'Trạm quan tâm' },
  ];

  const navItemsMobile = [
    { to: '/citizen', icon: <Home size={18}/>, label: 'Tổng quan', end: true },
    { to: '/citizen/map', icon: <Map size={18}/>, label: 'Bản đồ' },
    {
      to: '/citizen/alerts',
      label: 'Cảnh báo',
      icon: (
        <span className="relative inline-flex">
          <Bell size={18}/>
          {hasNotif && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"/>
              <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500"/>
            </span>
          )}
        </span>
      ),
    },
    { to: '/citizen/stations', icon: <Star size={18}/>, label: 'Trạm' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/90 backdrop-blur-xl border-b border-gray-200 dark:border-gray-700/50 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center shadow-md shadow-blue-500/30">
              <span className="text-xl">🍃</span>
            </div>
            <div>
              <p className="font-bold text-gray-900 dark:text-white text-sm leading-none">AirGuard BN</p>
              <p className="text-xs text-blue-500 font-medium">Cổng Người dân</p>
            </div>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navItemsDesktop.map(item => (
              <NavLink key={item.to} to={item.to} end={item.end}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
                      : 'text-gray-600 dark:text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10'
                  }`
                }>
                {item.icon}
                <span>{item.label}</span>
                {item.hasBadge && (
                  <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white bg-red-500 rounded-full min-w-[18px]">
                    {item.badge > 9 ? '9+' : item.badge}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          {/* User info + Logout */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-400 to-blue-600 flex items-center justify-center text-white text-sm font-bold shadow">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 leading-none">{user?.full_name}</p>
                <span className="text-xs text-blue-500 font-medium">👤 Người dân</span>
              </div>
            </div>
            <button onClick={handleLogout} title="Đăng xuất"
              className="p-2 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
              <LogOut size={18}/>
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        <div className="md:hidden flex border-t border-gray-100 dark:border-gray-800">
          {navItemsMobile.map(item => (
            <NavLink key={item.to} to={item.to} end={item.end}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
                  isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'
                }`
              }>
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
