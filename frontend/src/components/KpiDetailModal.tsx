import { X } from 'lucide-react';
import type { Incident, IOC, Vulnerability } from '../types';

export type KpiType = 'active_alerts' | 'blocked_ips' | 'kev_vulnerabilities' | 'total_incidents';

interface KpiDetailModalProps {
  kpiType: KpiType;
  title: string;
  loading: boolean;
  incidents?: Incident[];
  iocs?: IOC[];
  vulnerabilities?: Vulnerability[];
  onClose: () => void;
}

const severityStyles: Record<string, string> = {
  critical: 'text-rose-400',
  high: 'text-orange-400',
  medium: 'text-amber-400',
  low: 'text-emerald-400',
};

export default function KpiDetailModal({
  kpiType,
  title,
  loading,
  incidents,
  iocs,
  vulnerabilities,
  onClose,
}: KpiDetailModalProps) {
  const count =
    incidents?.length ?? iocs?.length ?? vulnerabilities?.length ?? 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
            <p className="text-sm text-slate-400 mt-0.5">
              {loading ? 'Cargando...' : `${count} registro${count !== 1 ? 's' : ''}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-colors"
            aria-label="Cerrar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-auto p-6 flex-1">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500" />
            </div>
          ) : count === 0 ? (
            <p className="text-center text-slate-500 py-8">No hay registros</p>
          ) : (
            <>
              {(kpiType === 'active_alerts' || kpiType === 'total_incidents') && incidents && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-700">
                      <th className="pb-3 pr-4">Título</th>
                      <th className="pb-3 pr-4">Severidad</th>
                      <th className="pb-3 pr-4">Estado</th>
                      <th className="pb-3 pr-4">Origen</th>
                      <th className="pb-3">Asignado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.map((inc) => (
                      <tr key={inc.id} className="border-b border-slate-800">
                        <td className="py-3 pr-4 text-slate-200">{inc.title}</td>
                        <td className={`py-3 pr-4 capitalize ${severityStyles[inc.severity] || ''}`}>
                          {inc.severity}
                        </td>
                        <td className="py-3 pr-4 text-slate-300 capitalize">{inc.status}</td>
                        <td className="py-3 pr-4 text-slate-400">{inc.source}</td>
                        <td className="py-3 text-slate-400">{inc.assigned_to || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {kpiType === 'blocked_ips' && iocs && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-700">
                      <th className="pb-3 pr-4">Valor</th>
                      <th className="pb-3 pr-4">Tipo</th>
                      <th className="pb-3 pr-4">Riesgo</th>
                      <th className="pb-3 pr-4">Veredicto</th>
                      <th className="pb-3">Fuente</th>
                    </tr>
                  </thead>
                  <tbody>
                    {iocs.map((ioc) => (
                      <tr key={ioc.id} className="border-b border-slate-800">
                        <td className="py-3 pr-4 font-mono text-slate-200">{ioc.value}</td>
                        <td className="py-3 pr-4 text-slate-400 uppercase">{ioc.ioc_type}</td>
                        <td className="py-3 pr-4 text-rose-400 font-medium">{ioc.risk_score}</td>
                        <td className="py-3 pr-4 text-slate-300 capitalize">{ioc.verdict}</td>
                        <td className="py-3 text-slate-400">{ioc.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {kpiType === 'kev_vulnerabilities' && vulnerabilities && (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-400 border-b border-slate-700">
                      <th className="pb-3 pr-4">CVE</th>
                      <th className="pb-3 pr-4">Título</th>
                      <th className="pb-3 pr-4">CVSS</th>
                      <th className="pb-3">Sistemas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vulnerabilities.map((vuln) => (
                      <tr key={vuln.id} className="border-b border-slate-800">
                        <td className="py-3 pr-4 font-mono text-emerald-400">{vuln.cve_id}</td>
                        <td className="py-3 pr-4 text-slate-200 max-w-xs truncate">{vuln.title}</td>
                        <td className="py-3 pr-4 font-medium text-slate-200">
                          {vuln.cvss_score?.toFixed(1)}
                        </td>
                        <td className="py-3 text-slate-400">{vuln.affected_systems}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
