import { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Map, TrendingUp, Cpu, Bell, PieChart, Sun, Moon, LogOut, Server, MessageSquarePlus } from 'lucide-react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { authService } from '../../services/authService';

export default function MainLayout() {
  const [isDark, setIsDark] = useState(true);
  const [hoveredPath, setHoveredPath] = useState(null);
  const navigate = useNavigate();
  const currentUser = authService.getUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Toggle Dark/Light mode
  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [isDark]);

  // Fetch số lượng cảnh báo gần đây (poll mỗi 60 giây)
  const { data: alertsData } = useQuery({
    queryKey: ['activeAlertsCount'],
    queryFn: async () => {
      const res = await api.get('/alerts/active');
      return res.data.data || [];
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const alertCount = alertsData?.length || 0;
  const hasAlerts = alertCount > 0;

  const navItems = [
    { to: "/", icon: <Map size={18} />, label: "Bản đồ AQI" },
    { to: "/forecast", icon: <TrendingUp size={18} />, label: "Dự báo 6h" },
    { to: "/shap", icon: <Cpu size={18} />, label: "Phân tích SHAP" },
    { to: "/alerts", icon: <Bell size={18} />, label: "Cảnh báo", showBadge: true },
    { to: "/analytics", icon: <PieChart size={18} />, label: "Thống kê" },
    { to: "/station-status", icon: <Server size={18} />, label: "Trạng thái trạm", adminOnly: true },
    { to: "/recommendations", icon: <MessageSquarePlus size={18} />, label: "Khuyến nghị", adminOnly: true },
  ];

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header / Top Navigation */}
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md transition-colors duration-300">
        <div className="flex items-center justify-between px-6 h-16 max-w-7xl mx-auto">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-2xl">🍃</span>
            <h1 className="text-xl font-bold bg-gradient-to-r from-green-500 to-emerald-400 bg-clip-text text-transparent">
              AirGuard BN
            </h1>
          </div>

          {/* Animated Sliding Glass Menu */}
          <nav 
            className="hidden md:flex items-center gap-1 relative"
            onMouseLeave={() => setHoveredPath(null)}
          >
            {/* Nhóm 1: Menu chính */}
            {navItems
              .filter(item => !item.adminOnly)
              .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                onMouseEnter={() => setHoveredPath(item.to)}
                className={({ isActive }) =>
                  `relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors z-10 ${
                    isActive
                      ? "text-green-600 dark:text-green-400"
                      : "text-gray-600 dark:text-gray-300 hover:text-green-500 dark:hover:text-green-300"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <div className="absolute inset-0 bg-green-500/10 dark:bg-green-500/20 rounded-xl -z-10" />
                    )}
                    {hoveredPath === item.to && (
                      <motion.div
                        layoutId="glass-pill"
                        className="absolute inset-0 bg-white/40 dark:bg-white/10 backdrop-blur-md rounded-xl shadow-[0_4px_12px_rgba(0,0,0,0.05)] dark:shadow-[0_4px_12px_rgba(255,255,255,0.02)] border border-white/20 dark:border-white/5 -z-10"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                      />
                    )}
                    <span className="relative">
                      {item.icon}
                      {item.showBadge && hasAlerts && (
                        <span className="absolute -top-1.5 -right-1.5 flex h-3 w-3">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                        </span>
                      )}
                    </span>
                    {item.label}
                    {item.showBadge && hasAlerts && (
                      <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white bg-red-500 rounded-full min-w-[18px]">
                        {alertCount > 9 ? '9+' : alertCount}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            ))}

            {/* Divider phân cách nhóm Admin */}
            {currentUser?.role === 'MANAGER' && (
              <div className="flex items-center gap-1 ml-1">
                <div className="h-5 w-px bg-gray-200 dark:bg-gray-700 mx-1" />
                {navItems
                  .filter(item => item.adminOnly)
                  .map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onMouseEnter={() => setHoveredPath(item.to)}
                    className={({ isActive }) =>
                      `relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors z-10 ${
                        isActive
                          ? "text-blue-600 dark:text-blue-400"
                          : "text-gray-500 dark:text-gray-400 hover:text-blue-500 dark:hover:text-blue-300"
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <div className="absolute inset-0 bg-blue-500/10 dark:bg-blue-500/15 rounded-xl -z-10" />
                        )}
                        {hoveredPath === item.to && (
                          <motion.div
                            layoutId="glass-pill-admin"
                            className="absolute inset-0 bg-white/40 dark:bg-white/10 backdrop-blur-md rounded-xl border border-white/20 dark:border-white/5 -z-10"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ type: "spring", stiffness: 400, damping: 30 }}
                          />
                        )}
                        {item.icon}
                        <span className="hidden lg:inline">{item.label}</span>
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            )}
          </nav>


          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Alert Bell mobile */}
            {hasAlerts && (
              <div className="relative md:hidden">
                <Bell size={20} className="text-red-500" />
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              </div>
            )}

            {/* Theme Toggle */}
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle Dark Mode"
            >
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            {/* Divider */}
            <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />

            {/* User info + Logout */}
            <div className="flex items-center gap-2">
              {/* Avatar + Tên */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center text-white font-bold shadow-md text-sm">
                  {currentUser?.full_name?.charAt(0) || 'A'}
                </div>
                <div className="hidden lg:block">
                  <p className="text-sm font-semibold text-gray-800 dark:text-gray-100 leading-none">
                    {currentUser?.full_name || 'Admin'}
                  </p>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                    currentUser?.role === 'MANAGER' 
                      ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' 
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400'
                  }`}>
                    {currentUser?.role === 'MANAGER' ? '🛡️ Quản lý' : '👤 Công dân'}
                  </span>
                </div>
              </div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                title="Đăng xuất"
                className="p-2 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900 transition-colors duration-300 p-6">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
