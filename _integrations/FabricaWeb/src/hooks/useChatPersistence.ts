import { useState, useEffect } from 'react';
import { Message } from '@/types/chatbot';

const CHAT_STORAGE_KEY = 'dm_chat_history';
const MAX_STORED_MESSAGES = 50;

export function useChatPersistence() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [hasRestoredHistory, setHasRestoredHistory] = useState(false);

    // Restore chat history on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(CHAT_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored) as Message[];
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setMessages(parsed);
                }
            }
        } catch { /* ignore parse errors */ }
        setHasRestoredHistory(true);
    }, []);

    // Persist chat history to localStorage
    useEffect(() => {
        if (messages.length > 0 && hasRestoredHistory) {
            const toStore = messages.slice(-MAX_STORED_MESSAGES);
            try { localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(toStore)); } catch { /* ignore quota */ }
        }
    }, [messages, hasRestoredHistory]);

    const clearHistory = () => {
        setMessages([]);
        localStorage.removeItem(CHAT_STORAGE_KEY);
    };

    return { messages, setMessages, hasRestoredHistory, clearHistory };
}
