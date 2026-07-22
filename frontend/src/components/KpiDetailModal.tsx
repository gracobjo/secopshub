import { useState } from 'react';
import { FileDown, X } from 'lucide-react';
import type { Incident, IOC, Vulnerability } from '../types';
import { downloadIncidentReport, updateIncident } from '../services/incidents';

export type KpiType = 'active_alerts' | 'blocked_ips' | 'kev_vulnerabilities' | 'total_incidents';

const INCIDENT_STATUSES = ['open', 'investigating', 'resolved', 'closed'] as const;

interface KpiDetailModalProps {
  kpiType: KpiType;
  title: string;
  loading: boolean;
  incidents?: Incident[];
  iocs?: IOC[];
  vulnerabilities?: Vulnerability[];
  onClose: () => void;
  onIncidentsChange?: (incidents: Incident[]) => void;
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
  onIncidentsChange,
}: KpiDetailModalProps) {
  const [exportingId, setExportingId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [drafts, setDrafts] = useState<
    Record<number, { status: string; assigned_to: string }>
  >({});

  const count =
    incidents?.length ?? iocs?.length ?? vulnerabilities?.length ?? 0;

  const getDraft = (inc: Incident) =>
    drafts[inc.id] ?? {
      status: inc.status,
      assigned_to: inc.assigned_to || '',
    };

  const setDraftField = (
    inc: Incident,
    field: 'status' | 'assigned_to',
    value: string
  ) => {
    const current = getDraft(inc);
    setDrafts((prev) => ({
      ...prev,
      [inc.id]: { ...current, [field]: value },
    }));
  };

  const handleExportPdf = async (incidentId: number) => {
    setExportingId(incidentId);
    try {
      await downloadIncidentReport(incidentId);
    } finally {
      setExportingId(null);
    }
  };

  const handleSave = async (inc: Incident) => {
    const draft = getDraft(inc);
    setError('');
    setSavingId(inc.id);
    try {
      const updated = await updateIncident(inc.id, {
        status: draft.status,
        assigned_to: draft.assigned_to.trim() || null,
      });
      if (incidents && onIncidentsChange) {
        onIncidentsChange(
          incidents.map((item) => (item.id === updated.id ? updated : item))
        );
      }
      setDrafts((prev) => {
        const next = { ...prev };
        delete next[inc.id];
        return next;
      });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { error?: string } } })?.response?.data
          ?.error || 'No se pudo actualizar el incidente';
      setError(message);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-5xl max-h-[80vh] flex flex-col shadow-xl"
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
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              {error}
            </div>
          )}

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
                      <th className="pb-3 pr-4">Asignado</th>
                      <th className="pb-3 pr-4">Origen</th>
                      <th className="pb-3">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.map((inc) => {
                      const draft = getDraft(inc);
                      const dirty =
                        draft.status !== inc.status ||
                        draft.assigned_to !== (inc.assigned_to || '');

                      return (
                        <tr key={inc.id} className="border-b border-slate-800 align-top">
                          <td className="py-3 pr-4 text-slate-200">{inc.title}</td>
                          <td
                            className={`py-3 pr-4 capitalize ${severityStyles[inc.severity] || ''}`}
                          >
                            {inc.severity}
                          </td>
                          <td className="py-3 pr-4">
                            <select
                              value={draft.status}
                              onChange={(e) =>
                                setDraftField(inc, 'status', e.target.value)
                              }
                              className="bg-slate-900 border border-slate-600 rounded-lg px-2 py-1.5 text-slate-200 text-xs"
                            >
                              {INCIDENT_STATUSES.map((status) => (
                                <option key={status} value={status}>
                                  {status}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-3 pr-4">
                            <input
                              type="text"
                              value={draft.assigned_to}
                              onChange={(e) =>
                                setDraftField(inc, 'assigned_to', e.target.value)
                              }
                              placeholder="username"
                              className="w-28 bg-slate-900 border border-slate-600 rounded-lg px-2 py-1.5 text-slate-200 text-xs"
                            />
                          </td>
                          <td className="py-3 pr-4 text-slate-400">{inc.source}</td>
                          <td className="py-3">
                            <div className="flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() => handleSave(inc)}
                                disabled={!dirty || savingId === inc.id}
                                className="inline-flex items-center px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-700 text-slate-100 hover:bg-slate-600 disabled:opacity-40 transition-colors"
                              >
                                {savingId === inc.id ? 'Guardando...' : 'Guardar'}
                              </button>
                              <button
                                type="button"
                                onClick={() => handleExportPdf(inc.id)}
                                disabled={exportingId === inc.id}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 disabled:opacity-50 transition-colors"
                              >
                                <FileDown className="w-3.5 h-3.5" />
                                {exportingId === inc.id ? 'Generando...' : 'PDF'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
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
