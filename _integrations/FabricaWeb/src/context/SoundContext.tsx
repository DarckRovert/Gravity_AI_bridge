"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { soundEngine } from '@/lib/soundEngine';

interface SoundContextType {
    muted: boolean;
    toggleMute: () => void;
    playSound: (sound: 'pop' | 'ding' | 'chime' | 'click') => void;
}

const SoundContext = createContext<SoundContextType | null>(null);

export function SoundProvider({ children }: { children: ReactNode }) {
    const [muted, setMuted] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem('pastelito_sound_muted');
        if (saved) {
            const isMuted = saved === 'true';
            setMuted(isMuted);
            soundEngine.setMuted(isMuted);
        }
    }, []);

    const toggleMute = () => {
        const newState = !muted;
        setMuted(newState);
        soundEngine.setMuted(newState);
        localStorage.setItem('pastelito_sound_muted', String(newState));
    };

    const playSound = (sound: 'pop' | 'ding' | 'chime' | 'click') => {
        if (muted) return;
        switch (sound) {
            case 'pop': soundEngine.playPop(); break;
            case 'ding': soundEngine.playDing(); break;
            case 'chime': soundEngine.playChime(); break;
            case 'click': soundEngine.playClick(); break;
        }
    };

    return (
        <SoundContext.Provider value={{ muted, toggleMute, playSound }}>
            {children}
        </SoundContext.Provider>
    );
}

export function useSound() {
    const context = useContext(SoundContext);
    if (!context) throw new Error('useSound must be used within SoundProvider');
    return context;
}
