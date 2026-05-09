import { motion } from 'framer-motion';
import AQIMap from '../components/Map/AQIMap';

export default function Dashboard() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400 bg-clip-text text-transparent">
            Bản đồ Chất lượng Không khí (AQI)
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Giám sát thời gian thực 18 làng nghề tại Bắc Ninh</p>
        </div>
      </div>
      
      {/* Map Component */}
      <AQIMap />
      
    </motion.div>
  );
}
