/**
 * 💳 API Route: /api/culqi-charge
 *
 * Server-side Culqi charge creation.
 * Uses the SECRET key (never exposed to the browser).
 *
 * ⚠️  SETUP: Add CULQI_SECRET_KEY to your .env.local
 *     (this is the Secret Key from the Culqi Dashboard → API Keys)
 */

import { NextRequest, NextResponse } from 'next/server';

const CULQI_CHARGES_URL = 'https://api.culqi.com/v2/charges';

export async function POST(req: NextRequest) {
    const secretKey = process.env.CULQI_SECRET_KEY;

    if (!secretKey) {
        return NextResponse.json(
            { success: false, message: 'CULQI_SECRET_KEY no configurada en .env.local' },
            { status: 503 }
        );
    }

    let body: { tokenId: string; amount: number; email: string; orderId: string; description?: string };
    try {
        body = await req.json();
    } catch {
        return NextResponse.json({ success: false, message: 'JSON inválido.' }, { status: 400 });
    }

    const { tokenId, amount, email, orderId, description } = body;

    if (!tokenId || !amount || !email || !orderId) {
        return NextResponse.json(
            { success: false, message: 'Faltan campos requeridos: tokenId, amount, email, orderId.' },
            { status: 400 }
        );
    }

    try {
        const culqiRes = await fetch(CULQI_CHARGES_URL, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${secretKey}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount,
                currency_code: 'PEN',
                email,
                source_id: tokenId,
                description: description ?? `Pedido ${orderId} - Dulces Momentos`,
                metadata: { orderId },
            }),
        });

        const data = await culqiRes.json();

        if (!culqiRes.ok || data.object === 'error') {
            console.error('[Culqi API] Charge failed:', data);
            return NextResponse.json(
                { success: false, message: data.user_message ?? 'Error al procesar el pago.' },
                { status: 400 }
            );
        }

        // data.id is the Culqi charge ID (chr_xxx)
        return NextResponse.json({ success: true, id: data.id, amount: data.amount });
    } catch (err) {
        console.error('[Culqi API] Network error:', err);
        return NextResponse.json(
            { success: false, message: 'Error de conexión con Culqi.' },
            { status: 502 }
        );
    }
}
