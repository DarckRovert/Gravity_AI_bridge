import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { adminBrain } from '@/lib/adminBrain';
import { generateWhatsAppLink } from '@/lib/whatsappEngine';
import { products as staticProducts } from '@/data/products';
import { multiTurnEngine } from '@/lib/multiTurnEngine';
import { getOrdersSync } from '@/lib/firebaseOrders';

import { ChatOption } from '@/types/chatbot';
import { SiteConfigContextType } from '@/context/SiteConfigContext';

interface UseChatActionsProps {
    router: ReturnType<typeof useRouter>;
    addMessage: (text: string, sender: 'bot' | 'user', isGodMode?: boolean) => void;
    showNode: (nodeId: string) => void;
    siteConfig: SiteConfigContextType;
    startWizard: (flowId: string) => void;
    setIsOpen: (isOpen: boolean) => void;
    setCurrentOptions: (options: ChatOption[]) => void;
    clearHistory: () => void;
}

export function useChatActions({
    router,
    addMessage,
    showNode,
    siteConfig,
    startWizard,
    setIsOpen,
    setCurrentOptions,
    clearHistory
}: UseChatActionsProps) {

    const handleAction = useCallback((action: string) => {
        const orders = getOrdersSync();
        const stats = adminBrain.calculateFinancials(orders);

        switch (action) {
            case 'menu': router.push('/menu'); setIsOpen(false); break;
            case 'open_tracker': router.push('/tracker'); setIsOpen(false); break;
            case 'admin_start': showNode('admin_start'); break;
            case 'calc_sales':
                addMessage(`💰 Ventas: **${stats.grossTotal}** (${orders.length} pedidos)`, 'bot');
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            case 'calc_profit':
                addMessage(`📉 Utilidad: **${stats.netProfit}** (Margen 60%)`, 'bot');
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            case 'calc_tax':
                addMessage(`🇵🇪 IGV Estimado: **${stats.igv}**`, 'bot');
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            case 'calc_projection':
                const projection = adminBrain.getMonthlyProjection(stats._rawTotal);
                addMessage(`🔮 Proyección: **${projection.projectedTotal}**`, 'bot');
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            case 'whatsapp': {
                const num = siteConfig?.config?.content?.whatsappNumber;
                const link = generateWhatsAppLink(num, 'support', { details: 'Consulta desde el Chatbot' });
                window.open(link, '_blank');
                break;
            }
            case 'track_prompt': showNode('track_prompt'); break;
            case 'open_builder': router.push('/builder'); setIsOpen(false); break;
            case 'start_wizard_producto': startWizard('agregar_producto'); break;
            case 'start_wizard_cupon': startWizard('crear_cupon'); break;
            case 'start_wizard_zona': startWizard('agregar_zona'); break;
            case 'start_wizard_banner': startWizard('agregar_banner'); break;
            case 'calc_inventory': {
                const currentProducts = siteConfig?.config?.products || staticProducts;
                const outOfStock = currentProducts.filter((p: { stock: string }) => p.stock === 'out_of_stock');
                const lowStock = currentProducts.filter((p: { stock: string }) => p.stock === 'low');
                const available = currentProducts.filter((p: { stock: string }) => p.stock === 'available');
                let msg = `📦 **Inventario actual:**\n• ✅ Disponibles: **${available.length}** productos\n• ⚠️ Stock bajo: **${lowStock.length}**`;
                if (lowStock.length > 0) msg += ` (${lowStock.map((p: { title: string }) => p.title).join(', ')})`;
                msg += `\n• 🔴 Agotados: **${outOfStock.length}**`;
                if (outOfStock.length > 0) msg += ` (${outOfStock.map((p: { title: string }) => p.title).join(', ')})`;
                addMessage(msg, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_ticket': {
                const avgTicket = adminBrain.getAverageTicket(orders);
                addMessage(`🎟️ Ticket promedio: **${avgTicket}** por pedido`, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_weekly': {
                const weekly = adminBrain.getWeeklyComparison(orders);
                const trendIcon = weekly.trend === 'up' ? '📈' : weekly.trend === 'down' ? '📉' : '➡️';
                addMessage(`${trendIcon} **Comparación semanal:**\n• Esta semana: **${weekly.thisWeek}**\n• Semana pasada: **${weekly.lastWeek}**\n• Cambio: **${weekly.change > 0 ? '+' : ''}${weekly.change}%**`, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_peak': {
                const peak = adminBrain.getPeakHour(orders);
                addMessage(`⏰ Tu **hora pico** es a las **${peak.label}** con ${peak.count} pedidos registrados.`, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_bestday': {
                const best = adminBrain.getBestDay(orders);
                addMessage(`📅 Tu mejor día es el **${best.day}** con ${best.count} pedidos. ¡Prepárate cada semana!`, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'clear_chat': {
                clearHistory();
                addMessage("🗑️ Historial de conversación limpiado. ¿En qué puedo ayudarte?", 'bot');
                break;
            }
            case 'guide_wallet': showNode('admin_wallet_guide'); break;
            case 'open_web3_guide':
                router.push('/admin/guide');
                setIsOpen(false);
                addMessage("📄 He abierto la guía técnica interna. ¡Aquí tienes todos los pasos!", 'bot');
                break;
            // === Smart CEO v3.0 ===
            case 'calc_smart_report': {
                const currentProducts = siteConfig?.config?.products || staticProducts;
                const report = adminBrain.getSmartReport(orders, currentProducts);
                addMessage(report, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_ranking': {
                const ranking = adminBrain.getProductRanking(orders);
                if (ranking.length === 0) {
                    addMessage("📊 Aún no hay datos de productos vendidos.", 'bot', true);
                } else {
                    const medals = ['🥇', '🥈', '🥉'];
                    let msg = "🏆 **Ranking de Productos:**\n";
                    ranking.slice(0, 10).forEach((p, i) => {
                        const medal = medals[i] || `${i + 1}.`;
                        msg += `${medal} **${p.name}** — ${p.quantity} uds, ${adminBrain.formatCurrency(p.revenue)}\n`;
                    });
                    addMessage(msg, 'bot', true);
                }
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_anomalies': {
                const anomalies = adminBrain.getAnomalies(orders);
                if (anomalies.length === 0) {
                    addMessage("✅ **Todo normal.** No se detectaron anomalías en tus ventas. ¡Sigue así!", 'bot', true);
                } else {
                    let msg = "⚠️ **Anomalías detectadas:**\n";
                    anomalies.forEach(a => msg += `• ${a}\n`);
                    addMessage(msg, 'bot', true);
                }
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_insights': {
                const currentProds = siteConfig?.config?.products || staticProducts;
                const insights = adminBrain.getActionableInsights(orders, currentProds);
                if (insights.length === 0) {
                    addMessage("💡 Aún no hay suficientes datos para generar sugerencias. ¡Sigue vendiendo!", 'bot', true);
                } else {
                    let msg = "💡 **Sugerencias para tu negocio:**\n";
                    insights.forEach(i => msg += `• ${i}\n`);
                    addMessage(msg, 'bot', true);
                }
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'calc_demand': {
                const demand = adminBrain.predictDemand(orders);
                addMessage(demand, 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
            case 'export_csv': {
                adminBrain.exportToCSV(orders);
                addMessage("📥 ¡Reporte CSV descargado! Revisa tu carpeta de descargas.", 'bot', true);
                setCurrentOptions([{ text: "🔙 Menú Admin", next: "admin_start" }]);
                break;
            }
        }

        // Handle wizard option selections
        if (action.startsWith('wizard_select_')) {
            const value = action.replace('wizard_select_', '');
            if (multiTurnEngine.isActive()) {
                const stepResult = multiTurnEngine.processInput(value);
                if (stepResult.type === 'next_step') {
                    addMessage(stepResult.message, 'bot', true);
                    if (stepResult.options) {
                        setCurrentOptions(stepResult.options.map(o => ({ text: o.text, action: `wizard_select_${o.value}` })));
                    }
                } else if (stepResult.type === 'summary') {
                    addMessage(stepResult.message, 'bot', true);
                }
            }
            return;
        }
    }, [router, addMessage, showNode, siteConfig, startWizard, setIsOpen, setCurrentOptions, clearHistory]);

    return { handleAction };
}
