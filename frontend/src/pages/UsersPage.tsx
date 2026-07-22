import { useEffect, useState, type FormEvent } from 'react';
import { KeyRound, Shield, UserPlus } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types';

export default function UsersPage() {
  const { user: me, refreshUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [webhookMasked, setWebhookMasked] = useState('');
  const [rotatedKey, setRotatedKey] = useState('');

  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'analyst',
  });

  const [mfaSecret, setMfaSecret] = useState('');
  const [mfaUri, setMfaUri] = useState('');
  const [mfaOtp, setMfaOtp] = useState('');

  const fetchUsers = () => {
    setLoading(true);
    api
      .get<User[]>('/users')
      .then(({ data }) => setUsers(data))
      .catch(() => setError('No se pudo cargar usuarios'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsers();
    api.get<{ masked: string }>('/settings/webhook-key').then(({ data }) => {
      setWebhookMasked(data.masked);
    });
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await api.post('/auth/register', form);
      setMessage(`Usuario ${form.username} creado`);
      setForm({ username: '', email: '', password: '', role: 'analyst' });
      fetchUsers();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'Error al crear usuario'
      );
    }
  };

  const toggleActive = async (u: User) => {
    setError('');
    try {
      await api.patch(`/users/${u.id}`, { is_active: !u.is_active });
      fetchUsers();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'No se pudo actualizar'
      );
    }
  };

  const changeRole = async (u: User, role: string) => {
    try {
      await api.patch(`/users/${u.id}`, { role });
      fetchUsers();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'No se pudo cambiar el rol'
      );
    }
  };

  const rotateWebhook = async () => {
    if (!window.confirm('¿Rotar WEBHOOK_API_KEY? El SIEM dejará de autenticarse hasta actualizarla.')) {
      return;
    }
    setError('');
    try {
      const { data } = await api.post<{ webhook_api_key: string }>(
        '/settings/webhook-key/rotate'
      );
      setRotatedKey(data.webhook_api_key);
      setMessage('Clave de webhook rotada. Cópiala ahora; no se volverá a mostrar completa.');
      const meta = await api.get<{ masked: string }>('/settings/webhook-key');
      setWebhookMasked(meta.data.masked);
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'Error al rotar clave'
      );
    }
  };

  const setupMfa = async () => {
    setError('');
    try {
      const { data } = await api.post<{ secret: string; otpauth_uri: string }>(
        '/auth/mfa/setup'
      );
      setMfaSecret(data.secret);
      setMfaUri(data.otpauth_uri);
      setMessage('Escanea el secreto en tu app TOTP y confirma con un código');
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'Error MFA setup'
      );
    }
  };

  const enableMfa = async () => {
    try {
      await api.post('/auth/mfa/enable', { otp: mfaOtp });
      setMessage('MFA activado');
      setMfaSecret('');
      setMfaUri('');
      setMfaOtp('');
      await refreshUser();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'Código MFA inválido'
      );
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Administración</h1>
        <p className="text-slate-400 mt-1">Usuarios, MFA y rotación de webhook</p>
      </div>

      {(message || error) && (
        <div
          className={`p-3 rounded-lg text-sm border ${
            error
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}
        >
          {error || message}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <form onSubmit={handleCreate} className="card space-y-4">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-emerald-400" /> Nuevo usuario
          </h2>
          <input
            className="input-field"
            placeholder="username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            className="input-field"
            type="email"
            placeholder="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <input
            className="input-field"
            type="password"
            placeholder="password (≥8)"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={8}
          />
          <select
            className="input-field"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
          >
            <option value="analyst">analyst</option>
            <option value="admin">admin</option>
          </select>
          <button type="submit" className="btn-primary">
            Crear
          </button>
        </form>

        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-emerald-400" /> Webhook API Key
          </h2>
          <p className="text-sm text-slate-400">
            Actual (enmascarada): <span className="font-mono text-slate-200">{webhookMasked}</span>
          </p>
          <button type="button" onClick={rotateWebhook} className="btn-danger">
            Rotar clave
          </button>
          {rotatedKey && (
            <code className="block p-3 rounded-lg bg-slate-900 text-amber-300 text-xs break-all">
              {rotatedKey}
            </code>
          )}

          <div className="border-t border-slate-700 pt-4 space-y-3">
            <h3 className="text-sm font-medium text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4" /> MFA (tu cuenta: {me?.username})
            </h3>
            <p className="text-xs text-slate-500">
              Estado: {me?.mfa_enabled ? 'activado' : 'desactivado'}
            </p>
            {!me?.mfa_enabled && (
              <>
                <button type="button" onClick={setupMfa} className="btn-primary text-sm">
                  Generar secreto TOTP
                </button>
                {mfaSecret && (
                  <div className="space-y-2 text-xs">
                    <p className="font-mono text-slate-300 break-all">Secret: {mfaSecret}</p>
                    <p className="text-slate-500 break-all">{mfaUri}</p>
                    <input
                      className="input-field"
                      placeholder="Código TOTP"
                      value={mfaOtp}
                      onChange={(e) => setMfaOtp(e.target.value)}
                    />
                    <button type="button" onClick={enableMfa} className="btn-primary text-sm">
                      Confirmar y activar MFA
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Usuarios</h2>
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="pb-3 pr-4">Usuario</th>
                <th className="pb-3 pr-4">Email</th>
                <th className="pb-3 pr-4">Rol</th>
                <th className="pb-3 pr-4">Origen</th>
                <th className="pb-3 pr-4">MFA</th>
                <th className="pb-3">Estado</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-800">
                  <td className="py-3 pr-4 text-slate-200">{u.username}</td>
                  <td className="py-3 pr-4 text-slate-400">{u.email}</td>
                  <td className="py-3 pr-4">
                    <select
                      className="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-xs"
                      value={u.role}
                      onChange={(e) => changeRole(u, e.target.value)}
                      disabled={u.id === me?.id}
                    >
                      <option value="analyst">analyst</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="py-3 pr-4 text-slate-500">{u.auth_source || 'local'}</td>
                  <td className="py-3 pr-4 text-slate-400">
                    {u.mfa_enabled ? 'sí' : 'no'}
                  </td>
                  <td className="py-3">
                    <button
                      type="button"
                      onClick={() => toggleActive(u)}
                      disabled={u.id === me?.id}
                      className={`text-xs px-2 py-1 rounded ${
                        u.is_active
                          ? 'bg-emerald-600/20 text-emerald-400'
                          : 'bg-rose-600/20 text-rose-400'
                      } disabled:opacity-40`}
                    >
                      {u.is_active ? 'Activo' : 'Inactivo'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
