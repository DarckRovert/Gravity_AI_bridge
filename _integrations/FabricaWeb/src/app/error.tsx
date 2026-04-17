"use client";

import { useEffect } from "react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error(error);
    }, [error]);

    return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-4">
            <div className="text-8xl mb-6">🍪</div>
            <h2 className="text-3xl font-playfair font-bold text-primary mb-4">
                ¡Ups! Algo salió mal en el horno.
            </h2>
            <p className="text-gray-500 mb-8 max-w-md">
                Lo sentimos, ha ocurrido un error inesperado. Nuestro equipo de reposteros ya está investigando.
            </p>
            <div className="flex gap-4">
                <button
                    onClick={() => reset()}
                    className="bg-secondary text-white px-8 py-3 rounded-full font-bold shadow-lg hover:scale-105 transition-all"
                >
                    Intentar de nuevo
                </button>
                <a
                    href="/"
                    className="border-2 border-primary/10 text-primary px-8 py-3 rounded-full font-bold hover:bg-primary/5 transition-all"
                >
                    Volver al Inicio
                </a>
            </div>
        </div>
    );
}
