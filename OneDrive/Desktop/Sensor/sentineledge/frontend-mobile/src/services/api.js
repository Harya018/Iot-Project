// ─────────────────────────────────────────────
//  SentinelEdge — Axios API Service
// ─────────────────────────────────────────────
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE } from '../config/config';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor — inject auth token ───
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('@sentineledge_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.warn('Failed to read auth token from storage:', error);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor — log errors ───
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(`API Error [${error.response.status}]:`, error.response.data);
    } else if (error.request) {
      console.error('API Error: No response received', error.request);
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ─────────────────────────────────────────────
//  Exported API Functions
// ─────────────────────────────────────────────

/** GET /health — server health check */
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/** GET /alerts — fetch all alerts */
export const getAlerts = async () => {
  const response = await apiClient.get('/alerts');
  return response.data;
};

/**
 * POST /alerts/{alertId}/acknowledge
 * @param {string|number} alertId
 * @param {string} workerName
 */
export const acknowledgeAlert = async (alertId, workerName) => {
  const response = await apiClient.post(`/alerts/${alertId}/acknowledge`, {
    acknowledged_by: workerName,
    timestamp: new Date().toISOString(),
  });
  return response.data;
};

/** GET /sensor/history — temperature history */
export const getTemperatureHistory = async () => {
  const response = await apiClient.get('/sensor/history');
  return response.data;
};

/** GET /sensor/current — current sensor reading */
export const getCurrentReading = async () => {
  const response = await apiClient.get('/sensor/current');
  return response.data;
};

export default apiClient;
