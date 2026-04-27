import { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Map, TrendingUp, Cpu, Bell, PieChart, Sun, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function MainLayout() {
  const [isDark, setIsDark] = useState(true);
  const [hoveredPath, setHoveredPath] = useState(null);

  // Toggle Dark/Light mode
  useEffect(() => {
    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [isDark]);

  const navItems = [
    { to: "/", icon: <Map size={18} />, label: "Bản đồ AQI" },
    { to: "/forecast", icon: <TrendingUp size={18} />, label: "Dự báo 6h" },
    { to: "/shap", icon: <Cpu size={18} />, label: "Phân tích SHAP" },
    { to: "/alerts", icon: <Bell size={18} />, label: "Cảnh báo" },
    { to: "/analytics", icon: <PieChart size={18} />, label: "Thống kê" },
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
            className="hidden md:flex items-center gap-2 relative"
            onMouseLeave={() => setHoveredPath(null)}
          >
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onMouseEnter={() => setHoveredPath(item.to)}
                className={({ isActive }) =>
                  `relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors z-10 ${
                    isActive
                      ? "text-green-600 dark:text-green-400"
                      : "text-gray-600 dark:text-gray-300 hover:text-green-500 dark:hover:text-green-300"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {/* Nền xanh khi đang ở trang đó (Active) */}
                    {isActive && (
                      <div className="absolute inset-0 bg-green-500/10 dark:bg-green-500/20 rounded-xl -z-10" />
                    )}
                    
                    {/* Hiệu ứng gương trượt khi Hover */}
                    {hoveredPath === item.to && (
                      <motion.div
                        layoutId="glass-pill"
                        className="absolute inset-0 bg-white/40 dark:bg-white/10 backdrop-blur-md rounded-xl shadow-[0_4px_12px_rgba(0,0,0,0.05)] dark:shadow-[0_4px_12px_rgba(255,255,255,0.02)] border border-white/20 dark:border-white/5 -z-10"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{
                          type: "spring",
                          stiffness: 400,
                          damping: 30,
                        }}
                      />
                    )}
                    
                    {item.icon}
                    {item.label}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            {/* Theme Toggle Button */}
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-full text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle Dark Mode"
            >
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-green-400 to-blue-500 flex items-center justify-center text-white font-bold shadow-md cursor-pointer hover:scale-105 transition-transform">
              A
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
