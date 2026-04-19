import { describe, it, expect, beforeEach } from 'vitest';
import { pastelitoEngine } from '../pastelitoEngine';

describe('PastelitoEngine', () => {
    beforeEach(() => {
        // Clear memory before each test
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (pastelitoEngine as any).memory = {
            lastIntent: null,
            pendingAction: null,
            context: {},
            lastProduct: null,
            lastCategory: null,
            lastAction: null,
            conversationHistory: [],
        };
    });

    it('should normalize text correctly', () => {
        const text = ' ¿QUÉ Tál?  MÁS   Allá ';
        expect(pastelitoEngine.normalize(text)).toBe('¿que tal? mas alla');
    });

    describe('Admin Intents', () => {
        it('should detect cambiar_precio and extract price and product', () => {
            const result = pastelitoEngine.parse('cambia precio de la torta de chocolate a s/ 50.50', true);
            expect(result.intent).toBe('cambiar_precio');
            expect(result.entities.price).toBe(50.5);
            expect(result.entities.product).toContain('torta  chocolate');
            expect(result.requiresConfirmation).toBe(true);
            expect(result.riskLevel).toBe('medium');
        });

        it('should detect agotar_stock', () => {
            const result = pastelitoEngine.parse('agota el pionono', true);
            expect(result.intent).toBe('agotar_stock');
            expect(result.entities.product).toContain('pionono');
        });

        it('should extract coupon and percentage discount', () => {
            const result = pastelitoEngine.parse('crear cupón VERANO24 de 20%', true);
            expect(result.intent).toBe('crear_cupon');
            expect(result.entities.couponCode).toBe('VERANO24');
            expect(result.entities.discount).toBe(20);
            expect(result.entities.discountType).toBe('percent');
        });

        it('should fallback to customer intents if isAdmin is false', () => {
            const result = pastelitoEngine.parse('cambia el precio de la torta a s/ 50', false);
            expect(result.intent).toBe('preguntar_precio'); // Since 'precio' is in the text
        });
    });

    describe('Customer Intents', () => {
        it('should detect saludar', () => {
            const result = pastelitoEngine.parse('hola pastelito', false);
            expect(result.intent).toBe('saludar');
        });

        it('should detect preguntar_precio and extract product', () => {
            const result = pastelitoEngine.parse('cuanto cuesta la torta selva negra', false);
            expect(result.intent).toBe('preguntar_precio');
            expect(result.entities.product).toContain('selva negra');
        });

        it('should detect preguntar_delivery', () => {
            const result = pastelitoEngine.parse('hacen envíos a surco?', false);
            expect(result.intent).toBe('preguntar_delivery');
        });
    });

    describe('Memory and Context', () => {
        it('should remember the last product for pronoun resolution', () => {
            // Mention a product
            pastelitoEngine.parse('cual es el precio del pastel de fresa', false);
            expect(pastelitoEngine.getLastProduct()).toContain('fresa');

            // Refer to it without naming it
            const result = pastelitoEngine.parse('cambiar precio a s/ 40', true);
            expect(result.intent).toBe('cambiar_precio');
            expect(result.entities.price).toBe(40);
            expect(result.entities.product).toContain('fresa');
        });
    });
});
