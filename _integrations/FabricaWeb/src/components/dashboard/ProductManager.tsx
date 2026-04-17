"use client";

import { useSiteConfig } from '@/context/SiteConfigContext';
import { Product } from '@/data/products';
import { useState } from 'react';

interface ProductManagerProps {
    onToast?: (msg: string, type: 'success' | 'error') => void;
}

export function ProductManager({ onToast }: ProductManagerProps) {
    const { config, updateProduct, removeProduct, addProduct } = useSiteConfig();
    const products = config?.products || [];
    const [search, setSearch] = useState('');
    const [activeCategory, setActiveCategory] = useState('all');
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editPrice, setEditPrice] = useState('');
    const [showForm, setShowForm] = useState(false);

    // New product form state
    const [newTitle, setNewTitle] = useState('');
    const [newCategory, setNewCategory] = useState('');
    const [newPrice, setNewPrice] = useState('');
    const [newDescription, setNewDescription] = useState('');

    // Get unique categories
    const categories = ['all', ...new Set(products.map(p => p.category).filter(Boolean))];

    // Filter products
    const filtered = products.filter(p => {
        const matchesSearch = p.title.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = activeCategory === 'all' || p.category === activeCategory;
        return matchesSearch && matchesCategory;
    });

    const handleStockToggle = (product: Product) => {
        const newStock = product.stock === 'available' ? 'out_of_stock' : 'available';
        updateProduct(product.id, { stock: newStock });
        onToast?.(`${product.title} → ${newStock === 'available' ? '✅ Disponible' : '❌ Agotado'}`, 'success');
    };

    const handleToggleFeatured = (product: Product) => {
        updateProduct(product.id, { featured: !product.featured });
        onToast?.(`${product.title} → ${product.featured ? 'Quitado de' : 'Añadido a'} destacados`, 'success');
    };

    const handleSavePrice = (product: Product) => {
        const newPrice = parseFloat(editPrice);
        if (isNaN(newPrice) || newPrice <= 0) {
            onToast?.('Precio inválido', 'error');
            return;
        }
        updateProduct(product.id, { price: newPrice });
        onToast?.(`${product.title} → S/${newPrice.toFixed(2)}`, 'success');
        setEditingId(null);
        setEditPrice('');
    };

    const handleDelete = (product: Product) => {
        if (confirm(`¿Eliminar "${product.title}"?`)) {
            removeProduct(product.id);
            onToast?.(`${product.title} eliminado`, 'success');
        }
    };

    const handleAddProduct = () => {
        if (!newTitle.trim()) { onToast?.('Ingresa un nombre', 'error'); return; }
        if (!newCategory.trim()) { onToast?.('Ingresa una categoría', 'error'); return; }
        const price = parseFloat(newPrice);
        if (isNaN(price) || price <= 0) { onToast?.('Precio inválido', 'error'); return; }

        const newProduct: Product = {
            id: `prod-${Date.now()}`,
            title: newTitle.trim(),
            category: newCategory.trim().toLowerCase(),
            price,
            description: newDescription.trim() || `Nuevo producto: ${newTitle.trim()}`,
            image: '/img/products/cake-chocolate.jpg',
            stock: 'available',
            featured: false,
        };

        addProduct(newProduct);
        onToast?.(`✅ ${newProduct.title} agregado`, 'success');
        setNewTitle('');
        setNewCategory('');
        setNewPrice('');
        setNewDescription('');
        setShowForm(false);
    };

    const stockColor = (stock: string) => {
        if (stock === 'out_of_stock') return 'text-red-400 bg-red-900/30';
        if (stock === 'low') return 'text-yellow-400 bg-yellow-900/30';
        return 'text-green-400 bg-green-900/30';
    };

    const stockLabel = (stock: string) => {
        if (stock === 'out_of_stock') return 'Agotado';
        if (stock === 'low') return 'Poco';
        return 'Disponible';
    };

    const formatPrice = (price: number) => `S/${price.toFixed(2)}`;

    return (
        <div className="bg-dash-card border border-dash-border rounded-2xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-playfair font-bold text-secondary">🛒 Gestión de Productos</h2>
                <div className="flex items-center gap-3">
                    <span className="text-dash-border text-sm">{products.length} productos</span>
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="bg-secondary/20 text-secondary px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-secondary/30 transition-all"
                    >
                        {showForm ? '✕ Cerrar' : '+ Agregar'}
                    </button>
                </div>
            </div>

            {/* Add Product Form */}
            {showForm && (
                <div className="bg-dash-bg/50 border border-dash-border/50 rounded-xl p-4 mb-6 space-y-3">
                    <p className="text-white text-sm font-medium mb-2">Nuevo Producto</p>
                    <div className="grid grid-cols-2 gap-3">
                        <input
                            type="text"
                            placeholder="Nombre del producto"
                            value={newTitle}
                            onChange={e => setNewTitle(e.target.value)}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        />
                        <input
                            type="text"
                            placeholder="Categoría (ej: piononos)"
                            value={newCategory}
                            onChange={e => setNewCategory(e.target.value)}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <input
                            type="number"
                            placeholder="Precio (ej: 75)"
                            value={newPrice}
                            onChange={e => setNewPrice(e.target.value)}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        />
                        <input
                            type="text"
                            placeholder="Descripción (opcional)"
                            value={newDescription}
                            onChange={e => setNewDescription(e.target.value)}
                            className="bg-dash-bg border border-dash-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                        />
                    </div>
                    <button
                        onClick={handleAddProduct}
                        className="w-full bg-secondary text-dash-bg py-2 rounded-lg text-sm font-bold hover:bg-white transition-all"
                    >
                        Agregar Producto
                    </button>
                </div>
            )}

            {/* Search + Filter */}
            <div className="flex gap-3 mb-6">
                <input
                    type="text"
                    placeholder="Buscar producto..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="flex-1 bg-dash-bg border border-dash-border rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-secondary transition-all"
                />
                <select
                    value={activeCategory}
                    onChange={e => setActiveCategory(e.target.value)}
                    className="bg-dash-bg border border-dash-border rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-secondary"
                >
                    {categories.map(cat => (
                        <option key={cat} value={cat}>
                            {cat === 'all' ? '📂 Todas' : cat}
                        </option>
                    ))}
                </select>
            </div>

            {/* Product Grid */}
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
                {filtered.length === 0 && (
                    <p className="text-center text-dash-border py-8">No se encontraron productos</p>
                )}
                {filtered.map(product => (
                    <div key={product.id} className="flex items-center gap-4 bg-dash-bg/50 rounded-xl p-3 border border-dash-border/50 hover:border-secondary/30 transition-all group">
                        {/* Image */}
                        <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 bg-dash-border/20">
                            {product.image?.startsWith('data:') ? (
                                <img src={product.image} alt={product.title} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-lg">🧁</div>
                            )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                                <span className="text-white text-sm font-medium truncate">{product.title}</span>
                                {product.featured && <span className="text-[10px] bg-secondary/20 text-secondary px-1.5 py-0.5 rounded">⭐</span>}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                                <span className="text-dash-border text-xs">{product.category || 'Sin categoría'}</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${stockColor(product.stock)}`}>
                                    {stockLabel(product.stock)}
                                </span>
                            </div>
                        </div>

                        {/* Price */}
                        <div className="text-right">
                            {editingId === product.id ? (
                                <div className="flex items-center gap-1">
                                    <input
                                        type="number"
                                        value={editPrice}
                                        onChange={e => setEditPrice(e.target.value)}
                                        className="w-20 bg-dash-bg border border-secondary rounded px-2 py-1 text-white text-sm text-right"
                                        autoFocus
                                        onKeyDown={e => e.key === 'Enter' && handleSavePrice(product)}
                                    />
                                    <button onClick={() => handleSavePrice(product)} className="text-green-400 hover:text-green-300 text-sm">✓</button>
                                    <button onClick={() => setEditingId(null)} className="text-red-400 hover:text-red-300 text-sm">✕</button>
                                </div>
                            ) : (
                                <span
                                    className="text-secondary font-bold text-sm cursor-pointer hover:underline"
                                    onClick={() => { setEditingId(product.id); setEditPrice(product.price.toString()); }}
                                >
                                    {formatPrice(product.price)}
                                </span>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                onClick={() => handleStockToggle(product)}
                                className="p-1.5 rounded-lg hover:bg-dash-border/20 text-xs"
                                title={product.stock === 'available' ? 'Agotar' : 'Reponer'}
                            >
                                {product.stock === 'available' ? '📦' : '♻️'}
                            </button>
                            <button
                                onClick={() => handleToggleFeatured(product)}
                                className="p-1.5 rounded-lg hover:bg-dash-border/20 text-xs"
                                title={product.featured ? 'Quitar destacado' : 'Destacar'}
                            >
                                {product.featured ? '⭐' : '☆'}
                            </button>
                            <button
                                onClick={() => handleDelete(product)}
                                className="p-1.5 rounded-lg hover:bg-red-900/20 text-xs text-red-400"
                                title="Eliminar"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
