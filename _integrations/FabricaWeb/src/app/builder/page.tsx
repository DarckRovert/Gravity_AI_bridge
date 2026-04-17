"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CakePreview } from '@/components/CakePreview';

import { CakeSelections, BuilderOptions, CakeOption } from '@/types/cake';
import { sanitizeInput } from '@/lib/security';

const STEPS = [
    { id: 'base', title: 'Elige la Base', icon: '🍰' },
    { id: 'relleno', title: 'Elige el Relleno', icon: '🍯' },
    { id: 'cobertura', title: 'La Cobertura', icon: '🎨' },
    { id: 'tamano', title: '¿Para cuántos?', icon: '🎂' },
    { id: 'resumen', title: 'Resumen', icon: '📋' }
];

const OPTIONS: BuilderOptions = {
    base: [
        { label: 'Vainilla', price: 0, icon: '🍦', desc: 'Clásico y esponjoso' },
        { label: 'Chocolate', price: 5, icon: '🍫', desc: 'Húmedo e intenso (+S/5)' },
        { label: 'Marmoleado', price: 3, icon: '🌀', desc: 'Lo mejor de ambos mundos (+S/3)' },
        { label: 'Red Velvet', price: 8, icon: '🧣', desc: 'Elegancia y suave (+S/8)' },
        { label: 'Zanahoria', price: 8, icon: '🥕', desc: 'Con nueces (+S/8)' },
    ],
    relleno: [
        { label: 'Manjar Blanco', price: 0, icon: '🍶', desc: 'Dulce tradicional' },
        { label: 'Fudge de la Casa', price: 5, icon: '🍫', desc: 'Chocolate cremoso (+S/5)' },
        { label: 'Crema Pastelera', price: 3, icon: '🍮', desc: 'Suave y ligera (+S/3)' },
        { label: 'Queso Crema', price: 8, icon: '🧀', desc: 'Toque ácido (+S/8)' },
    ],
    cobertura: [
        { label: 'Chantilly', price: 0, icon: '☁️', desc: 'Fresca y ligera' },
        { label: 'Buttercream', price: 10, icon: '🧈', desc: 'Cremosa y dulce (+S/10)' },
        { label: 'Fudge', price: 8, icon: '🍫', desc: 'Bañada en chocolate (+S/8)' },
        { label: 'Fondant', price: 25, icon: '🎨', desc: 'Diseño personalizado (+S/25)' },
    ],
    tamano: [
        { label: 'Pequeña (10 porc.)', price: 40, icon: '🎂', desc: 'Base S/40' },
        { label: 'Mediana (18 porc.)', price: 60, icon: '🎂', desc: 'Base S/60' },
        { label: 'Grande (25 porc.)', price: 90, icon: '🎂', desc: 'Base S/90' },
        { label: 'Castillo (40 porc.)', price: 140, icon: '🏰', desc: 'Base S/140' },
    ]
};

