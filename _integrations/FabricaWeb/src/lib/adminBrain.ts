import { Product } from '@/data/products';

export interface OrderItem extends Product {
    quantity: number;
    price: number; // Override as number
}

export interface Order {
    id: string;
    date: string;
    customer?: string;
    phone: string;
    address: string;
    deliveryDate: string;
    deliveryTime: string;
    items: OrderItem[];
    notes?: string;
    coupon?: string;
    paymentMethod: string;
    total?: number; // Calculated or stored
}

export interface Financials {
    grossTotal: string; // Formatted
    netProfit: string;
    igv: string;
    subtotal: string;
    _rawTotal: number;
    _rawProfit: number;
}

export class AdminBrain {
    private IGV_RATE = 0.18; // IGV Peru
    private ESTIMATED_COST_RATE = 0.40; // 40% Costo Estimado Legacy

    calculateFinancials(orders: Order[]): Financials {
        let totalRevenue = 0;
        orders.forEach(o => {
            if (o.total) totalRevenue += o.total;
            else if (o.items) o.items.forEach(i => totalRevenue += (i.price * i.quantity));
        });

        const subtotal = totalRevenue / (1 + this.IGV_RATE);
        const igv = totalRevenue - subtotal;
        const costs = totalRevenue * this.ESTIMATED_COST_RATE;
        const netProfit = totalRevenue - costs - igv;

        return {
            grossTotal: this.formatCurrency(totalRevenue),
            subtotal: this.formatCurrency(subtotal),
            igv: this.formatCurrency(igv),
            netProfit: this.formatCurrency(netProfit),
            _rawTotal: totalRevenue,
            _rawProfit: netProfit
        };
    }

    getMonthlyProjection(currentTotal: number): { projectedTotal: string, trend: 'up' | 'down' | 'stable' } {
        const now = new Date();
        const dayOfMonth = now.getDate();
        const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();

        if (dayOfMonth === 0) return { projectedTotal: this.formatCurrency(currentTotal), trend: 'stable' };

        const dailyAverage = currentTotal / dayOfMonth;
        const projected = dailyAverage * daysInMonth;

        return {
            projectedTotal: this.formatCurrency(projected),
            trend: projected > (currentTotal * 1.1) ? 'up' : 'stable'
        };
    }

    getAverageTicket(orders: Order[]): string {
        if (orders.length === 0) return "S/ 0.00";
        let totalRevenue = 0;
        orders.forEach(o => {
            o.items.forEach(i => totalRevenue += (i.price * i.quantity));
        });
        return this.formatCurrency(totalRevenue / orders.length);
    }

    analyzeInventory(orders: Order[]): { criticalItems: string[] } {
        const productCounts: Record<string, number> = {};
        orders.forEach(o => {
            o.items.forEach(i => {
                productCounts[i.title] = (productCounts[i.title] || 0) + i.quantity;
            });
        });

        // Simula alerta si > 5 unidades vendidas hoy
        const critical = Object.entries(productCounts)
            .filter(([_, count]) => count >= 5)
            .map(([name]) => name);

        return { criticalItems: critical };
    }

