import { useEffect, useState, type FormEvent } from 'react';
import { Search, ShieldBan, ShieldCheck, AlertTriangle } from 'lucide-react';
import api from '../services/api';
import type { EnrichResult, IOC } from '../types';

const verdictStyles: Record<string, string> = {
  malicious: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  suspicious: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  clean: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
};

export default function IOCsPage() {
  const [iocs, setIocs] = useState<IOC[]>([]);
  const [value, setValue] = useState('');
  const [result, setResult] = useState<EnrichResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);

  const fetchIocs = () => {
    setLoading(true);
    api
      .get<IOC[]>('/iocs')
      .then(({ data }) => setIocs(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchIocs();
  }, []);

  const handleEnrich = async (e: FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;
    setEnriching(true);
    setResult(null);
    try {
      const { data } = await api.post<EnrichResult>('/iocs/enrich', { value: value.trim() });
      setResult(data);
      fetchIocs();
    } catch {
      /* handled by interceptor */
    } finally {
      setEnriching(false);
    }
  };

  const handleBlock = async (iocId: number) => {
    await api.post(`/iocs/${iocId}/block`);
    fetchIocs();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Triaje de IOCs</h1>
        <p className="text-slate-400 mt-1">
          Enriquecimiento con AbuseIPDB y VirusTotal (simulado)
        </p>
      </div>

      <form onSubmit={handleEnrich} className="card">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          IP, Hash MD5/SHA1/SHA256 o URL
        </label>
        <div className="flex gap-3">
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="input-field flex-1"
            placeholder="Ej: 192.168.1.100 o a1b2c3d4..."
          />
          <button type="submit" disabled={enriching} className="btn-primary flex items-center gap-2">
            <Search className="w-4 h-4" />
            {enriching ? 'Analizando...' : 'Enriquecer'}
          </button>
        </div>
      </form>

      {result && (
        <div className="card border-emerald-500/30">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-100">Resultado del análisis</h2>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${
                  result.enrichment_mode === 'live'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-amber-500/20 text-amber-400'
                }`}
              >
                {result.enrichment_mode === 'live' ? 'API en vivo' : 'Modo simulado'}
              </span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  verdictStyles[result.verdict] || verdictStyles.clean
                }`}
              >
                {result.verdict.toUpperCase()}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="p-4 rounded-lg bg-slate-900/50">
              <p className="text-xs text-slate-500">Valor</p>
              <p className="text-sm font-mono text-slate-200 break-all">{result.value}</p>
            </div>
            <div className="p-4 rounded-lg bg-slate-900/50">
              <p className="text-xs text-slate-500">Tipo</p>
              <p className="text-sm text-slate-200 uppercase">{result.ioc_type}</p>
            </div>
            <div className="p-4 rounded-lg bg-slate-900/50">
              <p className="text-xs text-slate-500">Puntuación de riesgo</p>
              <p className="text-2xl font-bold text-slate-100">{result.risk_score}/100</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700">
              <p className="text-sm font-medium text-slate-300 mb-2">VirusTotal</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <span className="text-rose-400">Malicioso: {result.virustotal.malicious}</span>
                <span className="text-amber-400">Sospechoso: {result.virustotal.suspicious}</span>
                <span className="text-emerald-400">Limpio: {result.virustotal.harmless}</span>
                <span className="text-slate-400">No detectado: {result.virustotal.undetected}</span>
              </div>
            </div>
            {result.abuseipdb && (
              <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700">
                <p className="text-sm font-medium text-slate-300 mb-2">AbuseIPDB</p>
                <div className="text-sm space-y-1">
                  <p className="text-slate-300">
                    Confianza de abuso: {result.abuseipdb.abuse_confidence_score}%
                  </p>
                  <p className="text-slate-400">
                    Reportes: {result.abuseipdb.total_reports}
                  </p>
                </div>
              </div>
            )}
          </div>

          {result.recommendation === 'block' && (
            <div className="mt-4 flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
              <AlertTriangle className="w-4 h-4" />
              Recomendación: Bloquear este indicador
            </div>
          )}
        </div>
      )}

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">IOCs registrados</h2>
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-emerald-500" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="pb-3 pr-4">Valor</th>
                  <th className="pb-3 pr-4">Tipo</th>
                  <th className="pb-3 pr-4">Riesgo</th>
                  <th className="pb-3 pr-4">Veredicto</th>
                  <th className="pb-3 pr-4">Estado</th>
                  <th className="pb-3">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {iocs.map((ioc) => (
                  <tr key={ioc.id} className="border-b border-slate-800">
                    <td className="py-3 pr-4 font-mono text-slate-200">{ioc.value}</td>
                    <td className="py-3 pr-4 text-slate-400 uppercase">{ioc.ioc_type}</td>
                    <td className="py-3 pr-4">
                      <span
                        className={`font-medium ${
                          ioc.risk_score >= 75
                            ? 'text-rose-400'
                            : ioc.risk_score >= 40
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                        }`}
                      >
                        {ioc.risk_score}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs border ${
                          verdictStyles[ioc.verdict] || verdictStyles.clean
                        }`}
                      >
                        {ioc.verdict}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      {ioc.blocked ? (
                        <span className="flex items-center gap-1 text-rose-400">
                          <ShieldBan className="w-4 h-4" /> Bloqueado
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <ShieldCheck className="w-4 h-4" /> Activo
                        </span>
                      )}
                    </td>
                    <td className="py-3">
                      {!ioc.blocked && ioc.verdict === 'malicious' && (
                        <button
                          onClick={() => handleBlock(ioc.id)}
                          className="btn-danger text-xs py-1 px-2"
                        >
                          Bloquear
                        </button>
                      )}
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
