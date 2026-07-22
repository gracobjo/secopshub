import { useCallback, useEffect, useState } from 'react';
import {
  Play,
  CheckCircle,
  Lock,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Ban,
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Playbook, PlaybookResult } from '../types';

interface PlaybookApproval {
  id: number;
  playbook_id: string;
  params: Record<string, string>;
  status: string;
  requested_by: string;
  approved_by?: string;
  created_at: string;
  result?: PlaybookResult;
}

const DESTRUCTIVE_HINTS: Record<string, string> = {
  isolate_host: 'Esto aislará el host en el EDR. ¿Solicitar ejecución (4-eyes)?',
  block_ip: 'Esto bloqueará la IP en el firewall. ¿Solicitar ejecución (4-eyes)?',
  revoke_user: 'Esto revocará sesiones del usuario. ¿Solicitar ejecución (4-eyes)?',
};

export default function PlaybooksPage() {
  const { user } = useAuth();
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [results, setResults] = useState<PlaybookResult[]>([]);
  const [approvals, setApprovals] = useState<PlaybookApproval[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [integrationMode, setIntegrationMode] = useState<string>('simulated');
  const [executable, setExecutable] = useState<Record<string, boolean>>({});
  const [fourEyes, setFourEyes] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const isAdmin = user?.role === 'admin';

  const loadApprovals = useCallback(() => {
    if (!isAdmin) return;
    api.get<PlaybookApproval[]>('/playbooks/approvals?status=pending').then(({ data }) => {
      setApprovals(data);
    });
  }, [isAdmin]);

  useEffect(() => {
    api
      .get<{ playbooks: Playbook[]; four_eyes: boolean } | Playbook[]>('/playbooks')
      .then(({ data }) => {
        if (Array.isArray(data)) {
          setPlaybooks(data);
        } else {
          setPlaybooks(data.playbooks);
          setFourEyes(data.four_eyes);
        }
      });
    api
      .get<{
        respuesta: { mode: string; executable?: Record<string, boolean> };
      }>('/integrations/status')
      .then(({ data }) => {
        setIntegrationMode(data.respuesta.mode);
        setExecutable(data.respuesta.executable || {});
      });
    loadApprovals();
  }, [loadApprovals]);

  const handleRun = async (playbook: Playbook) => {
    if (!isAdmin) return;
    setError('');
    setMessage('');

    if (playbook.destructive !== false && DESTRUCTIVE_HINTS[playbook.id]) {
      const ok = window.confirm(
        fourEyes
          ? DESTRUCTIVE_HINTS[playbook.id]
          : `¿Confirmas ejecutar el playbook «${playbook.name}»?`
      );
      if (!ok) return;
    }

    setRunning(playbook.id);
    try {
      const { data, status } = await api.post<
        PlaybookResult & {
          status?: string;
          approval?: PlaybookApproval;
          message?: string;
        }
      >('/playbooks/run', {
        playbook_id: playbook.id,
        params,
        confirm: true,
      });

      if (status === 202 || data.status === 'pending_approval') {
        setMessage(data.message || 'Pendiente de aprobación 4-eyes');
        loadApprovals();
      } else {
        setResults((prev) => [data as PlaybookResult, ...prev]);
      }
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

  const handleApprove = async (id: number) => {
    setError('');
    try {
      const { data } = await api.post<{ result: PlaybookResult }>(
        `/playbooks/approvals/${id}/approve`
      );
      if (data.result) setResults((prev) => [data.result, ...prev]);
      setMessage(`Solicitud #${id} aprobada y ejecutada`);
      loadApprovals();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'No se pudo aprobar'
      );
    }
  };

  const handleReject = async (id: number) => {
    setError('');
    try {
      await api.post(`/playbooks/approvals/${id}/reject`);
      setMessage(`Solicitud #${id} rechazada`);
      loadApprovals();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'No se pudo rechazar'
      );
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
          {fourEyes && (
            <span className="ml-2 px-2 py-0.5 rounded text-xs bg-sky-500/20 text-sky-400">
              4-eyes activo
            </span>
          )}
          {!isAdmin && (
            <span className="ml-2 text-amber-400">
              (Solo lectura — requiere rol admin para ejecutar)
            </span>
          )}
        </p>
      </div>

      {(error || message) && (
        <div
          className={`flex items-center gap-2 p-3 rounded-lg text-sm border ${
            error
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error || message}
        </div>
      )}

      {isAdmin && approvals.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Aprobaciones pendientes (4-eyes)
          </h2>
          <div className="space-y-3">
            {approvals.map((a) => (
              <div
                key={a.id}
                className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-lg bg-slate-900/50 border border-sky-500/20"
              >
                <div>
                  <p className="text-sm text-slate-200">
                    #{a.id} · <span className="font-mono">{a.playbook_id}</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Solicitado por {a.requested_by} ·{' '}
                    {a.created_at ? new Date(a.created_at).toLocaleString('es-ES') : ''}
                  </p>
                  <p className="text-xs text-slate-400 font-mono mt-1">
                    {JSON.stringify(a.params)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    disabled={a.requested_by === user?.username}
                    onClick={() => handleApprove(a.id)}
                    className="btn-primary text-xs inline-flex items-center gap-1 disabled:opacity-40"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" /> Aprobar
                  </button>
                  <button
                    type="button"
                    disabled={a.requested_by === user?.username}
                    onClick={() => handleReject(a.id)}
                    className="btn-danger text-xs inline-flex items-center gap-1 disabled:opacity-40"
                  >
                    <Ban className="w-3.5 h-3.5" /> Rechazar
                  </button>
                </div>
              </div>
            ))}
          </div>
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
              {running === pb.id
                ? 'Procesando...'
                : fourEyes && pb.destructive
                  ? 'Solicitar'
                  : 'Ejecutar'}
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