    exportToCSV(orders: Order[]): void {
        if (orders.length === 0) return;

        const headers = ['Fecha', 'ID', 'Cliente', 'WhatsApp', 'Total', 'Método', 'Items'];
        const rows = orders.map(o => {
            const itemsStr = o.items.map(i => `${i.quantity}x ${i.title}`).join(' + ');
            const total = o.total || o.items.reduce((sum, i) => sum + (i.price * i.quantity), 0);

            return [
                new Date(o.date).toLocaleDateString('es-PE'),
                o.id,
                `"${o.customer || ''}"`,
                o.phone,
                total.toFixed(2),
                o.paymentMethod,
                `"${itemsStr}"`
            ].join(',');
        });

        const blob = new Blob(['\uFEFF' + headers.join(',') + '\n' + rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Pastelito_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }
    // === Advanced Analytics (v2.0) ===

    getWeeklyComparison(orders: Order[]): { thisWeek: string; lastWeek: string; change: number; trend: 'up' | 'down' | 'stable' } {
        const now = new Date();
        const thisWeekStart = new Date(now);
        thisWeekStart.setDate(now.getDate() - now.getDay());
        thisWeekStart.setHours(0, 0, 0, 0);

        const lastWeekStart = new Date(thisWeekStart);
        lastWeekStart.setDate(lastWeekStart.getDate() - 7);

        let thisWeekTotal = 0;
        let lastWeekTotal = 0;

        orders.forEach(o => {
            const d = new Date(o.date);
            const revenue = o.total || o.items?.reduce((s, i) => s + (i.price * i.quantity), 0) || 0;
            if (d >= thisWeekStart) thisWeekTotal += revenue;
            else if (d >= lastWeekStart && d < thisWeekStart) lastWeekTotal += revenue;
        });

        const change = lastWeekTotal > 0 ? ((thisWeekTotal - lastWeekTotal) / lastWeekTotal) * 100 : 0;

        return {
            thisWeek: this.formatCurrency(thisWeekTotal),
            lastWeek: this.formatCurrency(lastWeekTotal),
            change: Math.round(change),
            trend: change > 5 ? 'up' : change < -5 ? 'down' : 'stable'
        };
    }

    getPeakHour(orders: Order[]): { hour: number; label: string; count: number } {
        const hourCounts: Record<number, number> = {};
        orders.forEach(o => {
            const hour = new Date(o.date).getHours();
            hourCounts[hour] = (hourCounts[hour] || 0) + 1;
        });

        let peakHour = 12; // default
        let maxCount = 0;
        Object.entries(hourCounts).forEach(([h, count]) => {
            if (count > maxCount) {
                maxCount = count;
                peakHour = parseInt(h);
            }
        });

        const ampm = peakHour >= 12 ? 'PM' : 'AM';
        const displayHour = peakHour > 12 ? peakHour - 12 : peakHour === 0 ? 12 : peakHour;

        return { hour: peakHour, label: `${displayHour}:00 ${ampm}`, count: maxCount };
    }

    getBestDay(orders: Order[]): { day: string; count: number } {
        const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
        const dayCounts: Record<number, number> = {};

        orders.forEach(o => {
            const day = new Date(o.date).getDay();
            dayCounts[day] = (dayCounts[day] || 0) + 1;
        });

        let bestDay = 0;
        let maxCount = 0;
        Object.entries(dayCounts).forEach(([d, count]) => {
            if (count > maxCount) {
                maxCount = count;
                bestDay = parseInt(d);
            }
        });

        return { day: dayNames[bestDay], count: maxCount };
    }

    // === Smart CEO Analytics (v3.0) ===

    /**
     * Generate a comprehensive executive report combining all metrics.
     */
    getSmartReport(orders: Order[], products: Product[]): string {
        if (orders.length === 0) return "📊 Aún no hay pedidos registrados. ¡El primer pedido está por llegar! 🚀";

        const financials = this.calculateFinancials(orders);
        const projection = this.getMonthlyProjection(financials._rawTotal);
        const avgTicket = this.getAverageTicket(orders);
        const peak = this.getPeakHour(orders);
        const bestDay = this.getBestDay(orders);
        const weekly = this.getWeeklyComparison(orders);
        const ranking = this.getProductRanking(orders);
        const anomalies = this.getAnomalies(orders);

        const trendIcon = weekly.trend === 'up' ? '📈' : weekly.trend === 'down' ? '📉' : '➡️';
        const topProduct = ranking.length > 0 ? ranking[0] : null;

        let report = `📊 **REPORTE EJECUTIVO — Pastelito CEO**\n\n`;
        report += `💰 **Ventas totales:** ${financials.grossTotal} (${orders.length} pedidos)\n`;
        report += `📈 **Utilidad neta:** ${financials.netProfit}\n`;
        report += `🎟️ **Ticket promedio:** ${avgTicket}\n`;
        report += `🔮 **Proyección mensual:** ${projection.projectedTotal}\n\n`;
        report += `${trendIcon} **Semana:** ${weekly.thisWeek} vs ${weekly.lastWeek} (${weekly.change > 0 ? '+' : ''}${weekly.change}%)\n`;
        report += `⏰ **Hora pico:** ${peak.label} (${peak.count} pedidos)\n`;
        report += `📅 **Mejor día:** ${bestDay.day}\n`;

        if (topProduct) {
            report += `\n🏆 **Producto estrella:** ${topProduct.name} (${topProduct.quantity} unidades, ${this.formatCurrency(topProduct.revenue)})\n`;
        }

        if (anomalies.length > 0) {
            report += `\n⚠️ **Alertas:**\n`;
            anomalies.forEach(a => report += `• ${a}\n`);
        }

        // Smart suggestions
        const insights = this.getActionableInsights(orders, products);
        if (insights.length > 0) {
            report += `\n💡 **Sugerencias:**\n`;
            insights.forEach(i => report += `• ${i}\n`);
        }

        return report;
    }

    /**
     * Rank products by revenue and units sold.
     */
    getProductRanking(orders: Order[]): Array<{ name: string; quantity: number; revenue: number; rank: number }> {
        const products: Record<string, { quantity: number; revenue: number }> = {};

        orders.forEach(o => {
            o.items?.forEach(i => {
                const key = i.title;
                if (!products[key]) products[key] = { quantity: 0, revenue: 0 };
                products[key].quantity += i.quantity;
                products[key].revenue += i.price * i.quantity;
            });
        });

        return Object.entries(products)
            .map(([name, data]) => ({ name, ...data, rank: 0 }))
            .sort((a, b) => b.revenue - a.revenue)
            .map((p, i) => ({ ...p, rank: i + 1 }));
    }

    /**
     * Detect anomalies in order patterns.
     */
    getAnomalies(orders: Order[]): string[] {
        const alerts: string[] = [];
        const now = new Date();

        // Check if today has zero orders (during business hours)
        const todayOrders = orders.filter(o => {
            const d = new Date(o.date);
            return d.toDateString() === now.toDateString();
        });

        if (todayOrders.length === 0 && now.getHours() >= 12 && now.getHours() < 20) {
            alerts.push("🔴 Cero pedidos hoy después del mediodía — revisar visibilidad");
        }

        // Check weekly trend
        const weekly = this.getWeeklyComparison(orders);
        if (weekly.change < -30) {
            alerts.push(`📉 Ventas cayeron ${Math.abs(weekly.change)}% vs semana pasada — considerar promoción`);
        } else if (weekly.change > 50) {
            alerts.push(`🚀 Ventas subieron ${weekly.change}% — ¡excelente! Verificar stock suficiente`);
        }

        // Check if a product dominates (>60% of revenue)
        const ranking = this.getProductRanking(orders);
        const totalRevenue = ranking.reduce((s, p) => s + p.revenue, 0);
        if (ranking.length > 0 && totalRevenue > 0) {
            const topShare = (ranking[0].revenue / totalRevenue) * 100;
            if (topShare > 60) {
                alerts.push(`⚠️ ${ranking[0].name} representa ${Math.round(topShare)}% de tus ingresos — diversificar`);
            }
        }

        return alerts;
    }

    /**
     * Generate actionable business insights based on data.
     */
    getActionableInsights(orders: Order[], products: Product[]): string[] {
        const insights: string[] = [];

        // Suggest combos based on frequently bought together
        const pairCounts: Record<string, number> = {};
        orders.forEach(o => {
            const items = o.items?.map(i => i.title) || [];
            for (let i = 0; i < items.length; i++) {
                for (let j = i + 1; j < items.length; j++) {
                    const pair = [items[i], items[j]].sort().join(' + ');
                    pairCounts[pair] = (pairCounts[pair] || 0) + 1;
                }
            }
        });

        const topPair = Object.entries(pairCounts).sort((a, b) => b[1] - a[1])[0];
        if (topPair && topPair[1] >= 3) {
            insights.push(`🎯 "${topPair[0]}" se compran juntos ${topPair[1]} veces — crear un combo con descuento`);
        }

        // Check for out-of-stock products
        const outOfStock = products.filter(p => p.stock === 'out_of_stock');
        if (outOfStock.length > 0) {
            insights.push(`📦 ${outOfStock.length} producto(s) agotados: ${outOfStock.map(p => p.title).join(', ')}`);
        }

        // Check payment method distribution
        const payMethods: Record<string, number> = {};
        orders.forEach(o => {
            payMethods[o.paymentMethod] = (payMethods[o.paymentMethod] || 0) + 1;
        });
        const topMethod = Object.entries(payMethods).sort((a, b) => b[1] - a[1])[0];
        if (topMethod) {
            const share = Math.round((topMethod[1] / orders.length) * 100);
            if (share > 70) {
                insights.push(`💳 ${share}% de tus clientes pagan con ${topMethod[0]} — asegúrate de tener saldo`);
            }
        }

        // Suggest if average ticket is low
        const avgRaw = orders.length > 0
            ? orders.reduce((s, o) => s + (o.total || o.items?.reduce((si, i) => si + i.price * i.quantity, 0) || 0), 0) / orders.length
            : 0;
        if (avgRaw > 0 && avgRaw < 40) {
            insights.push(`💡 Ticket promedio bajo (${this.formatCurrency(avgRaw)}) — promover combos o productos premium`);
        }

        return insights;
    }

    /**
     * Basic demand prediction based on day-of-week patterns.
     */
    predictDemand(orders: Order[]): string {
        if (orders.length < 7) return "📊 Se necesitan al menos 7 pedidos para predecir demanda.";

        const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
        const dayTotals: Record<number, number[]> = {};

        orders.forEach(o => {
            const d = new Date(o.date);
            const day = d.getDay();
            const revenue = o.total || o.items?.reduce((s, i) => s + i.price * i.quantity, 0) || 0;
            if (!dayTotals[day]) dayTotals[day] = [];
            dayTotals[day].push(revenue);
        });

        const now = new Date();
        const tomorrow = (now.getDay() + 1) % 7;
        const tomorrowData = dayTotals[tomorrow] || [];
        const avgTomorrow = tomorrowData.length > 0
            ? tomorrowData.reduce((s, v) => s + v, 0) / tomorrowData.length
            : 0;

        const todayData = dayTotals[now.getDay()] || [];
        const avgToday = todayData.length > 0
            ? todayData.reduce((s, v) => s + v, 0) / todayData.length
            : 0;

        let prediction = `🔮 **Predicción de Demanda:**\n`;
        prediction += `• **Hoy (${dayNames[now.getDay()]}):** ~${this.formatCurrency(avgToday)} esperados\n`;
        prediction += `• **Mañana (${dayNames[tomorrow]}):** ~${this.formatCurrency(avgTomorrow)} esperados\n`;

        if (avgTomorrow > avgToday * 1.2) {
            prediction += `\n📈 Mañana suele ser más fuerte. ¡Prepara stock extra!`;
        } else if (avgTomorrow < avgToday * 0.8) {
            prediction += `\n📉 Mañana suele ser más suave. Buen día para preparar inventario.`;
        }

        return prediction;
    }

    formatCurrency(amount: number): string {
        return new Intl.NumberFormat('es-PE', {
            style: 'currency',
            currency: 'PEN'
        }).format(amount);
    }
}

export const adminBrain = new AdminBrain();
