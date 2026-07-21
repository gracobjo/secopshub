import { useEffect, useState } from 'react';
import { Play, CheckCircle, Lock } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Playbook, PlaybookResult } from '../types';

export default function PlaybooksPage() {
  const { user } = useAuth();
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [results, setResults] = useState<PlaybookResult[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    api.get<Playbook[]>('/playbooks').then(({ data }) => setPlaybooks(data));
  }, []);

  const handleRun = async (playbookId: string) => {
    if (!isAdmin) return;
    setRunning(playbookId);
    try {
      const { data } = await api.post<PlaybookResult>('/playbooks/run', {
        playbook_id: playbookId,
        params,
      });
      setResults((prev) => [data, ...prev]);
    } catch {
      /* handled by interceptor */
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
          {!isAdmin && (
            <span className="ml-2 text-amber-400">
              (Solo lectura — requiere rol admin para ejecutar)
            </span>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {playbooks.map((pb) => (
          <div key={pb.id} className="card flex flex-col">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-lg font-semibold text-slate-100">{pb.name}</h3>
              {!isAdmin && <Lock className="w-4 h-4 text-slate-500" />}
            </div>
            <p className="text-sm text-slate-400 mb-4 flex-1">{pb.description}</p>

            {pb.params.length > 0 && isAdmin && (
              <div className="space-y-2 mb-4">
                {pb.params.map((param) => (
                  <input
                    key={param}
                    type="text"
                    placeholder={param}
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
              onClick={() => handleRun(pb.id)}
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
            {results.map((result, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-4 rounded-lg bg-slate-900/50 border border-emerald-500/20"
              >
                <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-slate-200">{result.name}</p>
                  <p className="text-sm text-slate-400 mt-1">{result.result}</p>
                </div>
              </div>
            ))}
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
          Header: X-API-Key: secops-webhook-key-dev
        </code>
      </div>
    </div>
  );
}
