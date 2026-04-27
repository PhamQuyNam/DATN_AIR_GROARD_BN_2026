import { motion } from 'framer-motion';

export default function Analytics() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <h2 className="text-3xl font-bold">Thống kê Xu hướng (Analytics)</h2>
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 min-h-[400px] flex items-center justify-center">
        <p className="text-gray-400">Time-series Comparison Charts will be here</p>
      </div>
    </motion.div>
  );
}
