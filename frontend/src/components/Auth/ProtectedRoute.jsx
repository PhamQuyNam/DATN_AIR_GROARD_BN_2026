import { Navigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';

/**
 * ProtectedRoute — Bảo vệ toàn bộ ứng dụng.
 * Nếu chưa đăng nhập → /login
 * Nếu là CITIZEN cố vào trang Admin → /citizen
 * Nếu là MANAGER cố vào trang Citizen → /
 */
export default function ProtectedRoute({ children, requireRole }) {
  const location = useLocation();

  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const user = authService.getUser();

  // CITIZEN cố vào Admin routes → redirect về citizen portal
  if (requireRole === 'MANAGER' && user?.role !== 'MANAGER') {
    return <Navigate to="/citizen" replace />;
  }

  // MANAGER cố vào Citizen routes → redirect về admin
  if (requireRole === 'CITIZEN' && user?.role !== 'CITIZEN') {
    return <Navigate to="/" replace />;
  }

  return children;
}
