
import { ContentConfig } from '@/context/SiteConfigContext';

/**
 * Generates a WhatsApp Deep Link with a pre-filled message based on context.
 * Uses the phone number from SiteConfig or falls back to the default.
 */
export const generateWhatsAppLink = (
    phone: string | undefined,
    intent: 'support' | 'order' | 'product' | 'general',
    data?: {
        customerName?: string;
        orderId?: string;
        productName?: string;
        total?: string;
        details?: string;
    }
): string => {
    // Default fallback number if config is missing
    const targetPhone = phone?.replace(/\D/g, '') || '51965968723';

    let message = '';

    switch (intent) {
        case 'support':
            message = `Hola Antojín 🍍, soy ${data?.customerName || 'un cliente'}. Necesito ayuda con: ${data?.details || 'una consulta'}.`;
            break;

        case 'order':
            message = `Hola! 🛒 Quiero confirmar mi pedido #${data?.orderId || 'PENDIENTE'}.\n\nTotal: ${data?.total || 'S/0.00'}\n\nPor favor envíenme los datos de pago.`;
            break;

        case 'product':
            message = `Hola! 🍰 Vi el producto *${data?.productName}* en la web y me interesa saber más detalles o disponibilidad.`;
            break;

        case 'general':
        default:
            message = `Hola Antojín! 🍍 Tengo una consulta general para el Admin.`;
            break;
    }

    const encodedMessage = encodeURIComponent(message);
    return `https://wa.me/${targetPhone}?text=${encodedMessage}`;
};
