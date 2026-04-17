"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import ErrorBoundary from "@/components/ErrorBoundary";

const Chatbot = dynamic(() => import("@/components/Chatbot"), {
    ssr: false,
    loading: () => null,
});

/**
 * Delays chatbot loading by 3 seconds after mount to prioritize
 * above-the-fold content. On mobile, waits for first user interaction instead.
 */
export default function ChatbotLoader() {
    const [shouldLoad, setShouldLoad] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setShouldLoad(true), 3000);

        const onInteraction = () => {
            setShouldLoad(true);
            cleanup();
        };

        const cleanup = () => {
            clearTimeout(timer);
            window.removeEventListener('scroll', onInteraction);
            window.removeEventListener('click', onInteraction);
            window.removeEventListener('touchstart', onInteraction);
        };

        window.addEventListener('scroll', onInteraction, { once: true, passive: true });
        window.addEventListener('click', onInteraction, { once: true });
        window.addEventListener('touchstart', onInteraction, { once: true, passive: true });

        return cleanup;
    }, []);

    if (!shouldLoad) return null;
    return (
        <ErrorBoundary name="Chatbot" fallback={null}>
            <Chatbot />
        </ErrorBoundary>
    );
}
