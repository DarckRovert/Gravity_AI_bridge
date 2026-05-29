import { processQuery, NLPResult } from './pastelitoNLP';
import type { Product } from '@/data/products';

export type WorkerMessage = {
    id: string;
    type: 'PROCESS_QUERY' | 'TRACK_MESSAGE';
    payload: any;
};

export type WorkerResponse = {
    id: string;
    type: 'QUERY_RESULT';
    payload: NLPResult;
};

self.onmessage = (event: MessageEvent<WorkerMessage>) => {
    const { type, payload, id } = event.data;

    if (type === 'PROCESS_QUERY') {
        const { query, products, whatsappNumber, isAdmin } = payload;
        try {
            const result = processQuery(query, products, whatsappNumber, isAdmin);
            self.postMessage({ id, type: 'QUERY_RESULT', payload: result } as WorkerResponse);
        } catch (error) {
            self.postMessage({ id, type: 'ERROR', payload: error } as any);
        }
    } else if (type === 'TRACK_MESSAGE') {
        import('./pastelitoNLP').then(({ trackMessage }) => {
            trackMessage(payload.text, payload.role);
        });
    }
};
