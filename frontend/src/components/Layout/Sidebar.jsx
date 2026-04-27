import { NavLink } from 'react-router-dom';
import { Map, TrendingUp, Cpu, Bell, PieChart } from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { to: "/", icon: <Map size={20} />, label: "Bản đồ AQI" },
    { to: "/forecast", icon: <TrendingUp size={20} />, label: "Dự báo 6h" },
    { to: "/shap", icon: <Cpu size={20} />, label: "Phân tích SHAP" },
    { to: "/alerts", icon: <Bell size={20} />, label: "Cảnh báo" },
    { to: "/analytics", icon: <PieChart size={20} />, label: "Thống kê" },
  ];

  return (
    <div className="w-64 bg-gray-800 h-screen border-r border-gray-700 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-green-400 flex items-center gap-2">
          🍃 AirGuard BN
        </h1>
      </div>
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? "bg-green-600 text-white"
                  : "text-gray-400 hover:bg-gray-700 hover:text-white"
              }`
            }
          >
            {item.icon}
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
