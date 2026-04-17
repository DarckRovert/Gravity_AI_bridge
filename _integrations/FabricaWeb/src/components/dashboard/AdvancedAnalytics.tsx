"use client";

import { adminBrain, Order } from '@/lib/adminBrain';

interface AdvancedAnalyticsProps {
    orders: Order[];
}

export function AdvancedAnalytics({ orders }: AdvancedAnalyticsProps) {
    const weeklyData = adminBrain.getWeeklyComparison(orders);
    const peakHour = adminBrain.getPeakHour(orders);
    const bestDay = adminBrain.getBestDay(orders);
    const avgTicket = adminBrain.getAverageTicket(orders);

    // Calculate product popularity
    const productCounts: Record<string, number> = {};
    orders.forEach(o => {
        o.items?.forEach(i => {
            productCounts[i.title] = (productCounts[i.title] || 0) + i.quantity;
        });
    });
    const topProducts = Object.entries(productCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5);
    const maxProductCount = topProducts.length > 0 ? topProducts[0][1] : 1;

    // Weekly comparison bar chart data
    const thisWeekNum = parseFloat(weeklyData.thisWeek.replace(/[^0-9.]/g, ''));
    const lastWeekNum = parseFloat(weeklyData.lastWeek.replace(/[^0-9.]/g, ''));
    const maxWeek = Math.max(thisWeekNum, lastWeekNum, 1);

    const trendIcon = weeklyData.trend === 'up' ? '📈' : weeklyData.trend === 'down' ? '📉' : '➡️';
    const trendColor = weeklyData.trend === 'up' ? 'text-green-400' : weeklyData.trend === 'down' ? 'text-red-400' : 'text-dash-border';

    return (
        <div className="space-y-6">
            {/* Weekly Comparison */}
            <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
                <h2 className="text-xl font-playfair font-bold text-secondary mb-4">📊 Comparación Semanal</h2>
                <div className="space-y-3">
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-dash-border">Esta Semana</span>
                            <span className="text-white font-bold">{weeklyData.thisWeek}</span>
                        </div>
                        <div className="h-6 bg-dash-bg rounded-lg overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-secondary/60 to-secondary rounded-lg transition-all duration-700"
                                style={{ width: `${Math.max((thisWeekNum / maxWeek) * 100, 2)}%` }}
                            />
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between text-sm mb-1">
                            <span className="text-dash-border">Semana Pasada</span>
                            <span className="text-white font-bold">{weeklyData.lastWeek}</span>
                        </div>
                        <div className="h-6 bg-dash-bg rounded-lg overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-dash-border/40 to-dash-border/60 rounded-lg transition-all duration-700"
                                style={{ width: `${Math.max((lastWeekNum / maxWeek) * 100, 2)}%` }}
                            />
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2 mt-4">
                    <span className="text-lg">{trendIcon}</span>
                    <span className={`text-sm font-bold ${trendColor}`}>
                        {weeklyData.change > 0 ? '+' : ''}{weeklyData.change}% vs semana anterior
                    </span>
                </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-dash-card border border-dash-border rounded-2xl p-4 text-center">
                    <span className="text-2xl mb-2 block">⏰</span>
                    <p className="text-dash-border text-[10px] uppercase tracking-wider">Hora Pico</p>
                    <p className="text-white font-bold text-lg">{peakHour.label}</p>
                    <p className="text-dash-border text-xs">{peakHour.count} pedidos</p>
                </div>
                <div className="bg-dash-card border border-dash-border rounded-2xl p-4 text-center">
                    <span className="text-2xl mb-2 block">📅</span>
                    <p className="text-dash-border text-[10px] uppercase tracking-wider">Mejor Día</p>
                    <p className="text-white font-bold text-lg">{bestDay.day}</p>
                    <p className="text-dash-border text-xs">{bestDay.count} pedidos</p>
                </div>
                <div className="bg-dash-card border border-dash-border rounded-2xl p-4 text-center">
                    <span className="text-2xl mb-2 block">🎫</span>
                    <p className="text-dash-border text-[10px] uppercase tracking-wider">Ticket Prom.</p>
                    <p className="text-white font-bold text-lg">{avgTicket}</p>
                </div>
            </div>

            {/* Top Products */}
            <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
                <h3 className="text-lg font-playfair font-bold text-secondary mb-4">🏆 Top 5 Productos</h3>
                {topProducts.length === 0 ? (
                    <p className="text-center text-dash-border py-4">Sin datos de ventas aún</p>
                ) : (
                    <div className="space-y-3">
                        {topProducts.map(([name, count], i) => (
                            <div key={name} className="flex items-center gap-3">
                                <span className="text-secondary font-bold text-sm w-5">{i + 1}.</span>
                                <div className="flex-1">
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white truncate">{name}</span>
                                        <span className="text-dash-border">{count} uds</span>
                                    </div>
                                    <div className="h-2 bg-dash-bg rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-secondary/50 to-secondary rounded-full transition-all duration-500"
                                            style={{ width: `${(count / maxProductCount) * 100}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
