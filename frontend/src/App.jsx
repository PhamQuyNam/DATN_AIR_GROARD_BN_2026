import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import Pages (Chúng ta sẽ tạo sau)
import Dashboard from './pages/Dashboard';
import Forecast from './pages/Forecast';
import ShapAnalysis from './pages/ShapAnalysis';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';

// Import Layout Component
import MainLayout from './components/Layout/MainLayout';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="forecast" element={<Forecast />} />
            <Route path="shap" element={<ShapAnalysis />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <ToastContainer theme="dark" position="bottom-right" />
    </QueryClientProvider>
  );
}

export default App;
