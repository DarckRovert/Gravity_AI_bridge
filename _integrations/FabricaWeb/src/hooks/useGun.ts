import { useEffect, useState } from 'react';
import db from '@/lib/gun';

export const useGunState = <T>(node: string, key: string, initialValue: T) => {
    const [value, setValue] = useState<T>(initialValue);

    useEffect(() => {
        if (!db) return;

        // Subscribe to changes in real-time
        const ref = db.get(node).get(key);

        ref.on((data: unknown) => {
            if (data !== undefined && data !== null) {
                setValue(data as T);
            }
        });

        return () => {
            // Gun doesn't have a clean unsubscribe, but we can ignore updates
        };
    }, [node, key]);

    const updateValue = (newValue: T) => {
        if (!db) return;
        db.get(node).get(key).put(newValue as unknown);
    };

    return [value, updateValue] as const;
};
