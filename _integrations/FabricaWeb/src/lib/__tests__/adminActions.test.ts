import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AdminActions } from '../adminActions';
import { SiteConfigContextType } from '@/context/SiteConfigContext';
import { Product } from '@/data/products';

describe('AdminActions', () => {
    let mockCtx: SiteConfigContextType;
    let actions: AdminActions;

    const mockProduct: Product = {
        id: 'torta-fresa',
        title: 'Torta de Fresa',
        category: 'tortas',
        price: 50,
        description: 'Deliciosa',
        image: '/img',
        stock: 'available',
        featured: false
    };

    beforeEach(() => {
        mockCtx = {
            config: {
                products: [mockProduct],
                coupons: [],
                promotions: [],
                deliveryZones: [],
                testimonials: [],
                theme: { primary: '#000', secondary: '#000', accent: '#000', paper: '#fff', darkMode: false },
                content: { businessName: 'Pastelito' },
                layout: { sections: [], showNewsletter: false },
                actionLog: [],
            },
            updateProduct: vi.fn(),
            addProduct: vi.fn(),
            removeProduct: vi.fn(),
            addCoupon: vi.fn(),
            removeCoupon: vi.fn(),
            setTheme: vi.fn(),
            resetTheme: vi.fn(),
            setContent: vi.fn(),
            setSectionVisibility: vi.fn(),
            setShowNewsletter: vi.fn(),
            addPromotion: vi.fn(),
            removePromotion: vi.fn(),
            addZone: vi.fn(),
            updateZone: vi.fn(),
            addTestimonial: vi.fn(),
            logAction: vi.fn(),
            resetAll: vi.fn(),
        } as unknown as SiteConfigContextType;

        actions = new AdminActions(mockCtx);

        // Mock localStorage for getOrders() used in some actions
        global.localStorage = {
            getItem: vi.fn(() => '[]'),
            setItem: vi.fn(),
            removeItem: vi.fn(),
            clear: vi.fn(),
            length: 0,
            key: vi.fn(),
        };
    });

    describe('Products', () => {
        it('should change price successfully', () => {
            const result = actions.execute('cambiar_precio', { product: 'fresa', price: 60, rawText: '' });
            expect(result.success).toBe(true);
            expect(mockCtx.updateProduct).toHaveBeenCalledWith('torta-fresa', { price: 60 });
            expect(mockCtx.logAction).toHaveBeenCalled();
        });

        it('should fail to change price if product not found', () => {
            const result = actions.execute('cambiar_precio', { product: 'chocolate', price: 60, rawText: '' });
            expect(result.success).toBe(false);
            expect(mockCtx.updateProduct).not.toHaveBeenCalled();
        });

        it('should set out of stock', () => {
            const result = actions.execute('agotar_stock', { product: 'torta-fresa', rawText: '' });
            expect(result.success).toBe(true);
            expect(mockCtx.updateProduct).toHaveBeenCalledWith('torta-fresa', { stock: 'out_of_stock' });
        });

        it('should add a new product via wizard intent', () => {
            const result = actions.execute('agregar_producto_wizard', { product: 'Pionono', price: 20, category: 'piononos', rawText: '' });
            expect(result.success).toBe(true);
            expect(mockCtx.addProduct).toHaveBeenCalledWith(expect.objectContaining({
                id: 'pionono',
                title: 'Pionono',
                price: 20,
                category: 'piononos'
            }));
        });
    });

    describe('Theme', () => {
        it('should toggle dark mode', () => {
            const result = actions.execute('toggle_dark', { rawText: '' });
            expect(result.success).toBe(true);
            expect(mockCtx.setTheme).toHaveBeenCalledWith({ darkMode: true });
        });
    });

    describe('System', () => {
        it('should execute optimize_shop', () => {
            // Should create generic promo
            const result = actions.execute('optimizar_todo', { rawText: '' });
            expect(result.success).toBe(true);
            expect(mockCtx.addCoupon).toHaveBeenCalled();
        });
    });
});
