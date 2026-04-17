"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { isValidSessionToken } from '@/lib/auth';
import { isFirebaseConfigured } from '@/lib/firebase';
import { onAdminAuthStateChanged, firebaseAdminLogout } from '@/lib/firebaseAuth';
import { adminBrain, Order, Financials } from '@/lib/adminBrain';
import { KPIItem } from '@/components/dashboard/KPIItem';
import { OrderTable } from '@/components/dashboard/OrderTable';
import { InventoryAlerts } from '@/components/dashboard/InventoryAlerts';

// Lazy-loaded heavy tabs (only bundled when the user visits that tab)
const ProductManager = dynamic(() => import('@/components/dashboard/ProductManager').then(m => ({ default: m.ProductManager })), { ssr: false, loading: () => <div className="text-dash-border p-8 text-center">Cargando...</div> });
const CouponManager = dynamic(() => import('@/components/dashboard/CouponManager').then(m => ({ default: m.CouponManager })), { ssr: false, loading: () => <div className="text-dash-border p-8 text-center">Cargando...</div> });
const QuickThemeEditor = dynamic(() => import('@/components/dashboard/QuickThemeEditor').then(m => ({ default: m.QuickThemeEditor })), { ssr: false, loading: () => <div className="text-dash-border p-8 text-center">Cargando...</div> });
const AdvancedAnalytics = dynamic(() => import('@/components/dashboard/AdvancedAnalytics').then(m => ({ default: m.AdvancedAnalytics })), { ssr: false, loading: () => <div className="text-dash-border p-8 text-center">Cargando...</div> });
const OrderPipeline = dynamic(() => import('@/components/dashboard/OrderPipeline').then(m => ({ default: m.OrderPipeline })), { ssr: false, loading: () => <div className="text-dash-border p-8 text-center">Cargando...</div> });

interface Projection {
    projectedTotal: string;
    trend: 'up' | 'down' | 'stable';
}

type TabId = 'resumen' | 'pedidos' | 'productos' | 'cupones' | 'tema' | 'analytics';

const tabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'resumen', label: 'Resumen', icon: '📊' },
    { id: 'pedidos', label: 'Pedidos', icon: '📦' },
    { id: 'productos', label: 'Productos', icon: '🛒' },
    { id: 'cupones', label: 'Cupones', icon: '🏷️' },
    { id: 'tema', label: 'Tema', icon: '🎨' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
];

// Quick access sidebar items
const quickActions = [
    { icon: '🏠', label: 'Inicio', action: '/' },
    { icon: '📋', label: 'Menú', action: '/menu' },
    { icon: '🎂', label: 'Builder', action: '/builder' },
    { icon: '📦', label: 'Tracker', action: '/tracker' },
];

