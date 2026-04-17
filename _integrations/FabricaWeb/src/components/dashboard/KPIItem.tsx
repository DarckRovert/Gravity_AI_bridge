export interface KPIItemProps {
    title: string;
    value: string;
    color: string;
    icon: string;
    trend?: 'up' | 'down' | 'stable';
}

export function KPIItem({ title, value, color, icon, trend }: KPIItemProps) {
    return (
        <div className="bg-dash-card border border-dash-border p-6 rounded-2xl shadow-xl transition-transform hover:scale-105">
            <div className="flex justify-between items-start mb-4">
                <span className="text-2xl">{icon}</span>
                {trend === 'up' && <span className="text-[10px] bg-green-900/40 text-green-400 px-2 py-1 rounded-full border border-green-900">↑ TENDENCIA</span>}
                {trend === 'down' && <span className="text-[10px] bg-red-900/40 text-red-400 px-2 py-1 rounded-full border border-red-900">↓ TENDENCIA</span>}
            </div>
            <p className="text-dash-border text-xs uppercase tracking-widest mb-1">{title}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
    );
}
