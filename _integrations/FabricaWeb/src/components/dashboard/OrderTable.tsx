import { Order } from '@/lib/adminBrain';

export function OrderTable({ orders }: { orders: Order[] }) {
    return (
        <div className="lg:col-span-2 bg-dash-card border border-dash-border rounded-2xl p-6 overflow-hidden">
            <div className="flex justify-between items-center mb-6 border-bottom border-dash-border pb-4">
                <h2 className="text-xl font-playfair text-secondary">Pedidos Recientes</h2>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-dash-border border-b border-dash-border">
                        <tr>
                            <th className="pb-3 px-2">ID</th>
                            <th className="pb-3 px-2">Cliente</th>
                            <th className="pb-3 px-2">Fecha</th>
                            <th className="pb-3 px-2">Método</th>
                            <th className="pb-3 px-2 text-right">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.slice(0, 10).map((order) => {
                            const orderTotal = order.total || order.items?.reduce((s, i) => s + (i.price * i.quantity), 0) || 0;
                            return (
                                <tr key={order.id} className="hover:bg-white/5 transition-colors border-b border-dash-border/30">
                                    <td className="py-4 px-2 font-mono text-xs opacity-60">#{order.id.slice(-6)}</td>
                                    <td className="py-4 px-2 font-medium">{order.customer || 'Anónimo'}</td>
                                    <td className="py-4 px-2 opacity-80">{new Date(order.date).toLocaleDateString()}</td>
                                    <td className="py-4 px-2">
                                        <span className="px-2 py-0.5 rounded-full bg-blue-900/30 text-blue-300 text-[10px] border border-blue-900/50 uppercase">
                                            {order.paymentMethod}
                                        </span>
                                    </td>
                                    <td className="py-4 px-2 text-right font-bold">S/ {orderTotal.toFixed(2)}</td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
