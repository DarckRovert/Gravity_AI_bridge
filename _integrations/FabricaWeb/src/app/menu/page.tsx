"use client";

import { useState, useMemo } from 'react';
import ProductCard from '@/components/ProductCard';
import ProductSkeleton from '@/components/ProductSkeleton';
import { useProducts } from '@/context/SiteConfigContext';

const categories = [
    { id: 'all', label: 'Todos', icon: '🍍' },
    { id: 'jugos', label: 'Jugos', icon: '🥤' },
    { id: 'sandwichs', label: 'Sánguches', icon: '🥪' },
    { id: 'empanadas', label: 'Empanadas', icon: '🥟' },
    { id: 'postres', label: 'Postres', icon: '🍮' },
    { id: 'pasteles', label: 'Pasteles', icon: '🍰' },
    { id: 'bebidas-frias', label: 'Bebidas Frías', icon: '🧊' },
    { id: 'bebidas-calientes', label: 'Bebidas Calientes', icon: '☕' }
];

export default function MenuPage() {
    const { products } = useProducts();
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('featured');
    const [maxPrice, setMaxPrice] = useState(200);
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    const filteredAndSortedProducts = useMemo(() => {
        let result = products.filter(p => {
            const matchesCategory = activeCategory === 'all' || p.category === activeCategory;
            const matchesSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                p.description.toLowerCase().includes(searchQuery.toLowerCase());
            const matchesPrice = p.price <= maxPrice;
            return matchesCategory && matchesSearch && matchesPrice;
        });

        // Sorting logic
        result.sort((a, b) => {
            if (sortBy === 'price-asc') return a.price - b.price;
            if (sortBy === 'price-desc') return b.price - a.price;
            if (sortBy === 'featured') {
                if (a.featured && !b.featured) return -1;
                if (!a.featured && b.featured) return 1;
                return 0;
            }
            return 0;
        });

        return result;
    }, [products, activeCategory, searchQuery, sortBy, maxPrice]);

    const actualMaxPrice = Math.max(...products.map(p => p.price), 0);

    return (
        <div className="container mx-auto px-4 py-12 max-w-7xl animate-fade-in">
            <header className="text-center mb-16 space-y-4">
                <h1 className="text-5xl md:text-6xl font-playfair font-black text-primary tracking-tight">
                    Nuestra Carta <span className="text-secondary">Artesanal</span>
                </h1>
                <p className="text-gray-500 max-w-2xl mx-auto text-lg italic">
                    Cada bocado es una historia de amor horneada con los mejores ingredientes peruanos.
                </p>
                <div className="w-24 h-1 bg-secondary mx-auto rounded-full mt-6" />
            </header>

            <div className="flex flex-col lg:flex-row gap-8 items-start">
                {/* Filters Sidebar */}
                <aside className="w-full lg:w-64 space-y-8 bg-white p-8 rounded-[2rem] shadow-sm border border-primary/5 lg:sticky lg:top-24">
                    {/* Search */}
                    <div className="space-y-3">
                        <label className="text-xs font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                            <span>🔍</span> Buscar
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="¿Qué se te antoja?"
                                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary transition-all text-sm"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Sorting */}
                    <div className="space-y-3">
                        <label className="text-xs font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                            <span>🔃</span> Ordenar por
                        </label>
                        <select
                            className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:border-secondary appearance-none cursor-pointer text-sm font-medium"
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                        >
                            <option value="featured">Recomendados ✨</option>
                            <option value="price-asc">Precio: Menor a Mayor 📉</option>
                            <option value="price-desc">Precio: Mayor a Menor 📈</option>
                        </select>
                    </div>

                    {/* Price Range */}
                    <div className="space-y-4">
                        <div className="flex justify-between items-center text-xs font-bold text-primary uppercase tracking-widest">
                            <span className="flex items-center gap-2"><span>💰</span> Precio Máx.</span>
                            <span className="text-secondary">S/ {maxPrice}</span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max={actualMaxPrice || 200}
                            step="5"
                            value={maxPrice}
                            onChange={(e) => setMaxPrice(parseInt(e.target.value))}
                            className="w-full h-2 bg-gray-100 rounded-lg appearance-none cursor-pointer accent-secondary"
                        />
                        <div className="flex justify-between text-[10px] text-gray-400 font-bold uppercase">
                            <span>S/ 0</span>
                            <span>S/ {actualMaxPrice || 200}</span>
                        </div>
                    </div>

                    <button
                        onClick={() => {
                            setActiveCategory('all');
                            setSearchQuery('');
                            setSortBy('featured');
                            setMaxPrice(200);
                        }}
                        className="w-full py-3 text-xs font-bold text-gray-400 hover:text-primary transition-colors border border-gray-100 rounded-xl"
                    >
                        Limpiar Filtros
                    </button>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 space-y-12">
                    {/* Categories Strip */}
                    <div className="flex overflow-x-auto pb-4 gap-4 no-scrollbar -mx-4 px-4 scroll-smooth">
                        {categories.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => setActiveCategory(cat.id)}
                                className={`flex items-center gap-2 px-6 py-4 rounded-2xl font-bold whitespace-nowrap transition-all shadow-sm border ${activeCategory === cat.id
                                    ? 'bg-primary text-white border-primary scale-105 shadow-xl shadow-primary/20'
                                    : 'bg-white text-primary border-transparent hover:border-primary/10'
                                    }`}
                            >
                                <span className="text-xl">{cat.icon}</span>
                                <span>{cat.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Results Count */}
                    <div className="flex items-center justify-between text-sm text-gray-400 font-medium">
                        <p>Mostrando {filteredAndSortedProducts.length} delicias</p>
                        {activeCategory !== 'all' && (
                            <span className="bg-secondary/10 text-secondary px-3 py-1 rounded-full text-xs font-bold">
                                Categoría: {categories.find(c => c.id === activeCategory)?.label}
                            </span>
                        )}

                        <div className="flex gap-2 ml-auto">
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400 hover:text-primary'}`}
                                aria-label="Vista de cuadrícula"
                            >
                                🔲
                            </button>
                            <button
                                onClick={() => setViewMode('list')}
                                className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400 hover:text-primary'}`}
                                aria-label="Vista de lista"
                            >
                                📄
                            </button>
                        </div>
                    </div>

                    {/* Product Grid / List */}
                    <div className={viewMode === 'grid' ? "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-8" : "flex flex-col gap-6"}>
                        {filteredAndSortedProducts.length > 0 ? (
                            filteredAndSortedProducts.map((product, idx) => (
                                <div key={product.id} className="animate-fade-up" style={{ animationDelay: `${idx * 0.05}s` }}>
                                    <ProductCard product={product} />
                                </div>
                            ))
                        ) : (
                            <div className="col-span-full py-24 text-center space-y-6 bg-white rounded-[3rem] border border-dashed border-gray-200">
                                <span className="text-8xl block grayscale opacity-20">🍯</span>
                                <div className="space-y-2">
                                    <h3 className="text-2xl font-playfair font-bold text-primary">
                                        No encontramos ese sabor...
                                    </h3>
                                    <p className="text-gray-400 max-w-sm mx-auto">
                                        Intenta ajustando tus filtros o busca algo diferente para endulzar tu día.
                                    </p>
                                </div>
                                <button
                                    onClick={() => { setSearchQuery(''); setActiveCategory('all'); setMaxPrice(200); }}
                                    className="bg-secondary text-white px-8 py-3 rounded-full font-bold shadow-lg hover:brightness-110 active:scale-95 transition-all"
                                >
                                    Ver Todo el Menú
                                </button>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