export default function BuilderPage() {
    const [step, setStep] = useState(0);
    const [selections, setSelections] = useState<CakeSelections>({
        base: '', relleno: '', cobertura: '', tamano: ''
    });
    const [submitted, setSubmitted] = useState(false);
    const [name, setName] = useState('');
    const [note, setNote] = useState('');
    const [slideDir, setSlideDir] = useState<'left' | 'right'>('left');
    const router = useRouter();

    const calculateTotal = () => {
        let total = 0;
        if (selections.base) total += OPTIONS.base.find(o => o.label === selections.base)?.price || 0;
        if (selections.relleno) total += OPTIONS.relleno.find(o => o.label === selections.relleno)?.price || 0;
        if (selections.cobertura) total += OPTIONS.cobertura.find(o => o.label === selections.cobertura)?.price || 0;
        if (selections.tamano) total += OPTIONS.tamano.find(o => o.label === selections.tamano)?.price || 0;
        return total;
    };

    const currentStepId = STEPS[step].id as keyof typeof OPTIONS;

    const handleSelect = (val: string) => {
        setSelections({ ...selections, [currentStepId]: val });
    };

    const nextStep = () => {
        setSlideDir('left');
        setStep(prev => prev + 1);
    };

    const prevStep = () => {
        setSlideDir('right');
        setStep(prev => prev - 1);
    };

    const handleOrder = () => {
        const total = calculateTotal();
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const rand = Math.random().toString(36).substr(2, 4).toUpperCase();
        const orderNum = `DM-CUSTOM-${yyyy}${mm}${dd}-${rand}`;

        const sanitizedName = sanitizeInput(name);
        const sanitizedNote = sanitizeInput(note);

        const message =
            `🎨 *NUEVA TORTA PERSONALIZADA* 🎂%0A` +
            `🧾 *RECETA ${orderNum}*%0A` +
            `━━━━━━━━━━━━━━━━━━%0A` +
            `👤 *Cliente:* ${sanitizedName || 'Explorador Dulce'}%0A` +
            `🎂 *Base:* ${selections.base}%0A` +
            `🍯 *Relleno:* ${selections.relleno}%0A` +
            `🎨 *Cobertura:* ${selections.cobertura}%0A` +
            `📏 *Tamaño:* ${selections.tamano}%0A` +
            `━━━━━━━━━━━━━━━━━━%0A` +
            (sanitizedNote ? `📝 *Detalles:* ${sanitizedNote.replace(/\n/g, '%0A')}%0A` : '') +
            `━━━━━━━━━━━━━━━━━━%0A` +
            `💰 *PRECIO ESTIMADO:* S/ ${total.toFixed(2)}%0A` +
            `━━━━━━━━━━━━━━━━━━%0A` +
            `Diseñado en el Constructor de Dulces Momentos 🍰✨`;

        window.open(`https://wa.me/51965968723?text=${message}`, '_blank');
        setSubmitted(true);
    };

    if (submitted) {
        return (
            <main className="min-h-screen bg-paper flex items-center justify-center p-4 animate-fade-in">
                <div className="bg-white p-12 rounded-[3rem] shadow-2xl max-w-lg w-full text-center space-y-6 animate-scale-in">
                    <div className="text-7xl mb-4 animate-bounce">🎂✨</div>
                    <h1 className="text-3xl font-playfair font-bold text-primary">¡Solicitud Enviada!</h1>
                    <p className="text-lg text-primary/80">
                        Hemos abierto WhatsApp con los detalles de tu diseño.
                        Coordinaremos los toques finales y la entrega por ahí.
                    </p>
                    <button
                        onClick={() => router.push('/')}
                        className="bg-secondary text-white px-8 py-3 rounded-full font-bold hover:scale-105 transition-transform shadow-lg shadow-secondary/20"
                    >
                        Volver al Inicio
                    </button>
                    <div className="pt-4">
                        <p className="text-xs text-gray-400 italic">No olvides adjuntar el mensaje en WhatsApp si no se envió automáticamente.</p>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-paper py-12 px-4 font-poppins">
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-10 animate-fade-in">
                    <h1 className="text-4xl font-playfair font-bold text-primary mb-2">Diseña tu Torta Ideal 🎂</h1>
                    <p className="text-gray-500">Crea una obra maestra en 5 simples pasos.</p>
                </div>

                {/* Progress Bar */}
                <div className="mb-8 px-4">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-secondary transition-all duration-500 ease-out rounded-full"
                            style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                        ></div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                    {/* Visual Preview (Sticky on desktop) */}
                    <div className="lg:col-span-1 bg-white p-6 rounded-3xl shadow-xl flex flex-col items-center justify-center min-h-[300px] sticky top-8 animate-scale-in">
                        <h3 className="text-lg font-playfair font-bold text-primary mb-4 text-center">Tu Creación</h3>
                        <CakePreview selections={selections} />
                        <div className="mt-6 text-center w-full">
                            <p className="text-xs text-gray-400 uppercase tracking-widest">Total Estimado</p>
                            <p className="text-3xl font-bold text-secondary">S/ {calculateTotal().toFixed(2)}</p>
                        </div>
                    </div>

                    {/* Steps Content */}
                    <div className="lg:col-span-2 bg-white rounded-3xl p-8 shadow-2xl min-h-[400px] flex flex-col border border-primary/5 animate-fade-up">
                        {/* Internal Stepper Header */}
                        <div className="flex justify-between mb-8 overflow-x-auto pb-4 px-2 border-b border-gray-100">
                            {/* Simplified stepper ticks */}
                            {STEPS.map((s, idx) => (
                                <div key={s.id} className={`flex flex-col items-center min-w-[60px] cursor-default opacity-100`}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs transition-all ${idx <= step ? 'bg-secondary text-white' : 'bg-gray-100 text-gray-400'}`}>
                                        {idx + 1}
                                    </div>
                                    <span className={`text-[8px] mt-1 font-bold uppercase ${idx === step ? 'text-secondary' : 'text-gray-300'}`}>
                                        {s.id}
                                    </span>
                                </div>
                            ))}
                        </div>

                        <div key={step} className={`flex-1 ${slideDir === 'left' ? 'animate-slide-left' : 'animate-fade-in'}`}>
                            {step < 4 ? (
                                <div>
                                    <h2 className="text-2xl font-playfair font-bold text-primary mb-6 flex items-center gap-2">
                                        <span>{STEPS[step].icon}</span> {STEPS[step].title}
                                    </h2>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        {OPTIONS[currentStepId].map((opt: CakeOption) => (
                                            <button
                                                key={opt.label}
                                                onClick={() => handleSelect(opt.label)}
                                                className={`p-4 rounded-2xl border-2 text-left transition-all hover:scale-105 active:scale-95 flex items-start gap-4 ${selections[currentStepId] === opt.label
                                                    ? 'border-secondary bg-secondary/5 ring-2 ring-secondary/20'
                                                    : 'border-gray-50 bg-gray-50 hover:border-accent hover:bg-white'
                                                    }`}
                                            >
                                                <div className="text-3xl bg-white p-2 rounded-xl shadow-sm">{opt.icon}</div>
                                                <div>
                                                    <p className="font-bold text-primary">{opt.label}</p>
                                                    <p className="text-xs text-gray-400 mt-1">{opt.desc || ''}</p>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-6">
                                    <h2 className="text-3xl font-playfair font-bold text-primary mb-8">¡Tu creación está lista! ✨</h2>
                                    <div className="bg-paper p-8 rounded-3xl border-2 border-dashed border-accent/30 space-y-4 shadow-inner text-left">
                                        <div className="flex justify-between border-b border-accent/10 pb-2"><span>Base:</span> <strong>{selections.base || '-'}</strong></div>
                                        <div className="flex justify-between border-b border-accent/10 pb-2"><span>Relleno:</span> <strong>{selections.relleno || '-'}</strong></div>
                                        <div className="flex justify-between border-b border-accent/10 pb-2"><span>Cobertura:</span> <strong>{selections.cobertura || '-'}</strong></div>
                                        <div className="flex justify-between border-b border-accent/10 pb-2"><span>Tamaño:</span> <strong>{selections.tamano || '-'}</strong></div>
                                    </div>
                                    <div className="mt-8 space-y-4">
                                        <input
                                            placeholder="Tu Nombre"
                                            className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-secondary transition-all"
                                            onChange={e => setName(e.target.value)}
                                        />
                                        <textarea
                                            placeholder="Dedicatoria o detalles extra..."
                                            className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-secondary transition-all"
                                            rows={2}
                                            onChange={e => setNote(e.target.value)}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="mt-8 pt-6 border-t border-gray-100 flex justify-between items-center">
                            <button
                                disabled={step === 0}
                                onClick={prevStep}
                                className="px-6 py-2 rounded-full font-bold text-gray-400 hover:text-primary disabled:opacity-0 transition-all hover:-translate-x-1"
                            >
                                ← Atrás
                            </button>
                            {step < 4 ? (
                                <button
                                    disabled={!selections[currentStepId]}
                                    onClick={nextStep}
                                    className="bg-primary text-white px-8 py-3 rounded-full font-bold shadow-lg shadow-gray-200 hover:bg-secondary hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 transition-all flex items-center gap-2"
                                >
                                    Siguiente →
                                </button>
                            ) : (
                                <button
                                    onClick={handleOrder}
                                    className="bg-accent text-white px-10 py-3 rounded-full font-bold shadow-lg shadow-red-200 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                                >
                                    Solicitar por WhatsApp 💬
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
