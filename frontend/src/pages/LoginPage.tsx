import { useEffect, useState, type FormEvent } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';
import { Shield, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

export default function LoginPage() {
  const { login, isAuthenticated, isLoading, oidcEnabled, acceptTokens } = useAuth();
  const [searchParams] = useSearchParams();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const access = searchParams.get('access_token');
    const refresh = searchParams.get('refresh_token');
    if (access) {
      acceptTokens(access, refresh || undefined).then(() => {
        window.history.replaceState({}, '', '/login');
      });
    }
  }, [searchParams, acceptTokens]);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(username, password, mfaRequired ? otp : undefined);
    } catch (err: unknown) {
      const data = axios.isAxiosError(err) ? err.response?.data : undefined;
      if (data?.mfa_required) {
        setMfaRequired(true);
        setError('Introduce el código MFA de tu autenticador');
      } else {
        setError(data?.error || 'Credenciales inválidas. Inténtalo de nuevo.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-600/20 mb-4">
            <Shield className="w-8 h-8 text-emerald-400" />
          </div>
          <h1 className="text-3xl font-bold text-slate-100">SecOps Hub</h1>
          <p className="text-slate-400 mt-2">Consola de Operaciones de Ciberseguridad</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-5">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-1.5">
              Usuario
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              placeholder="admin o analyst"
              required
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-1.5">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="••••••••"
              required
            />
          </div>

          {mfaRequired && (
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-slate-300 mb-1.5">
                Código MFA (TOTP)
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="input-field"
                placeholder="123456"
                required
              />
            </div>
          )}

          <button type="submit" disabled={submitting} className="btn-primary w-full py-3">
            {submitting ? 'Iniciando sesión...' : 'Iniciar sesión'}
          </button>

          {oidcEnabled && (
            <a
              href="/api/auth/oidc/login"
              className="block text-center w-full py-3 rounded-lg border border-slate-600 text-slate-200 hover:bg-slate-800 transition-colors text-sm"
            >
              Continuar con SSO (OIDC)
            </a>
          )}

          <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-700">
            <p>Con datos demo (ENABLE_SEED=true): admin / admin123</p>
          </div>
        </form>
      </div>
    </div>
  );
}
