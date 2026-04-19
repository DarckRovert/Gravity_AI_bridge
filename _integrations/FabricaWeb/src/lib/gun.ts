// Gun.js configuration — P2P database for real-time sync
// Types are incomplete for gun/sea, using require() for dynamic import

interface GunInstance {
    user: () => GunUserInstance;
    get: (node: string) => GunChain;
}

interface GunUserInstance {
    recall: (opts: { sessionStorage: boolean }) => void;
    auth: (user: string, pass: string, cb: (ack: { err?: string }) => void) => void;
    create: (user: string, pass: string, cb: (ack: { err?: string }) => void) => void;
}

interface GunChain {
    get: (key: string) => GunChain;
    put: (value: unknown) => void;
    on: (cb: (data: unknown, key: string) => void) => void;
    once: (cb: (data: unknown) => void) => void;
}

let db: GunInstance | null = null;
let user: GunUserInstance | null = null;

if (typeof window !== 'undefined') {
    try {
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const Gun = require('gun/gun');
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        require('gun/sea');

        db = Gun({
            localStorage: true,
        }) as GunInstance;
        user = db.user();
    } catch {
        // Gun.js not available — P2P features disabled
    }
}

export { db, user };
export default db;
