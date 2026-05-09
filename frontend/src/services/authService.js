/**
 * services/authService.js
 * Quản lý Auth state: login, logout, lưu JWT vào localStorage.
 */
import api from './api';

const TOKEN_KEY = 'airguard_token';
const USER_KEY = 'airguard_user';

export const authService = {
  async login(email, password) {
    // OAuth2PasswordRequestForm yêu cầu form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });

    const { access_token, role, full_name } = res.data;
    localStorage.setItem(TOKEN_KEY, access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({ email, role, full_name }));
    return res.data;
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  isManager() {
    const user = this.getUser();
    return user?.role === 'MANAGER';
  }
};

// Inject token vào mọi request của Axios
import axios from 'axios';
api.interceptors.request.use(config => {
  const token = authService.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
