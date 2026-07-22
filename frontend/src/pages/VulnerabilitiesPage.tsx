import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Vulnerability } from '../types';

const severityStyles: Record<string, string> = {
  critical: 'bg-rose-500/20 text-rose-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-amber-500/20 text-amber-400',
  low: 'bg-emerald-500/20 text-emerald-400',
};

const VULN_STATUSES = ['open', 'in_progress', 'mitigated', 'accepted', 'closed'] as const;

export default function VulnerabilitiesPage() {
  const { user } = useAuth();
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [kevOnly, setKevOnly] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const isAdmin = user?.role === 'admin';

  const fetchVulns = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (severityFilter) params.set('severity', severityFilter);
    if (kevOnly) params.set('kev_only', 'true');

    api
      .get<Vulnerability[]>(`/vulnerabilities?${params}`)
      .then(({ data }) => setVulns(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVulns();
  }, [severityFilter, kevOnly]);

  const handleStatusChange = async (vuln: Vulnerability, status: string) => {
    if (status === vuln.status) return;
    setError('');
    setSavingId(vuln.id);
    try {
      const { data } = await api.patch<Vulnerability>(`/vulnerabilities/${vuln.id}`, {
        status,
      });
      setVulns((prev) => prev.map((v) => (v.id === data.id ? data : v)));
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'No se pudo actualizar el estado'
      );
    } finally {
      setSavingId(null);
    }
  };

  const handleSyncKev = async () => {
    if (!isAdmin) return;
    setError('');
    setMessage('');
    setSyncing(true);
    try {
      const { data } = await api.post<{
        created: number;
        updated: number;
        fetched: number;
        catalog_version?: string;
      }>('/vulnerabilities/sync-kev', {});
      setMessage(
        `KEV sincronizado: ${data.created} nuevos, ${data.updated} actualizados ` +
          `(feed ${data.fetched}${data.catalog_version ? `, catálogo ${data.catalog_version}` : ''})`
      );
      fetchVulns();
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ||
          'Error al sincronizar CISA KEV'
      );
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Vulnerabilidades</h1>
          <p className="text-slate-400 mt-1">
            Auditoría CISA KEV y cumplimiento normativo (RGPD)
          </p>
        </div>
        {isAdmin && (
          <button
            type="button"
            onClick={handleSyncKev}
            disabled={syncing}
            className="btn-primary inline-flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Sincronizando…' : 'Sync CISA KEV'}
          </button>
        )}
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

      <div className="card flex flex-wrap items-center gap-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Severidad</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="input-field w-40"
          >
            <option value="">Todas</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <label className="flex items-center gap-3 cursor-pointer mt-5">
          <input
            type="checkbox"
            checked={kevOnly}
            onChange={(e) => setKevOnly(e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-emerald-500 focus:ring-emerald-500"
          />
          <span className="text-sm text-slate-300">Solo CISA KEV (explotación activa)</span>
        </label>
      </div>

      <div className="card">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="pb-3 pr-4">CVE</th>
                  <th className="pb-3 pr-4">Título</th>
                  <th className="pb-3 pr-4">Severidad</th>
                  <th className="pb-3 pr-4">CVSS</th>
                  <th className="pb-3 pr-4">KEV</th>
                  <th className="pb-3 pr-4">Sistemas</th>
                  <th className="pb-3">Estado</th>
                </tr>
              </thead>
              <tbody>
                {vulns.map((vuln) => (
                  <tr key={vuln.id} className="border-b border-slate-800">
                    <td className="py-3 pr-4 font-mono text-emerald-400">{vuln.cve_id}</td>
                    <td className="py-3 pr-4 text-slate-200 max-w-xs truncate">
                      {vuln.title}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs capitalize ${
                          severityStyles[vuln.severity] || severityStyles.low
                        }`}
                      >
                        {vuln.severity}
                      </span>
                    </td>
                    <td className="py-3 pr-4 font-medium text-slate-200">
                      {vuln.cvss_score?.toFixed(1)}
                    </td>
                    <td className="py-3 pr-4">
                      {vuln.is_kev ? (
                        <span className="px-2 py-0.5 rounded text-xs bg-rose-500/20 text-rose-400">
                          KEV
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-slate-400">{vuln.affected_systems}</td>
                    <td className="py-3">
                      <select
                        value={vuln.status}
                        disabled={savingId === vuln.id}
                        onChange={(e) => handleStatusChange(vuln, e.target.value)}
                        className="bg-slate-900 border border-slate-600 rounded-lg px-2 py-1.5 text-slate-200 text-xs capitalize disabled:opacity-50"
                      >
                        {VULN_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
