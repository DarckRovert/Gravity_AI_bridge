// 🧠 Fallback Chain — Orquesta las capas de inteligencia de Pastelito
// 100% autónomo — zero dependencias externas (sin CDN, sin TensorFlow, sin HuggingFace)
// Usa PastelitoNLP como motor unificado.

import { Product } from '@/data/products';
import { processQuery, trackMessage, NLPResult } from './pastelitoNLP';

export interface FallbackContext {
    products: Product[];
    deliveryZones: Array<{ name: string; price: string; desc?: string }>;
    coupons: Array<{ code: string; type: string; discount: number; active: boolean }>;
    isAdmin: boolean;
    currentPage: string;
    businessHours: string;
    whatsappNumber: string;
    conversationHistory: Array<{ role: 'user' | 'bot'; text: string }>;
}

export interface FallbackResult {
    response: string;
    action?: string;
    source: 'kb-match' | 'nlp' | 'fallback';
    streaming: boolean;
}

// Map NLP sources to FallbackResult sources
function mapSource(nlpSource: NLPResult['source']): FallbackResult['source'] {
    switch (nlpSource) {
        case 'kb': return 'kb-match';
        case 'intent':
        case 'product':
        case 'faq':
        case 'context':
            return 'nlp';
        case 'fallback':
        default:
            return 'fallback';
    }
}

// ========================
// 🧠 MAIN CHAIN
// ========================

/**
 * Process a customer query through PastelitoNLP.
 * Everything is handled by the unified NLP engine — no external dependencies.
 */
export async function processCustomerQuery(
    query: string,
    ctx: FallbackContext
): Promise<FallbackResult> {

    console.log(`🔗 FallbackChain: Processing query "${query}"`);

    const result = processQuery(query, ctx.products, ctx.whatsappNumber, ctx.isAdmin);

    console.log(`🔗 FallbackChain: Result from PastelitoNLP [source: ${result.source}]${result.action ? ` [action: ${result.action}]` : ''} "${result.response.substring(0, 60)}..."`);

    // Track bot response for context
    if (result.response) {
        trackMessage(result.response, 'bot');
    }

    return {
        response: result.response,
        action: result.action,
        source: mapSource(result.source),
        streaming: false,
    };
}

/**
 * Streaming simulation — yields text chunks for a typing effect.
 * The 'action' field is included on the FINAL yield so the consumer can execute it.
 */
export async function* processCustomerQueryStreaming(
    query: string,
    ctx: FallbackContext
): AsyncGenerator<{ chunk: string; done: boolean; source: string; action?: string }> {

    const result = await processCustomerQuery(query, ctx);

    // If it returned an action with no text, yield immediately with the action
    if (result.action && !result.response) {
        yield { chunk: '', done: true, source: result.source, action: result.action };
        return;
    }

    // Simulate typing effect — split response into chunks
    const words = result.response.split(' ');
    const chunkSize = 3; // words per chunk

    for (let i = 0; i < words.length; i += chunkSize) {
        const chunk = words.slice(i, i + chunkSize).join(' ');
        const isLast = (i + chunkSize) >= words.length;
        yield {
            chunk: (i === 0 ? '' : ' ') + chunk,
            done: isLast,
            source: result.source,
            // Include action ONLY on the last chunk
            ...(isLast && result.action ? { action: result.action } : {}),
        };

        // Small delay for typing effect
        if (!isLast) {
            await new Promise(r => setTimeout(r, 30));
        }
    }
}
