import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import api, {
  clearAuthStorage,
  setCookieMode,
  setRefreshToken,
  setToken,
} from '../services/api';
import type { LoginResponse, User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  cookieMode: boolean;
  oidcEnabled: boolean;
  login: (username: string, password: string, otp?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  acceptTokens: (access: string, refresh?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cookieMode, setCookieModeState] = useState(false);
  const [oidcEnabled, setOidcEnabled] = useState(false);

  const refreshUser = useCallback(async () => {
    const { data } = await api.get<User>('/auth/me');
    setUser(data);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data: cfg } = await api.get<{
          cookie_mode: boolean;
          oidc_enabled: boolean;
        }>('/auth/config');
        if (!cancelled) {
          setCookieMode(cfg.cookie_mode);
          setCookieModeState(cfg.cookie_mode);
          setOidcEnabled(cfg.oidc_enabled);
        }
      } catch {
        /* ignore */
      }
      try {
        const { data } = await api.get<User>('/auth/me');
        if (!cancelled) setUser(data);
      } catch {
        if (!cancelled) {
          clearAuthStorage();
          setUser(null);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const acceptTokens = useCallback(
    async (access: string, refresh?: string) => {
      setToken(access);
      if (refresh) setRefreshToken(refresh);
      await refreshUser();
      setIsLoading(false);
    },
    [refreshUser]
  );

  const login = useCallback(async (username: string, password: string, otp?: string) => {
    const { data } = await api.post<LoginResponse>('/auth/login', {
      username,
      password,
      otp: otp || undefined,
    });
    if (data.access_token) setToken(data.access_token);
    if (data.refresh_token) setRefreshToken(data.refresh_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      /* ignore */
    }
    clearAuthStorage();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      cookieMode,
      oidcEnabled,
      login,
      logout,
      refreshUser,
      acceptTokens,
    }),
    [user, isLoading, cookieMode, oidcEnabled, login, logout, refreshUser, acceptTokens]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
}
