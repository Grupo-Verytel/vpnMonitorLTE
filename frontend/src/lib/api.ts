import axios from 'axios';
import { toast } from 'sonner';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

let lastErrorToast = 0;

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status && status >= 400) {
      const now = Date.now();
      if (now - lastErrorToast > 5000) {
        lastErrorToast = now;
        toast.error('No se pudo cargar los datos. Reintentando...');
      }
    }
    return Promise.reject(error);
  },
);

export function isNetworkError(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response;
}