export default function Dashboard() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [stats, setStats] = useState<Financials | null>(null);
    const [projection, setProjection] = useState<Projection | null>(null);
    const [avgTicket, setAvgTicket] = useState('S/ 0.00');
    const [activeTab, setActiveTab] = useState<TabId>('resumen');
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [useFirebase] = useState(() => isFirebaseConfigured());
    const router = useRouter();

    useEffect(() => {
        if (useFirebase) {
            // Firebase Auth: wait for auth state
            const unsub = onAdminAuthStateChanged((user) => {
                if (!user) router.push('/admin');
            });
            return unsub;
        } else {
            // Legacy localStorage session
            const session = localStorage.getItem('dm_admin_session');
            if (!session) {
                router.push('/admin');
                return;
            }
            if (!isValidSessionToken(session)) {
                localStorage.removeItem('dm_admin_session');
                router.push('/admin');
                return;
            }
        }

        // Load Data from Firestore (or localStorage fallback)
        const loadOrders = async () => {
            const { getOrders } = await import('@/lib/firebaseOrders');
            const firestoreOrders = await getOrders();
            const parsedOrders: Order[] = firestoreOrders.map(o => ({
                id: o.id,
                customer: o.customer,
                items: o.items,
                total: o.total,
                date: o.date || o.createdAt,
                phone: o.phone,
                address: o.deliveryZone || '',
                deliveryDate: o.deliveryDate,
                deliveryTime: o.deliveryTime,
                paymentMethod: o.paymentMethod || 'No especificado',
            }));
            setOrders(parsedOrders);
            const financialStats = adminBrain.calculateFinancials(parsedOrders);
            setStats(financialStats);
            setProjection(adminBrain.getMonthlyProjection(financialStats._rawTotal));
            setAvgTicket(adminBrain.getAverageTicket(parsedOrders));
        };
        loadOrders();
    }, [router, useFirebase]);

    const handleLogout = async () => {
        if (useFirebase) {
            await firebaseAdminLogout();
        } else {
            localStorage.removeItem('dm_admin_session');
        }
        router.push('/admin');
    };

    const showToast = (msg: string, type: 'success' | 'error') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    if (!stats) return <div className="min-h-screen bg-dash-bg text-white flex items-center justify-center">Cargando datos...</div>;

    return (
        <div className="min-h-screen bg-dash-bg flex">
            {/* Sidebar */}
            <aside
                className={`fixed lg:sticky top-0 left-0 h-screen bg-dash-card border-r border-dash-border flex flex-col items-center py-6 z-40 transition-all duration-300 ${sidebarOpen ? 'w-48' : 'w-16'
                    }`}
            >
                {/* Toggle */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="text-dash-border hover:text-secondary transition-colors mb-6 text-sm"
                    title={sidebarOpen ? 'Colapsar' : 'Expandir'}
                >
                    {sidebarOpen ? '◀' : '▶'}
                </button>

                {/* Tab Shortcuts */}
                <div className="flex flex-col gap-1 w-full px-2 mb-6">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${activeTab === tab.id
                                ? 'bg-secondary/20 text-secondary'
                                : 'text-dash-border hover:text-white hover:bg-dash-bg/50'
                                }`}
                            title={tab.label}
                        >
                            <span className="text-base flex-shrink-0">{tab.icon}</span>
                            {sidebarOpen && <span className="text-xs font-medium truncate">{tab.label}</span>}
                        </button>
                    ))}
                </div>

                {/* Divider */}
                <div className="w-8 border-t border-dash-border/50 mb-4" />

                {/* Quick Nav */}
                <p className={`text-dash-border text-[9px] uppercase tracking-widest mb-2 ${sidebarOpen ? 'px-4 self-start' : 'hidden'}`}>
                    Accesos
                </p>
                <div className="flex flex-col gap-1 w-full px-2">
                    {quickActions.map(qa => (
                        <button
                            key={qa.action}
                            onClick={() => router.push(qa.action)}
                            className="flex items-center gap-3 px-3 py-2 rounded-xl text-dash-border hover:text-white hover:bg-dash-bg/50 text-sm transition-all"
                            title={qa.label}
                        >
                            <span className="text-base flex-shrink-0">{qa.icon}</span>
                            {sidebarOpen && <span className="text-xs truncate">{qa.label}</span>}
                        </button>
                    ))}
                </div>

                {/* Spacer */}
                <div className="flex-1" />

                {/* Logout */}
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-3 py-2 rounded-xl text-red-400/70 hover:text-red-400 hover:bg-red-900/10 text-sm transition-all w-full mx-2"
                    title="Cerrar Sesión"
                >
                    <span className="text-base flex-shrink-0">🚪</span>
                    {sidebarOpen && <span className="text-xs truncate">Salir</span>}
                </button>
            </aside>

            {/* Sidebar overlay on mobile */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/40 z-30 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main Content */}
            <main className={`flex-1 text-[#e0e0e0] p-6 lg:p-10 font-poppins transition-all duration-300 ${sidebarOpen ? 'lg:ml-0' : ''}`}>
                {/* Toast */}
                {toast && (
                    <div className={`fixed top-6 right-6 z-50 px-4 py-3 rounded-xl text-sm font-medium shadow-2xl animate-fade-up ${toast.type === 'success' ? 'bg-green-900/90 text-green-300 border border-green-700' : 'bg-red-900/90 text-red-300 border border-red-700'
                        }`}>
                        {toast.type === 'success' ? '✅' : '❌'} {toast.msg}
                    </div>
                )}

                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-3">
                        {/* Mobile sidebar toggle */}
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="lg:hidden text-dash-border hover:text-white transition-colors text-xl"
                        >
                            ☰
                        </button>
                        <div>
                            <h1 className="text-3xl font-playfair font-bold text-secondary">CFO Dashboard</h1>
                            <p className="text-dash-border text-sm">Panel administrativo completo</p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => adminBrain.exportToCSV(orders)}
                            className="bg-secondary text-dash-bg px-4 py-2 rounded-lg text-sm font-bold hover:bg-white transition-all flex items-center gap-2"
                        >
                            📂 Exportar CSV
                        </button>
                        <button
                            onClick={handleLogout}
                            className="hidden lg:block bg-dash-card border border-dash-border px-4 py-2 rounded-lg text-sm hover:bg-red-900/20 hover:border-red-900/50 transition-all"
                        >
                            Cerrar Sesión
                        </button>
                    </div>
                </div>

                {/* Tab Navigation (horizontal — still visible on top for clarity) */}
                <div className="flex gap-1 bg-dash-card border border-dash-border rounded-xl p-1 mb-8 overflow-x-auto">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                ? 'bg-secondary text-dash-bg shadow-lg'
                                : 'text-dash-border hover:text-white hover:bg-dash-bg/50'
                                }`}
                        >
                            <span>{tab.icon}</span>
                            <span>{tab.label}</span>
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                {activeTab === 'resumen' && (
                    <div className="space-y-8 animate-fade-up">
                        {/* KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                            <KPIItem title="Ventas Totales" value={stats.grossTotal} color="text-secondary" icon="💰" />
                            <KPIItem title="Utilidad Neta (Est.)" value={stats.netProfit} color="text-[#43A047]" icon="📈" />
                            <KPIItem title="IGV (18%)" value={stats.igv} color="text-dash-border" icon="🏛️" />
                            <KPIItem title="Proyección Mensual" value={projection?.projectedTotal || '0'} color="text-amber-400" icon="🚀" trend={projection?.trend} />
                            <KPIItem title="Ticket Promedio" value={avgTicket} color="text-[#FF8F00]" icon="🎫" />
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Orders Table */}
                            <OrderTable orders={orders} />

                            {/* Popular Products / Alerts */}
                            <div className="space-y-6">
                                <InventoryAlerts orders={orders} />
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'pedidos' && (
                    <div className="animate-fade-up">
                        <OrderPipeline onToast={showToast} />
                    </div>
                )}

                {activeTab === 'productos' && (
                    <div className="animate-fade-up">
                        <ProductManager onToast={showToast} />
                    </div>
                )}

                {activeTab === 'cupones' && (
                    <div className="animate-fade-up max-w-2xl">
                        <CouponManager onToast={showToast} />
                    </div>
                )}

                {activeTab === 'tema' && (
                    <div className="animate-fade-up max-w-xl">
                        <QuickThemeEditor onToast={showToast} />
                    </div>
                )}

                {activeTab === 'analytics' && (
                    <div className="animate-fade-up max-w-3xl">
                        <AdvancedAnalytics orders={orders} />
                    </div>
                )}
            </main>
        </div>
    );
}
