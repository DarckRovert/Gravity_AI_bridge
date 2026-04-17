import { adminBrain, Order } from '@/lib/adminBrain';

export function InventoryAlerts({ orders }: { orders: Order[] }) {
    const alerts = adminBrain.analyzeInventory(orders);

    return (
        <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
            <h2 className="text-xl font-playfair text-secondary mb-6">Alertas de Inventario</h2>
            <div className="space-y-4">
                {alerts.criticalItems.length > 0 ? (
                    alerts.criticalItems.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-3 bg-red-900/20 border border-red-900/50 p-3 rounded-lg">
                            <span className="text-xl">⚠️</span>
                            <div>
                                <p className="text-sm font-bold text-red-200">{item}</p>
                                <p className="text-[10px] text-red-400 opacity-80 uppercase font-bold">Alta Rotación</p>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-8 text-gray-500 italic">
                        <span className="text-2xl mb-2 opacity-50">✅</span>
                        <p className="text-sm">Stock bajo control</p>
                    </div>
                )}
            </div>
        </div>
    );
}
