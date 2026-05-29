// 🧠 Fallback Chain — Orquesta las capas de inteligencia
// Usa Web Workers para procesar la NLP sin bloquear el UI.

import { Product } from '@/data/products';
import { NLPResult } from './pastelitoNLP';

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

// --- Web Worker Singleton ---
let nlpWorker: Worker | null = null;
let currentMessageId = 0;
const pendingRequests = new Map<string, (result: NLPResult) => void>();

function getWorker(): Worker {
    if (!nlpWorker && typeof window !== 'undefined') {
        // En Next.js, instanciar un Worker require esta sintaxis exacta para Turbopack/Webpack
        nlpWorker = new Worker(new URL('./nlp.worker.ts', import.meta.url));
        nlpWorker.onmessage = (event) => {
            const { id, type, payload } = event.data;
            if (type === 'QUERY_RESULT' && pendingRequests.has(id)) {
                pendingRequests.get(id)!(payload);
                pendingRequests.delete(id);
            }
        };
    }
    return nlpWorker as Worker;
}

export async function processCustomerQuery(
    query: string,
    ctx: FallbackContext
): Promise<FallbackResult> {
    console.log(`🔗 FallbackChain: Processing query "${query}"`);

    if (typeof window === 'undefined') {
        return { response: '', source: 'fallback', streaming: false };
    }

    const worker = getWorker();
    const id = `msg_${currentMessageId++}`;

    const nlpResult = await new Promise<NLPResult>((resolve) => {
        pendingRequests.set(id, resolve);
        worker.postMessage({
            id,
            type: 'PROCESS_QUERY',
            payload: {
                query,
                products: ctx.products,
                whatsappNumber: ctx.whatsappNumber,
                isAdmin: ctx.isAdmin
            }
        });
    });

    console.log(`🔗 FallbackChain: Result from Worker [source: ${nlpResult.source}]`);

    if (nlpResult.response) {
        worker.postMessage({
            id: `trk_${currentMessageId++}`,
            type: 'TRACK_MESSAGE',
            payload: { text: nlpResult.response, role: 'bot' }
        });
    }

    return {
        response: nlpResult.response,
        action: nlpResult.action,
        source: mapSource(nlpResult.source),
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
