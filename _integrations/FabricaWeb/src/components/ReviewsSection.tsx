"use client";

import { useState, useEffect } from 'react';
import { Review, getReviews, submitReview, getAverageRating } from '@/lib/firebaseReviews';

const StarRating = ({ value, onChange }: { value: number; onChange?: (v: number) => void }) => (
    <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map(star => (
            <button
                key={star}
                type="button"
                onClick={() => onChange?.(star)}
                className={`text-2xl transition-transform ${onChange ? 'hover:scale-125 cursor-pointer' : 'cursor-default'} ${star <= value ? 'text-secondary' : 'text-gray-200'}`}
                aria-label={`${star} estrellas`}
            >
                ★
            </button>
        ))}
    </div>
);

export default function ReviewsSection() {
    const [reviews, setReviews] = useState<Review[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');

    const [form, setForm] = useState({
        customerName: '',
        rating: 5,
        comment: '',
        orderId: '',
        product: '',
    });

    useEffect(() => {
        getReviews(20).then(data => {
            setReviews(data);
            setLoading(false);
        });
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSubmitting(true);
        const result = await submitReview(form);
        setSubmitting(false);
        if (result.success) {
            setSubmitted(true);
            setShowForm(false);
            // Optimistic update
            setReviews(prev => [{
                ...form,
                verified: !!form.orderId,
                createdAt: new Date().toISOString(),
            }, ...prev]);
        } else {
            setError(result.error ?? 'Error al enviar. Intenta de nuevo.');
        }
    };

    const avg = getAverageRating(reviews);

    return (
        <section className="py-20 bg-paper" id="opiniones">
            <div className="container mx-auto px-4 max-w-4xl">
                {/* Header */}
                <div className="text-center mb-12">
                    <h2 className="text-4xl font-playfair font-bold text-primary mb-2">Opiniones de Clientes</h2>
                    {reviews.length > 0 && (
                        <div className="flex items-center justify-center gap-3 mt-4">
                            <StarRating value={Math.round(avg)} />
                            <span className="text-3xl font-bold text-secondary">{avg.toFixed(1)}</span>
                            <span className="text-gray-400 text-sm">({reviews.length} reseñas)</span>
                        </div>
                    )}
                </div>

                {/* CTA */}
                {!showForm && !submitted && (
                    <div className="text-center mb-10">
                        <button
                            onClick={() => setShowForm(true)}
                            className="bg-secondary text-primary px-8 py-3 rounded-full font-bold shadow-lg hover:scale-105 transition-all"
                        >
                            ✍️ Escribe tu Reseña
                        </button>
                        <p className="text-xs text-gray-400 mt-2">¿Tienes tu N° de pedido? Obtendrás el badge ✅ Verificado</p>
                    </div>
                )}

                {submitted && (
                    <div className="text-center mb-10 bg-green-50 border border-green-200 rounded-2xl p-6">
                        <p className="text-green-700 font-bold text-lg">🎉 ¡Gracias por tu reseña!</p>
                    </div>
                )}

                {/* Review Form */}
                {showForm && (
                    <form onSubmit={handleSubmit} className="bg-white p-8 rounded-3xl shadow-md border border-primary/5 mb-12 space-y-5 animate-fade-up">
                        <h3 className="text-xl font-playfair font-bold text-primary">Tu Opinión</h3>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <input
                                required
                                placeholder="Tu nombre"
                                value={form.customerName}
                                onChange={e => setForm(f => ({ ...f, customerName: e.target.value }))}
                                className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-secondary text-sm"
                            />
                            <input
                                placeholder="N° de Pedido (opcional)"
                                value={form.orderId}
                                onChange={e => setForm(f => ({ ...f, orderId: e.target.value }))}
                                className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-secondary text-sm"
                            />
                        </div>

                        <input
                            placeholder="Producto (opcional)"
                            value={form.product}
                            onChange={e => setForm(f => ({ ...f, product: e.target.value }))}
                            className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-secondary text-sm"
                        />

                        <div>
                            <p className="text-sm font-bold text-primary mb-2">Tu calificación</p>
                            <StarRating value={form.rating} onChange={v => setForm(f => ({ ...f, rating: v }))} />
                        </div>

                        <textarea
                            required
                            placeholder="¿Qué te pareció? (mínimo 5 caracteres)"
                            value={form.comment}
                            onChange={e => setForm(f => ({ ...f, comment: e.target.value }))}
                            rows={4}
                            className="w-full border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-secondary text-sm resize-none"
                        />

                        {error && <p className="text-red-500 text-sm">{error}</p>}

                        <div className="flex gap-3">
                            <button
                                type="submit"
                                disabled={submitting}
                                className="bg-primary text-paper px-8 py-3 rounded-xl font-bold hover:bg-secondary hover:text-primary transition-all disabled:opacity-50"
                            >
                                {submitting ? 'Enviando...' : 'Publicar Reseña'}
                            </button>
                            <button type="button" onClick={() => setShowForm(false)} className="text-gray-400 hover:text-primary text-sm px-4">
                                Cancelar
                            </button>
                        </div>
                    </form>
                )}

                {/* Reviews List */}
                {loading ? (
                    <div className="text-center text-gray-400 py-12">Cargando reseñas...</div>
                ) : reviews.length === 0 ? (
                    <div className="text-center text-gray-400 py-12">
                        <span className="text-6xl block mb-4">💬</span>
                        <p>¡Sé el primero en dejar tu opinión!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {reviews.map((review, idx) => (
                            <div key={review.id ?? idx} className="bg-white p-6 rounded-2xl shadow-sm border border-primary/5 space-y-3 animate-fade-up" style={{ animationDelay: `${idx * 0.05}s` }}>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <p className="font-bold text-primary flex items-center gap-2">
                                            {review.customerName}
                                            {review.verified && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">✅ Verificado</span>}
                                        </p>
                                        {review.product && <p className="text-xs text-gray-400">{review.product}</p>}
                                    </div>
                                    <StarRating value={review.rating} />
                                </div>
                                <p className="text-gray-600 text-sm leading-relaxed">{review.comment}</p>
                                <p className="text-xs text-gray-300">{new Date(review.createdAt).toLocaleDateString('es-PE', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}
