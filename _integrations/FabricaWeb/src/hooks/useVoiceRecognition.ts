"use client";

import { useState, useEffect, useCallback } from 'react';

// Web Speech API types (not in standard lib)
interface SpeechRecognitionEvent {
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent {
    error: string;
}

interface SpeechRecognitionInstance {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    onstart: (() => void) | null;
    onend: (() => void) | null;
    onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    start: () => void;
    stop: () => void;
}

interface VoiceResult {
    text: string;
    isListening: boolean;
    startListening: () => void;
    stopListening: () => void;
    hasSupport: boolean;
}

export function useVoiceRecognition(): VoiceResult {
    const [text, setText] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [hasSupport, setHasSupport] = useState(false);
    const [recognition, setRecognition] = useState<SpeechRecognitionInstance | null>(null);

    useEffect(() => {
        if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
            setHasSupport(true);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const rec = new (window as Window & { webkitSpeechRecognition: new () => SpeechRecognitionInstance }).webkitSpeechRecognition();
            rec.continuous = false;
            rec.interimResults = false;
            rec.lang = 'es-PE'; // Peruvian Spanish

            rec.onstart = () => setIsListening(true);
            rec.onend = () => setIsListening(false);
            rec.onerror = (event: SpeechRecognitionErrorEvent) => {
                console.error('Voice recognition error', event.error);
                setIsListening(false);
            };

            rec.onresult = (event: SpeechRecognitionEvent) => {
                const transcript = event.results[0][0].transcript;
                setText(transcript);
            };

            setRecognition(rec);
        }
    }, []);

    const startListening = useCallback(() => {
        if (recognition) {
            setText('');
            recognition.start();
        }
    }, [recognition]);

    const stopListening = useCallback(() => {
        if (recognition) {
            recognition.stop();
        }
    }, [recognition]);

    return { text, isListening, startListening, stopListening, hasSupport };
}
