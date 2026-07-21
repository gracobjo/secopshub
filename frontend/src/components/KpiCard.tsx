import type { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  color: 'emerald' | 'rose' | 'amber' | 'blue';
}

const colorMap = {
  emerald: 'text-emerald-400 bg-emerald-400/10',
  rose: 'text-rose-400 bg-rose-400/10',
  amber: 'text-amber-400 bg-amber-400/10',
  blue: 'text-blue-400 bg-blue-400/10',
};

export default function KpiCard({ title, value, icon: Icon, color }: KpiCardProps) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${colorMap[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
      </div>
    </div>
  );
}
