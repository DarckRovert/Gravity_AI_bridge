import Link from 'next/link';
import { SiteConfigProvider } from '@/context/SiteConfigContext';

export default function NotFound() {
    return (
        <SiteConfigProvider>
            <main className="min-h-screen bg-paper flex items-center justify-center p-4 font-poppins text-primary">
                <div className="text-center max-w-lg">
                    <div className="text-9xl mb-4 animate-bounce">🧁</div>
                    <h1 className="text-6xl font-playfair font-bold mb-4">404</h1>
                    <h2 className="text-2xl font-bold mb-6">¡Se nos quemó el pastel!</h2>
                    <p className="text-lg mb-8 opacity-80">
                        Lo sentimos, la página que buscas no existe o se la comieron nuestros pasteleros.
                    </p>
                    <Link
                        href="/"
                        className="bg-secondary text-white px-8 py-4 rounded-full font-bold hover:scale-105 transition-transform shadow-xl inline-block"
                    >
                        Volver al Menú 🍰
                    </Link>
                </div>
            </main>
        </SiteConfigProvider>
    );
}
