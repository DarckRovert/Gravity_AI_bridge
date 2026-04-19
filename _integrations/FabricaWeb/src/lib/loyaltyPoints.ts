/**
 * 🍬 Loyalty Points — Dulces Momentos
 *
 * Simple points system: S/1 = 1 point.
 * Points are stored locally (tied to phone number hash in a future version).
 *
 * Usage:
 *   - Call earnPoints(total) after a successful order
 *   - Call getPoints() to read current balance
 *   - Call redeemPoints(points) to spend them (returns discount amount in S/)
 *   - REDEEM_RATE: every 100 points = S/ 10 off
 */

const POINTS_KEY = 'pastelito_points';
const POINTS_PER_SOL = 1;   // 1 point per S/
const REDEEM_RATE = 10;     // every 100 points = S/ 10 off
const MIN_REDEEM = 100;     // minimum points to redeem

export const POINTS_CONFIG = {
    POINTS_PER_SOL,
    REDEEM_RATE,
    MIN_REDEEM,
    /** How much S/ discount per MIN_REDEEM points */
    discountLabel: `${MIN_REDEEM} pts = S/ ${REDEEM_RATE} de descuento`,
};

// ── Core helpers ────────────────────────────────────────────────────────────

export function getPoints(): number {
    try {
        const raw = localStorage.getItem(POINTS_KEY);
        return raw ? parseInt(raw, 10) : 0;
    } catch {
        return 0;
    }
}

function setPoints(pts: number): void {
    try {
        localStorage.setItem(POINTS_KEY, String(Math.max(0, pts)));
    } catch {
        //
    }
}

/**
 * Award points for an order.
 * @param orderTotal  Total in S/ (e.g. 45.50 → 45 points)
 * @returns new total points
 */
export function earnPoints(orderTotal: number): number {
    const earned = Math.floor(orderTotal * POINTS_PER_SOL);
    const newTotal = getPoints() + earned;
    setPoints(newTotal);
    return newTotal;
}

/**
 * Redeem points for a discount.
 * @param pointsToRedeem  Must be a multiple of MIN_REDEEM
 * @returns { discount, newBalance } or null if insufficient
 */
export function redeemPoints(pointsToRedeem: number): { discount: number; newBalance: number } | null {
    const current = getPoints();
    if (pointsToRedeem < MIN_REDEEM || current < pointsToRedeem) return null;

    const discount = (pointsToRedeem / MIN_REDEEM) * REDEEM_RATE;
    const newBalance = current - pointsToRedeem;
    setPoints(newBalance);
    return { discount, newBalance };
}

/**
 * How much discount (in S/) can the user get with their current points?
 */
export function getRedeemableDiscount(): { points: number; discount: number } {
    const pts = getPoints();
    const redeemable = Math.floor(pts / MIN_REDEEM) * MIN_REDEEM;
    return {
        points: redeemable,
        discount: (redeemable / MIN_REDEEM) * REDEEM_RATE,
    };
}
