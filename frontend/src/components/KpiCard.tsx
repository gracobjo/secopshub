import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  color: 'emerald' | 'rose' | 'amber' | 'blue';
  onClick?: () => void;
}

const colorMap = {
  emerald: 'text-emerald-400 bg-emerald-400/10',
  rose: 'text-rose-400 bg-rose-400/10',
  amber: 'text-amber-400 bg-amber-400/10',
  blue: 'text-blue-400 bg-blue-400/10',
};

export default function KpiCard({ title, value, icon: Icon, color, onClick }: KpiCardProps) {
  const interactive = Boolean(onClick);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!interactive}
      className={`card flex items-center gap-4 w-full text-left transition-colors ${
        interactive
          ? 'cursor-pointer hover:border-emerald-500/50 hover:bg-slate-800/80 focus:outline-none focus:ring-2 focus:ring-emerald-500/50'
          : 'cursor-default'
      }`}
    >
      <div className={`p-3 rounded-lg ${colorMap[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="flex-1">
        <p className="text-sm text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        {interactive && (
          <p className="text-xs text-emerald-500/70 mt-1">Clic para ver detalle</p>
        )}
      </div>
    </button>
  );
}
