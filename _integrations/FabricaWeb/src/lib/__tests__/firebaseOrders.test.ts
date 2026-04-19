import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createOrder, getOrders, getOrderById, updateOrderStatus } from '../firebaseOrders';

// Mock the firebase module
vi.mock('../firebase', () => ({
    isFirebaseConfigured: vi.fn(() => false),
    firestore: {},
}));

describe('firebaseOrders (LocalStorage Fallback)', () => {
    beforeEach(() => {
        // Mock localStorage
        let store: Record<string, string> = {};

        global.localStorage = {
            getItem: vi.fn((key: string) => store[key] || null),
            setItem: vi.fn((key: string, value: string) => {
                store[key] = value.toString();
            }),
            removeItem: vi.fn((key: string) => {
                delete store[key];
            }),
            clear: vi.fn(() => {
                store = {};
            }),
            length: 0,
            key: vi.fn(),
        } as unknown as Storage;

        localStorage.clear();
    });

    it('should create an order and save it to localStorage', async () => {
        const orderData = {
            id: 'ord-123',
            customer: 'Juan',
            phone: '999888777',
            address: 'Av. Siempre Viva 123',
            deliveryDate: '2025-05-05',
            deliveryTime: 'tarde',
            deliveryZone: 'Surco',
            items: [{ id: 'torta', title: 'Torta', price: 50, quantity: 1, category: 'tortas', description: 'Torta', image: '/img/torta.png', stock: 'available' as const, featured: false }],
            total: 50,
            date: new Date().toISOString(),
            paymentMethod: 'Yape'
        };

        const newOrder = await createOrder(orderData);
        expect(newOrder.id).toBe('ord-123');
        expect(newOrder.status).toBe('nuevo');
        expect(newOrder.paymentConfirmed).toBe(false);

        // Verify it was saved
        const storedOrders = JSON.parse(localStorage.getItem('dm_orders') || '[]');
        expect(storedOrders).toHaveLength(1);
        expect(storedOrders[0].id).toBe('ord-123');
    });

    it('should get orders from localStorage', async () => {
        const orderData = { id: 'ord-1', total: 100, status: 'nuevo', paymentMethod: 'Efectivo' };
        localStorage.setItem('dm_orders', JSON.stringify([orderData]));

        const orders = await getOrders();
        expect(orders).toHaveLength(1);
        expect(orders[0].id).toBe('ord-1');
    });

    it('should get a single order by ID', async () => {
        const orderData1 = { id: 'ord-1', total: 100, status: 'nuevo', paymentMethod: 'Efectivo' };
        const orderData2 = { id: 'ord-2', total: 200, status: 'confirmado', paymentMethod: 'Yape' };
        localStorage.setItem('dm_orders', JSON.stringify([orderData1, orderData2]));

        const order = await getOrderById('ord-2');
        expect(order).not.toBeNull();
        expect(order?.total).toBe(200);
    });

    it('should update order status', async () => {
        const orderData = { id: 'ord-1', status: 'nuevo', paymentConfirmed: false };
        localStorage.setItem('dm_orders', JSON.stringify([orderData]));

        const updated = await updateOrderStatus('ord-1', 'entregado');
        expect(updated).toBe(true);

        const storedOrders = JSON.parse(localStorage.getItem('dm_orders') || '[]');
        expect(storedOrders[0].status).toBe('entregado');
    });
});
