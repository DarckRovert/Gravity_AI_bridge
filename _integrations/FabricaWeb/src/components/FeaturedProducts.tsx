"use client";

import ProductCard from './ProductCard';
import Link from 'next/link';
import { useProducts } from '@/context/SiteConfigContext';

export default function FeaturedProducts() {
    const { products } = useProducts();
    const featured = products.filter(p => p.featured).slice(0, 4);

    if (featured.length === 0) return null;

    return (
        <section className="py-20 bg-white">
            <div className="container mx-auto px-4">
                <div className="flex justify-between items-end mb-12">
                    <div>
                        <h2 className="text-4xl font-playfair font-bold text-primary mb-2">
                            Nuestras Especialidades
                        </h2>
                        <p className="text-gray-500 font-medium">Lo más pedido por nuestros clientes</p>
                    </div>
                    <Link
                        href="/menu"
                        className="text-accent font-bold hover:text-secondary flex items-center gap-1 transition-colors"
                    >
                        Ver toda la carta <span>→</span>
                    </Link>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {featured.map(product => (
                        <ProductCard key={product.id} product={product} />
                    ))}
                </div>
            </div>
        </section>
    );
}
