import { Product } from '@/data/products';
import { FAQ_DB } from './knowledgeBase';

/**
 * Convierte el catálogo de productos en un texto legible para la IA.
 * Esto es el corazón del RAG: dar información real al modelo.
 */
export const generateProductContext = (products: Product[]): string => {
    let context = "=== CATÁLOGO DE PRODUCTOS DISPONIBLES ===\n\n";

    products.forEach(p => {
        // Ignorar productos ocultos o sin stock si se desea, 
        // pero mejor incluirlos con etiqueta de estado para que la IA informe.
        const stockStatus = p.stock === 'out_of_stock' ? '[AGOTADO]' : p.stock === 'low' ? '[ÚLTIMAS UNIDADES]' : '[DISPONIBLE]';

        context += `🆔 ID: ${p.id}\n`;
        context += `🍰 Nombre: ${p.title} ${stockStatus}\n`;
        context += `💰 Precio: S/ ${p.price.toFixed(2)}\n`;
        context += `📂 Categoría: ${p.category}\n`;
        context += `📝 Descripción: ${p.description}\n`;
        if (p.featured) context += `⭐ DESTACADO: Sí (Recomendar este producto)\n`;
        context += "---\n";
    });

    return context;
};

/**
 * Genera el contexto de zonas de delivery.
 */
export const generateDeliveryContext = (zones: { name: string; price: string; desc: string }[]): string => {
    let context = "\n=== ZONAS DE DELIVERY ===\n";
    zones.forEach(z => {
        context += `- ${z.name}: ${z.price} (${z.desc})\n`;
    });
    return context;
};

/**
 * Genera contexto sobre cupones activos.
 */
export const generateCouponContext = (coupons: { code: string; type: string; discount: number; active: boolean }[]): string => {
    let context = "\n=== CUPONES ACTIVOS ===\n";
    coupons.filter(c => c.active).forEach(c => {
        const discountVal = c.type === 'percent' ? `${c.discount}%` : `S/ ${c.discount}`;
        context += `- Código: ${c.code} -> Descuento: ${discountVal}\n`;
    });
    return context;
};

/**
 * Genera el contexto de Preguntas Frecuentes.
 */
export const generateFAQContext = (): string => {
    let context = "\n=== PREGUNTAS FRECUENTES (FAQ) ===\n";
    FAQ_DB.forEach(item => {
        context += `P: ${item.question}\nR: ${item.answer}\n---\n`;
    });
    return context;
};
