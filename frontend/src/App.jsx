import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Inject auth token vào Axios
import './services/authService';

// ── Admin Pages ────────────────────────────────────────────────────────────────
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import ShapAnalysis from './pages/ShapAnalysis';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import StationStatus from './pages/StationStatus';
import Recommendations from './pages/Recommendations';
import NotFound from './pages/NotFound';

// ── Citizen Pages ──────────────────────────────────────────────────────────────
import CitizenOverview from './pages/citizen/CitizenOverview';
import CitizenStations from './pages/citizen/CitizenStations';
import CitizenAlerts from './pages/citizen/CitizenAlerts';

// ── Auth Pages ─────────────────────────────────────────────────────────────────
import Login from './pages/Login';
import Register from './pages/Register';

// ── Layouts & Guards ───────────────────────────────────────────────────────────
import MainLayout from './components/Layout/MainLayout';
import CitizenLayout from './components/Layout/CitizenLayout';
import ProtectedRoute from './components/Auth/ProtectedRoute';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } }
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* ── Public: Auth ──────────────────────────────────────── */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* ── Admin / MANAGER Portal ────────────────────────────── */}
          <Route
            path="/"
            element={
              <ProtectedRoute requireRole="MANAGER">
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="forecast" element={<Forecast />} />
            <Route path="shap" element={<ShapAnalysis />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="station-status" element={<StationStatus />} />
            <Route path="recommendations" element={<Recommendations />} />
          </Route>

          {/* ── Citizen / CITIZEN Portal ──────────────────────────── */}
          <Route
            path="/citizen"
            element={
              <ProtectedRoute requireRole="CITIZEN">
                <CitizenLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<CitizenOverview />} />
            <Route path="map" element={<Dashboard />} />
            <Route path="alerts" element={<CitizenAlerts />} />
            <Route path="stations" element={<CitizenStations />} />
          </Route>

          {/* ── 404 ───────────────────────────────────────────────── */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <ToastContainer theme="dark" position="bottom-right" />
    </QueryClientProvider>
  );
}

export default App;
