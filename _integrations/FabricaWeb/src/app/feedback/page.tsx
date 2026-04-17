"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/context/ToastContext';
import { useContent } from '@/context/SiteConfigContext';
import { sanitizeInput } from '@/lib/security';
import confetti from 'canvas-confetti';

export default function FeedbackPage() {
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState('');
    const [product, setProduct] = useState('');
    const [delivery, setDelivery] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const router = useRouter();
    const { showToast } = useToast();
    const { content } = useContent();

    const handleSend = () => {
        if (rating === 0) {
            showToast('Por favor selecciona una calificación ⭐', 'info');
            return;
        }

        const sanitizedComment = sanitizeInput(comment);

        // Build WhatsApp message (legacy logic)
        const stars = '⭐'.repeat(rating);
        const message = `📊 *FEEDBACK DE CLIENTE*%0A` +
            `━━━━━━━━━━━━━━━━━━%0A` +
            `${stars} (${rating}/5)%0A` +
            (product ? `🍰 *Producto:* ${product}%0A` : '') +
            (delivery ? `🛵 *Entrega:* ${delivery}%0A` : '') +
            (sanitizedComment ? `💬 *Comentario:* ${sanitizedComment}%0A` : '') +
            `━━━━━━━━━━━━━━━━━━%0A` +
            `Enviado desde Antojitos Express`;

        // Save to local storage
        const feedbacks = JSON.parse(localStorage.getItem('dm_feedbacks') || '[]');
        feedbacks.push({
            date: new Date().toISOString(),
            rating, product, delivery, comment: sanitizedComment
        });
        localStorage.setItem('dm_feedbacks', JSON.stringify(feedbacks));

        // Trigger Confetti
        const duration = 3000;
        const animationEnd = Date.now() + duration;
        const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

        const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

        const interval: NodeJS.Timeout = setInterval(function () {
            const timeLeft = animationEnd - Date.now();

            if (timeLeft <= 0) {
                return clearInterval(interval);
            }

            const particleCount = 50 * (timeLeft / duration);
            confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
            confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
        }, 250);

        // Open WhatsApp
        window.open(`https://wa.me/${content.whatsappNumber || '51965968723'}?text=${message}`, '_blank');
        setSubmitted(true);
        showToast('¡Gracias por tu feedback! 🎉', 'success');
    };

    if (submitted) {
        return (
            <main className="min-h-screen bg-paper flex items-center justify-center p-4 animate-fade-in">
                <div className="bg-white p-12 rounded-3xl shadow-xl max-w-lg w-full text-center space-y-6 animate-scale-in">
                    <div className="text-7xl mb-4 animate-bounce">🥰</div>
                    <h1 className="text-3xl font-playfair font-bold text-primary">¡Gracias por tu opinión!</h1>
                    <p className="text-lg text-primary/80">
                        Tu feedback nos ayuda a seguir mejorando para endulzar tus momentos.
                        ¡Nos vemos en tu próximo antojo!
                    </p>
                    <button
                        onClick={() => router.push('/')}
                        className="bg-accent text-white px-8 py-3 rounded-full font-bold hover:scale-105 transition-transform"
                    >
                        Volver al Inicio
                    </button>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-paper flex items-center justify-center py-12 px-4 font-poppins text-primary animate-fade-in">
            <div className="bg-white rounded-3xl p-8 md:p-12 max-w-xl w-full shadow-2xl space-y-8 animate-fade-up">
                <div className="text-center">
                    <h1 className="text-4xl font-playfair font-bold text-accent mb-2">🎂 ¿Cómo te fue?</h1>
                    <p className="text-gray-500">Tu opinión nos ayuda a mejorar. ¡Cuéntanos tu experiencia!</p>
                </div>

                {/* Star Rating */}
                <div className="flex justify-center gap-4 text-5xl">
                    {[1, 2, 3, 4, 5].map(star => (
                        <button
                            key={star}
                            onClick={() => setRating(star)}
                            className={`transition-all duration-300 transform hover:scale-125 hover:rotate-6 
                                ${rating >= star ? 'grayscale-0 drop-shadow-[0_0_10px_rgba(250,204,21,0.6)]' : 'grayscale opacity-50 hover:grayscale-0'}`}
                        >
                            ⭐
                        </button>
                    ))}
                </div>

                {/* Questions */}
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-bold mb-2">¿Qué pediste?</label>
                        <select
                            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-secondary transition-all"
                            onChange={(e) => setProduct(e.target.value)}
                        >
                            <option value="">Selecciona...</option>
                            <option value="Pionono">Pionono</option>
                            <option value="Torta">Torta</option>
                            <option value="Alfajores">Alfajores</option>
                            <option value="Combo">Combo</option>
                            <option value="Personalizada">Torta Personalizada</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-bold mb-2">¿Llegó a tiempo?</label>
                        <select
                            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-secondary transition-all"
                            onChange={(e) => setDelivery(e.target.value)}
                        >
                            <option value="">Selecciona...</option>
                            <option value="Sí, puntual">Sí, puntual ✅</option>
                            <option value="Llegó un poco tarde">Llegó un poco tarde ⏰</option>
                            <option value="Se demoró mucho">Se demoró mucho ❌</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-bold mb-2">Comentarios / Sugerencias</label>
                        <textarea
                            rows={4}
                            value={comment}
                            onChange={(e) => setComment(e.target.value)}
                            placeholder="Escribe aquí tu mensaje..."
                            className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-secondary transition-all"
                        />
                    </div>
                </div>

                <button
                    onClick={handleSend}
                    className="w-full bg-accent text-white py-4 rounded-xl font-bold text-lg hover:bg-accent/80 transition-all hover:scale-[1.02] shadow-lg shadow-red-200 active:scale-95"
                >
                    Enviar mi Opinión 💬
                </button>
            </div>
        </main>
    );
}
