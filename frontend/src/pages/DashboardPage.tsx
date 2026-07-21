import { useCallback, useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import { AlertTriangle, ShieldBan, Bug, Activity } from 'lucide-react';
import api from '../services/api';
import KpiCard from '../components/KpiCard';
import KpiDetailModal, { type KpiType } from '../components/KpiDetailModal';
import type { DashboardStats, Incident, IOC, Vulnerability } from '../types';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#f43f5e',
  high: '#f97316',
  medium: '#eab308',
  low: '#10b981',
};

const KPI_TITLES: Record<KpiType, string> = {
  active_alerts: 'Alertas activas',
  blocked_ips: 'IPs bloqueadas',
  kev_vulnerabilities: 'Vulnerabilidades KEV abiertas',
  total_incidents: 'Todos los incidentes',
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedKpi, setSelectedKpi] = useState<KpiType | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [iocs, setIocs] = useState<IOC[]>([]);
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);

  useEffect(() => {
    api
      .get<DashboardStats>('/incidents/stats')
      .then(({ data }) => setStats(data))
      .finally(() => setLoading(false));
  }, []);

  const openKpiDetail = useCallback(async (kpiType: KpiType) => {
    setSelectedKpi(kpiType);
    setDetailLoading(true);
    setIncidents([]);
    setIocs([]);
    setVulnerabilities([]);

    try {
      switch (kpiType) {
        case 'active_alerts': {
          const { data } = await api.get<Incident[]>('/incidents?status=active');
          setIncidents(data);
          break;
        }
        case 'blocked_ips': {
          const { data } = await api.get<IOC[]>('/iocs?blocked=true');
          setIocs(data);
          break;
        }
        case 'kev_vulnerabilities': {
          const { data } = await api.get<Vulnerability[]>(
            '/vulnerabilities?kev_only=true&status=open'
          );
          setVulnerabilities(data);
          break;
        }
        case 'total_incidents': {
          const { data } = await api.get<Incident[]>('/incidents');
          setIncidents(data);
          break;
        }
      }
    } finally {
      setDetailLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-emerald-500" />
      </div>
    );
  }

  if (!stats) return null;

  const severityData = stats.severity_distribution.map((item) => ({
    ...item,
    fill: SEVERITY_COLORS[item.severity] || '#64748b',
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Dashboard SOC</h1>
        <p className="text-slate-400 mt-1">Vista general de operaciones de seguridad</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          title="Alertas activas"
          value={stats.kpis.active_alerts}
          icon={AlertTriangle}
          color="rose"
          onClick={() => openKpiDetail('active_alerts')}
        />
        <KpiCard
          title="IPs bloqueadas"
          value={stats.kpis.blocked_ips}
          icon={ShieldBan}
          color="amber"
          onClick={() => openKpiDetail('blocked_ips')}
        />
        <KpiCard
          title="Vulnerabilidades KEV"
          value={stats.kpis.kev_vulnerabilities}
          icon={Bug}
          color="rose"
          onClick={() => openKpiDetail('kev_vulnerabilities')}
        />
        <KpiCard
          title="Total incidentes"
          value={stats.kpis.total_incidents}
          icon={Activity}
          color="emerald"
          onClick={() => openKpiDetail('total_incidents')}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Distribución por severidad
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={severityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="severity" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {severityData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-100 mb-4">
            Eventos por hora (24h)
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={stats.hourly_events}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                }}
              />
              <Line
                type="monotone"
                dataKey="events"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">
          Feed de auditoría
        </h2>
        <div className="space-y-3">
          {stats.audit_feed.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-4 p-3 rounded-lg bg-slate-900/50 border border-slate-700/50"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 mt-2 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-slate-200">{log.action}</p>
                {log.details && (
                  <p className="text-xs text-slate-500 mt-0.5">{log.details}</p>
                )}
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-emerald-400">{log.username}</p>
                <p className="text-xs text-slate-500">
                  {log.created_at
                    ? new Date(log.created_at).toLocaleString('es-ES')
                    : '-'}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedKpi && (
        <KpiDetailModal
          kpiType={selectedKpi}
          title={KPI_TITLES[selectedKpi]}
          loading={detailLoading}
          incidents={
            selectedKpi === 'active_alerts' || selectedKpi === 'total_incidents'
              ? incidents
              : undefined
          }
          iocs={selectedKpi === 'blocked_ips' ? iocs : undefined}
          vulnerabilities={
            selectedKpi === 'kev_vulnerabilities' ? vulnerabilities : undefined
          }
          onClose={() => setSelectedKpi(null)}
        />
      )}
    </div>
  );
}
