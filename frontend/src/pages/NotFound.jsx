import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, AlertCircle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="text-center"
      >
        <motion.div
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          transition={{ delay: 0.1, type: 'spring' }}
          className="text-9xl font-black text-transparent bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text mb-4"
        >
          404
        </motion.div>
        <AlertCircle className="mx-auto text-gray-600 mb-4" size={40}/>
        <h1 className="text-2xl font-bold text-white mb-2">Trang không tồn tại</h1>
        <p className="text-gray-500 mb-8 max-w-sm mx-auto">
          Đường dẫn bạn truy cập không tồn tại hoặc đã bị xóa.
        </p>
        <Link to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-semibold rounded-xl shadow-lg transition-all"
        >
          <Home size={18}/> Về trang chủ
        </Link>
      </motion.div>
    </div>
  );
}
