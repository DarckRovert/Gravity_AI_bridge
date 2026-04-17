"use client";

import { useContent } from '@/context/SiteConfigContext';

export default function Footer() {
    const { content } = useContent();

    return (
        <footer className="bg-primary text-paper pt-12 pb-6 mt-auto">
            <div className="container mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">

                {/* Brand */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 font-bold text-xl font-fredoka">
                        <span>🍍</span>
                        <span>{content.businessName}</span>
                    </div>
                    <p className="opacity-80 leading-relaxed">
                        {content.footerTagline}
                    </p>
                </div>

                {/* Links */}
                <div className="flex flex-col space-y-2">
                    <h4 className="font-bold text-lg mb-2 text-amber-200">Navegación</h4>
                    <a href="/" className="hover:text-amber-200 transition opacity-80 hover:opacity-100">Inicio</a>
                    <a href="/menu" className="hover:text-amber-200 transition opacity-80 hover:opacity-100">Menú Completo</a>
                    <a href="/tracker" className="hover:text-amber-200 transition opacity-80 hover:opacity-100">🛵 Rastrear Pedido</a>
                    <button
                        id="pwa-install-btn"
                        className="text-left hover:text-amber-200 transition opacity-80 hover:opacity-100 mt-2 font-bold"
                        style={{ display: 'none' }}
                    >📱 Instalar Aplicación</button>
                </div>

                {/* Social */}
                <div>
                    <h4 className="font-bold text-lg mb-4 text-amber-200">Síguenos</h4>
                    <div className="flex flex-col space-y-2">
                        <a href="#" className="flex items-center gap-2 hover:text-amber-200 transition opacity-80 hover:opacity-100">
                            <span>📘</span> Facebook
                        </a>
                        <a href="#" className="flex items-center gap-2 hover:text-amber-200 transition opacity-80 hover:opacity-100">
                            <span>📸</span> Instagram
                        </a>
                        <a href={`https://wa.me/${content.whatsappNumber}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-amber-200 transition opacity-80 hover:opacity-100">
                            <span>💬</span> WhatsApp
                        </a>
                    </div>
                </div>
            </div>

            <div className="border-t border-white/10 pt-6 text-center text-sm opacity-60">
                <p>&copy; 2026 {content.businessName}. Todos los derechos reservados. | Desarrollado por <span className="text-amber-200 font-semibold">DarckRovert</span></p>
            </div>
        </footer>
    );
}
