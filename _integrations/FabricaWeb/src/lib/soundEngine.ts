export class SoundEngine {
    private ctx: AudioContext | null = null;
    private muted: boolean = false;

    constructor() {
        if (typeof window !== 'undefined') {
            const AudioContextClass = window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
            if (AudioContextClass) {
                this.ctx = new AudioContextClass();
            }
        }
    }

    setMuted(muted: boolean) {
        this.muted = muted;
    }

    private createOscillator(type: OscillatorType, freq: number, duration: number, volume: number = 0.1) {
        if (!this.ctx || this.muted) return;

        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

        gain.gain.setValueAtTime(volume, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start();
        osc.stop(this.ctx.currentTime + duration);
    }

    playPop() {
        // High pitched short pop
        this.createOscillator('sine', 800, 0.1, 0.1);
    }

    playDing() {
        // Bell-like ding
        this.createOscillator('sine', 1200, 0.3, 0.1);
        setTimeout(() => this.createOscillator('triangle', 1800, 0.3, 0.05), 50);
    }

    playChime() {
        // Success melody
        const now = this.ctx?.currentTime || 0;
        const notes = [523.25, 659.25, 783.99, 1046.50]; // C E G C
        notes.forEach((note, i) => {
            setTimeout(() => this.createOscillator('sine', note, 0.4, 0.1), i * 100);
        });
    }

    playClick() {
        this.createOscillator('square', 200, 0.05, 0.05);
    }
}

export const soundEngine = new SoundEngine();
