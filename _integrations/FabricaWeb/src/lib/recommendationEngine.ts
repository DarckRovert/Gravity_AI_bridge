// ⚡ RecommendationEngine — Pastelito AI v2.0
// Recomienda productos de forma inteligente basándose en datos reales

import { Product } from '@/data/products';

interface OrderData {
    items: { id: string; title: string; quantity: number }[];
    date: string;
}

export class RecommendationEngine {
    /**
     * Get a smart recommendation based on popularity, stock, and time of day.
     */
    getSmartRecommendation(products: Product[], orders: OrderData[] = []): Product | null {
        const available = products.filter(p => p.stock !== 'out_of_stock');
        if (available.length === 0) return null;

        // If we have order data, recommend the most popular available product
        if (orders.length > 0) {
            const trending = this.getTrendingProducts(products, orders, 1);
            if (trending.length > 0) return trending[0];
        }

        // Time-based fallback
        const hour = new Date().getHours();
        if (hour < 12) {
            // Morning: recommend lighter items (bocaditos, piononos clásicos)
            const morning = available.filter(p =>
                p.category === 'bocaditos' || p.id.includes('clasico')
            );
            if (morning.length > 0) return morning[Math.floor(Math.random() * morning.length)];
        } else if (hour < 17) {
            // Afternoon: full tortas and combos
            const afternoon = available.filter(p =>
                p.category === 'tortas' || p.category === 'combos'
            );
            if (afternoon.length > 0) return afternoon[Math.floor(Math.random() * afternoon.length)];
        } else {
            // Evening: premium items (featured or combos)
            const evening = available.filter(p => p.featured || p.category === 'combos');
            if (evening.length > 0) return evening[Math.floor(Math.random() * evening.length)];
        }

        // Random fallback
        return available[Math.floor(Math.random() * available.length)];
    }

    /**
     * Get the top N trending products based on recent orders.
     */
    getTrendingProducts(products: Product[], orders: OrderData[], limit = 3): Product[] {
        if (orders.length === 0) {
            // No orders: return featured products
            return products.filter(p => p.featured && p.stock !== 'out_of_stock').slice(0, limit);
        }

        // Count product appearances in orders
        const productCounts: Record<string, number> = {};
        orders.forEach(order => {
            order.items?.forEach(item => {
                productCounts[item.id] = (productCounts[item.id] || 0) + item.quantity;
            });
        });

        // Sort by popularity, filter out unavailable
        return products
            .filter(p => p.stock !== 'out_of_stock')
            .sort((a, b) => (productCounts[b.id] || 0) - (productCounts[a.id] || 0))
            .slice(0, limit);
    }

    /**
     * Get complementary product suggestions based on what the customer is viewing.
     */
    getComplementary(currentProduct: Product, allProducts: Product[]): Product | null {
        const candidates = allProducts.filter(p =>
            p.id !== currentProduct.id &&
            p.stock !== 'out_of_stock'
        );

        if (candidates.length === 0) return null;

        // If viewing a single item, suggest a combo
        if (currentProduct.category !== 'combos') {
            const combos = candidates.filter(p => p.category === 'combos');
            if (combos.length > 0) return combos[Math.floor(Math.random() * combos.length)];
        }

        // If viewing a combo, suggest an add-on (bocaditos)
        if (currentProduct.category === 'combos') {
            const addons = candidates.filter(p => p.category === 'bocaditos');
            if (addons.length > 0) return addons[Math.floor(Math.random() * addons.length)];
        }

        // Same category, different product
        const sameCategory = candidates.filter(p => p.category === currentProduct.category);
        if (sameCategory.length > 0) return sameCategory[Math.floor(Math.random() * sameCategory.length)];

        return candidates[Math.floor(Math.random() * candidates.length)];
    }

    /**
     * Generate a recommendation message with emoji and context.
     */
    formatRecommendation(product: Product, reason: 'trending' | 'time' | 'complementary' = 'trending'): string {
        const reasons: Record<string, string> = {
            trending: '🔥 Lo más pedido',
            time: '⏰ Perfecto para esta hora',
            complementary: '💡 También te gustará'
        };

        return `${reasons[reason]}: **${product.title}** a solo **S/${product.price.toFixed(2)}**. ${product.description.split('.')[0]}. 😋`;
    }
}

export const recommendationEngine = new RecommendationEngine();
