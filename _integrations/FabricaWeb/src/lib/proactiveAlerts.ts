// ⚡ ProactiveAlerts — Pastelito AI v2.0
// Genera alertas inteligentes para el admin basándose en datos reales

import { Product } from '@/data/products';

interface OrderData {
    items: { id: string; title: string; quantity: number; price: number }[];
    date: string;
    total?: number;
}

export interface Alert {
    type: 'critical' | 'warning' | 'success' | 'info';
    emoji: string;
    message: string;
    action?: string; // Suggested command
}

// Fechas especiales de Perú y comercio
const SPECIAL_DATES: { month: number; day: number; name: string; theme?: string }[] = [
    { month: 2, day: 14, name: 'San Valentín 💝', theme: 'san_valentin' },
    { month: 3, day: 8, name: 'Día de la Mujer 💐' },
    { month: 5, day: 11, name: 'Día de la Madre 🌹' },
    { month: 6, day: 15, name: 'Día del Padre 👔' },
    { month: 7, day: 28, name: 'Fiestas Patrias 🇵🇪', theme: 'patrio' },
    { month: 7, day: 29, name: 'Fiestas Patrias 🇵🇪', theme: 'patrio' },
    { month: 10, day: 31, name: 'Halloween 🎃' },
    { month: 12, day: 25, name: 'Navidad 🎄', theme: 'navidad' },
    { month: 12, day: 31, name: 'Año Nuevo 🎆' },
];

export class ProactiveAlerts {
    /**
     * Generate all relevant alerts for the admin dashboard.
     */
    getAlerts(products: Product[], orders: OrderData[]): Alert[] {
        const alerts: Alert[] = [];

        // 1. Stock alerts
        const outOfStock = products.filter(p => p.stock === 'out_of_stock');
        const lowStock = products.filter(p => p.stock === 'low');

        if (outOfStock.length > 0) {
            alerts.push({
                type: 'critical',
                emoji: '🔴',
                message: `Tienes **${outOfStock.length} producto${outOfStock.length > 1 ? 's' : ''}** agotado${outOfStock.length > 1 ? 's' : ''}: ${outOfStock.map(p => p.title).join(', ')}`,
                action: `Reponer stock: di "reponer ${outOfStock[0].title}"`
            });
        }

        if (lowStock.length > 0) {
            alerts.push({
                type: 'warning',
                emoji: '🟡',
                message: `**${lowStock.length} producto${lowStock.length > 1 ? 's' : ''}** con stock bajo: ${lowStock.map(p => p.title).join(', ')}`,
            });
        }

        // 2. Sales trend alerts
        const today = new Date();
        const oneDayAgo = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        const twoDaysAgo = new Date(today.getTime() - 2 * 24 * 60 * 60 * 1000);

        const ordersToday = orders.filter(o => new Date(o.date) >= oneDayAgo);
        const ordersYesterday = orders.filter(o => {
            const d = new Date(o.date);
            return d >= twoDaysAgo && d < oneDayAgo;
        });

        if (orders.length > 0 && ordersToday.length === 0) {
            const hoursSinceLastOrder = this.hoursSinceLastOrder(orders);
            if (hoursSinceLastOrder > 48) {
                alerts.push({
                    type: 'warning',
                    emoji: '📉',
                    message: `No has tenido pedidos en las últimas **${Math.floor(hoursSinceLastOrder)} horas**. ¿Quizás crear una promoción?`,
                    action: 'Crea un cupón de descuento para reactivar ventas'
                });
            }
        }

        if (ordersToday.length > 0 && ordersYesterday.length > 0) {
            const todayRevenue = this.sumRevenue(ordersToday);
            const yesterdayRevenue = this.sumRevenue(ordersYesterday);
            const change = ((todayRevenue - yesterdayRevenue) / yesterdayRevenue) * 100;

            if (change > 20) {
                alerts.push({
                    type: 'success',
                    emoji: '🚀',
                    message: `¡Felicidades! Hoy vas un **${change.toFixed(0)}% arriba** vs ayer. ¡Sigue así!`
                });
            }
        }

        // 3. Trending product alert
        if (orders.length >= 3) {
            const productCounts: Record<string, number> = {};
            const recentOrders = orders.slice(-10);
            recentOrders.forEach(o => {
                o.items?.forEach(i => {
                    productCounts[i.title] = (productCounts[i.title] || 0) + i.quantity;
                });
            });

            const sorted = Object.entries(productCounts).sort((a, b) => b[1] - a[1]);
            if (sorted.length > 0) {
                const topProduct = sorted[0][0];
                const topCount = sorted[0][1];
                const isFeatured = products.find(p => p.title === topProduct)?.featured;

                if (!isFeatured && topCount >= 3) {
                    alerts.push({
                        type: 'info',
                        emoji: '💡',
                        message: `**${topProduct}** lleva ${topCount} ventas recientes. ¿Lo pongo en destacados?`,
                        action: `Destaca "${topProduct}"`
                    });
                }
            }
        }

        // 4. Upcoming special date
        const upcomingDate = this.getUpcomingSpecialDate();
        if (upcomingDate) {
            const daysUntil = upcomingDate.daysUntil;
            if (daysUntil <= 7 && daysUntil > 0) {
                alerts.push({
                    type: 'info',
                    emoji: '📅',
                    message: `**${upcomingDate.name}** es en **${daysUntil} día${daysUntil > 1 ? 's' : ''}**. ${upcomingDate.theme ? '¿Activo el modo temático?' : '¿Preparamos algo especial?'}`,
                    action: upcomingDate.theme ? `Tema ${upcomingDate.theme}` : undefined
                });
            }
        }

        return alerts;
    }

    /**
     * Format all alerts into a single chat message.
     */
    formatAlertsSummary(alerts: Alert[]): string {
        if (alerts.length === 0) {
            return '✅ Todo en orden, jefe. No hay alertas pendientes.';
        }

        let msg = `📋 **${alerts.length} alerta${alerts.length > 1 ? 's' : ''}:**\n\n`;
        alerts.forEach(a => {
            msg += `${a.emoji} ${a.message}\n`;
            if (a.action) msg += `  ↳ _${a.action}_\n`;
        });

        return msg;
    }

    private hoursSinceLastOrder(orders: OrderData[]): number {
        if (orders.length === 0) return Infinity;
        const lastDate = new Date(orders[orders.length - 1].date);
        return (Date.now() - lastDate.getTime()) / (1000 * 60 * 60);
    }

    private sumRevenue(orders: OrderData[]): number {
        return orders.reduce((sum, o) => {
            if (o.total) return sum + o.total;
            return sum + (o.items?.reduce((s, i) => s + (i.price * i.quantity), 0) || 0);
        }, 0);
    }

    private getUpcomingSpecialDate(): { name: string; theme?: string; daysUntil: number } | null {
        const now = new Date();
        let closest: { name: string; theme?: string; daysUntil: number } | null = null;

        for (const sd of SPECIAL_DATES) {
            const target = new Date(now.getFullYear(), sd.month - 1, sd.day);
            if (target < now) {
                target.setFullYear(target.getFullYear() + 1);
            }
            const daysUntil = Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

            if (!closest || daysUntil < closest.daysUntil) {
                closest = { name: sd.name, theme: sd.theme, daysUntil };
            }
        }

        return closest;
    }
}

export const proactiveAlerts = new ProactiveAlerts();
