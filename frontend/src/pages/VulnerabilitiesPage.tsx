import { useEffect, useState } from 'react';
import api from '../services/api';
import type { Vulnerability } from '../types';

const severityStyles: Record<string, string> = {
  critical: 'bg-rose-500/20 text-rose-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-amber-500/20 text-amber-400',
  low: 'bg-emerald-500/20 text-emerald-400',
};

export default function VulnerabilitiesPage() {
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [kevOnly, setKevOnly] = useState(false);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (severityFilter) params.set('severity', severityFilter);
    if (kevOnly) params.set('kev_only', 'true');

    api
      .get<Vulnerability[]>(`/vulnerabilities?${params}`)
      .then(({ data }) => setVulns(data))
      .finally(() => setLoading(false));
  }, [severityFilter, kevOnly]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Vulnerabilidades</h1>
        <p className="text-slate-400 mt-1">
          Auditoría CISA KEV y cumplimiento normativo (RGPD)
        </p>
      </div>

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
                      <span className="text-slate-300 capitalize">{vuln.status}</span>
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
