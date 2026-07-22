import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const TOKEN_KEY = 'secops_token';
const REFRESH_KEY = 'secops_refresh';

let cookieMode = false;

export const setCookieMode = (enabled: boolean): void => {
  cookieMode = enabled;
};

export const getToken = (): string | null =>
  cookieMode ? null : localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string): void => {
  if (!cookieMode) localStorage.setItem(TOKEN_KEY, token);
};
export const removeToken = (): void => localStorage.removeItem(TOKEN_KEY);

export const getRefreshToken = (): string | null =>
  cookieMode ? null : localStorage.getItem(REFRESH_KEY);
export const setRefreshToken = (token: string): void => {
  if (!cookieMode) localStorage.setItem(REFRESH_KEY, token);
};
export const removeRefreshToken = (): void => localStorage.removeItem(REFRESH_KEY);

export const clearAuthStorage = (): void => {
  removeToken();
  removeRefreshToken();
};

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  try {
    if (cookieMode) {
      await axios.post('/api/auth/refresh', {}, { withCredentials: true });
      return 'cookie';
    }
    const refresh = getRefreshToken();
    if (!refresh) return null;
    const { data } = await axios.post(
      '/api/auth/refresh',
      {},
      { headers: { Authorization: `Bearer ${refresh}` }, withCredentials: true }
    );
    setToken(data.access_token);
    if (data.refresh_token) setRefreshToken(data.refresh_token);
    return data.access_token as string;
  } catch {
    clearAuthStorage();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;
    const isMfaChallenge =
      status === 401 &&
      (error.response?.data as { mfa_required?: boolean } | undefined)?.mfa_required;

    if (status === 401 && !original?._retry && !isMfaChallenge) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken && original) {
        if (newToken !== 'cookie') {
          original.headers.Authorization = `Bearer ${newToken}`;
        }
        return api(original);
      }
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
