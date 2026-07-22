import { useEffect, useState } from 'react';
import { Play, CheckCircle, Lock, AlertTriangle, XCircle } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Playbook, PlaybookResult } from '../types';

const DESTRUCTIVE_HINTS: Record<string, string> = {
  isolate_host: 'Esto aislará el host en el EDR. ¿Confirmas la ejecución?',
  block_ip: 'Esto bloqueará la IP en el firewall. ¿Confirmas la ejecución?',
  revoke_user: 'Esto revocará sesiones del usuario en Azure AD. ¿Confirmas?',
};

export default function PlaybooksPage() {
  const { user } = useAuth();
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [results, setResults] = useState<PlaybookResult[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [integrationMode, setIntegrationMode] = useState<string>('simulated');
  const [executable, setExecutable] = useState<Record<string, boolean>>({});
  const [error, setError] = useState('');

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    api.get<Playbook[]>('/playbooks').then(({ data }) => setPlaybooks(data));
    api
      .get<{
        respuesta: { mode: string; executable?: Record<string, boolean> };
      }>('/integrations/status')
      .then(({ data }) => {
        setIntegrationMode(data.respuesta.mode);
        setExecutable(data.respuesta.executable || {});
      });
  }, []);

  const handleRun = async (playbook: Playbook) => {
    if (!isAdmin) return;
    setError('');

    if (playbook.destructive !== false && DESTRUCTIVE_HINTS[playbook.id]) {
      const ok = window.confirm(
        DESTRUCTIVE_HINTS[playbook.id] ||
          `¿Confirmas ejecutar el playbook «${playbook.name}»?`
      );
      if (!ok) return;
    }

    setRunning(playbook.id);
    try {
      const { data } = await api.post<PlaybookResult>('/playbooks/run', {
        playbook_id: playbook.id,
        params,
        confirm: true,
      });
      setResults((prev) => [data, ...prev]);
    } catch (err: unknown) {
      const payload = (err as { response?: { data?: PlaybookResult & { error?: string } } })
        ?.response?.data;
      if (payload?.playbook_id || payload?.result) {
        setResults((prev) => [payload as PlaybookResult, ...prev]);
      }
      setError(payload?.error || payload?.result || 'Error al ejecutar el playbook');
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Playbooks de Respuesta</h1>
        <p className="text-slate-400 mt-1">
          Automatización de respuesta a incidentes
          <span
            className={`ml-2 px-2 py-0.5 rounded text-xs ${
              integrationMode === 'live'
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-amber-500/20 text-amber-400'
            }`}
          >
            Respuesta: {integrationMode === 'live' ? 'HTTP ejecutable' : 'simulada'}
          </span>
          {!isAdmin && (
            <span className="ml-2 text-amber-400">
              (Solo lectura — requiere rol admin para ejecutar)
            </span>
          )}
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {playbooks.map((pb) => (
          <div key={pb.id} className="card flex flex-col">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-semibold text-slate-100">{pb.name}</h3>
              <div className="flex items-center gap-2">
                {pb.destructive && (
                  <span className="text-[10px] uppercase tracking-wide text-rose-400 border border-rose-500/30 px-1.5 py-0.5 rounded">
                    Destructivo
                  </span>
                )}
                {!isAdmin && <Lock className="w-4 h-4 text-slate-500" />}
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-2 flex-1">{pb.description}</p>
            <p className="text-xs text-slate-500 mb-4">
              Modo:{' '}
              {executable[pb.id]
                ? 'live (integración lista)'
                : pb.id === 'data_scan'
                  ? 'siempre simulado'
                  : 'simulado (sin credenciales)'}
            </p>

            {pb.params.length > 0 && isAdmin && (
              <div className="space-y-2 mb-4">
                {pb.params.map((param) => (
                  <input
                    key={param}
                    type="text"
                    placeholder={
                      param === 'device_id' ? 'device_id (opcional)' : param
                    }
                    value={params[param] || ''}
                    onChange={(e) =>
                      setParams((prev) => ({ ...prev, [param]: e.target.value }))
                    }
                    className="input-field text-sm"
                  />
                ))}
              </div>
            )}

            <button
              onClick={() => handleRun(pb)}
              disabled={!isAdmin || running === pb.id}
              className="btn-primary flex items-center justify-center gap-2 mt-auto disabled:opacity-40"
            >
              <Play className="w-4 h-4" />
              {running === pb.id ? 'Ejecutando...' : 'Ejecutar'}
            </button>
          </div>
        ))}
      </div>

      {results.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Resultados de ejecución
          </h2>
          <div className="space-y-3">
            {results.map((result, idx) => {
              const failed = result.status === 'failed';
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-4 rounded-lg bg-slate-900/50 border ${
                    failed ? 'border-rose-500/30' : 'border-emerald-500/20'
                  }`}
                >
                  {failed ? (
                    <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-slate-200">{result.name}</p>
                    <p className="text-sm text-slate-400 mt-1">{result.result}</p>
                    {result.mode && (
                      <p className="text-xs text-slate-500 mt-1">
                        Modo: {result.mode === 'live' ? 'integración real' : 'simulado'} ·{' '}
                        Estado: {result.status}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-100 mb-3">Webhook de alertas</h2>
        <p className="text-sm text-slate-400 mb-3">
          Envía alertas externas al endpoint protegido por API Key:
        </p>
        <code className="block p-3 rounded-lg bg-slate-900 text-emerald-400 text-sm font-mono">
          POST /api/webhooks/alert
          <br />
          Header: X-API-Key: &lt;WEBHOOK_API_KEY&gt;
        </code>
      </div>
    </div>
  );
}
