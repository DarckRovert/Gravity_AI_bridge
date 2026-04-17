"use client";

import { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef, ReactNode } from 'react';
import { Product, products as initialProducts } from '@/data/products';
import db from '@/lib/gun';

// ========================
// 🎨 INTERFACES
// ========================

export interface Coupon {
    code: string;
    discount: number;
    type: 'percent' | 'fixed';
    active: boolean;
}

export interface DeliveryZone {
    name: string;
    icon: string;
    price: string;
    desc: string;
    color: string;
}

export interface Promotion {
    text: string;
    link: string;
    bgColor?: string;
    active: boolean;
}

export interface Testimonial {
    name: string;
    text: string;
    rating?: number;
}

export interface SectionConfig {
    id: string;
    visible: boolean;
    order: number;
}

export interface ThemeConfig {
    primary: string;
    secondary: string;
    accent: string;
    paper: string;
    darkMode: boolean;
    borderRadius: 'sharp' | 'rounded' | 'pill';
    cardStyle: 'flat' | 'elevated' | 'glass';
}

export interface ContentConfig {
    businessName: string;
    heroTitle: string;
    heroSubtitle: string;
    heroImage: string;
    heroCtaText: string;
    whatsappNumber: string;
    scheduleText: string;
    footerTagline: string;
    metaDescription: string;
    adminPassword?: string;
}

export interface CustomerRecord {
    phone: string;
    name: string;
    totalOrders: number;
    totalSpent: number;
    favoriteProducts: string[];
    lastOrderDate: string;
    vipStatus: boolean;
    notes: string;
}

export interface ActionLogEntry {
    timestamp: string;
    action: string;
    details: string;
    category: 'product' | 'theme' | 'content' | 'coupon' | 'delivery' | 'layout' | 'promo' | 'system';
}

export interface SiteConfig {
    products: Product[];
    coupons: Coupon[];
    theme: ThemeConfig;
    content: ContentConfig;
    layout: {
        sections: SectionConfig[];
        showNewsletter: boolean;
        blockedDates: string[]; // YYYY-MM-DD format
    };
    promotions: Promotion[];
    deliveryZones: DeliveryZone[];
    testimonials: Testimonial[];
    customerMemory: CustomerRecord[];
    actionLog: ActionLogEntry[];
}

// ========================
// 📦 DEFAULTS
// ========================

const defaultTheme: ThemeConfig = {
    primary: '#2D6A4F',
    secondary: '#FFB703',
    accent: '#E85D04',
    paper: '#FFF3E0',
    darkMode: false,
    borderRadius: 'rounded',
    cardStyle: 'elevated',
};

const defaultContent: ContentConfig = {
    businessName: '<BUSINESS_NAME>',
    heroTitle: 'Cambiando el Mundo,\n Una Web a la vez',
    heroSubtitle: 'Plantilla universal para crear plataformas e-commerce, restaurantes o clínicas al instante.',
    heroImage: '/img/placeholder-hero.jpg',
    heroCtaText: 'Ver Servicios',
    whatsappNumber: '123456789',
    scheduleText: 'Lunes a Viernes - 9am a 6pm',
    footerTagline: 'Motor Boilerplate potenciado por IA.',
    metaDescription: 'Sitio generado con Motor Maestro.',
    // SHA-256 of 'admin123'
    adminPassword: '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
};

const defaultCoupons: Coupon[] = [
    { code: 'ANTOJITO10', discount: 10, type: 'percent', active: true },
    { code: 'EXPRESS5', discount: 5, type: 'fixed', active: true },
    { code: 'CUMPLE20', discount: 20, type: 'percent', active: true },
];

const defaultDeliveryZones: DeliveryZone[] = [
    { name: 'Surco', icon: '📍', price: '🎉 ¡GRATIS!', desc: 'Entrega prioritaria', color: 'bg-green-50' },
    { name: 'San Borja', icon: '📍', price: '🎉 ¡GRATIS!', desc: 'Entrega prioritaria', color: 'bg-green-50' },
    { name: 'Miraflores', icon: '🛵', price: 'S/ 5.00', desc: 'Envío estándar', color: 'bg-white' },
    { name: 'San Isidro', icon: '🛵', price: 'S/ 5.00', desc: 'Envío estándar', color: 'bg-white' },
    { name: 'La Molina', icon: '🛵', price: 'S/ 8.00', desc: 'Envío estándar', color: 'bg-white' },
    { name: 'Otras Zonas', icon: '🚗', price: 'Consultar', desc: 'Vía WhatsApp', color: 'bg-amber-50' },
];

const defaultPromotions: Promotion[] = [
    { text: "✨ ¡10% de descuento en tu primer pedido con el código ANTOJITO10! ✨", link: "#menu", active: true },
    { text: "🥤 ¡Combo Empanada + Jugo por solo S/ 15! 🥤", link: "#menu", active: true },
    { text: "🚚 ¡Envío GRATIS a Surco y Miraflores en pedidos > S/ 40! 🚚", link: "#delivery", active: true },
];

const defaultTestimonials: Testimonial[] = [
    { name: 'Maria Fernanda G.', text: 'Pedí el jugo surtido y la empanada de carne, ¡llegó súper rápido y caliente! Excelente servicio.', rating: 5 },
    { name: 'Carlos R.', text: 'La mejor pastelería y fuente de soda de Surco. Los alfajores se deshacen en la boca y el delivery funciona de maravilla 10/10.', rating: 5 },
    { name: 'Ana Sofia P.', text: 'El pionono clásico es exacto a como debe ser, además que la plataforma para pedir es muy fácil de usar y el pago contra entrega es cómodo.', rating: 5 },
];

const defaultSections: SectionConfig[] = [
    { id: 'hero', visible: true, order: 1 },
    { id: 'categories', visible: true, order: 2 },
    { id: 'featured', visible: true, order: 3 },
    { id: 'how-it-works', visible: true, order: 4 },
    { id: 'delivery', visible: true, order: 5 },
    { id: 'nosotros', visible: true, order: 6 },
    { id: 'testimonials', visible: true, order: 7 },
    { id: 'contact', visible: true, order: 8 },
];

const defaultConfig: SiteConfig = {
    products: initialProducts,
    coupons: defaultCoupons,
    theme: defaultTheme,
    content: defaultContent,
    layout: {
        sections: defaultSections,
        showNewsletter: true,
        blockedDates: [],
    },
    promotions: defaultPromotions,
    deliveryZones: defaultDeliveryZones,
    testimonials: defaultTestimonials,
    customerMemory: [],
    actionLog: [],
};

// ========================
// 🔧 CONTEXT TYPE
// ========================

export interface SiteConfigContextType {
    config: SiteConfig;

    // Products
    updateProduct: (id: string, changes: Partial<Product>) => void;
    addProduct: (product: Product) => void;
    removeProduct: (id: string) => void;

    // Coupons
    addCoupon: (coupon: Coupon) => void;
    removeCoupon: (code: string) => void;
    getCoupons: () => Coupon[];

    // Theme
    setTheme: (changes: Partial<ThemeConfig>) => void;
    resetTheme: () => void;

    // Content
    setContent: (changes: Partial<ContentConfig>) => void;
    resetContent: () => void;

    // Layout
    setSectionVisibility: (sectionId: string, visible: boolean) => void;
    reorderSections: (sectionId: string, newOrder: number) => void;
    setShowNewsletter: (show: boolean) => void;
    toggleBlockedDate: (date: string) => void;

    // Promotions
    addPromotion: (promo: Promotion) => void;
    removePromotion: (index: number) => void;

    // Delivery
    updateZone: (name: string, changes: Partial<DeliveryZone>) => void;
    addZone: (zone: DeliveryZone) => void;
    removeZone: (name: string) => void;

    // Testimonials
    addTestimonial: (testimonial: Testimonial) => void;
    removeTestimonial: (index: number) => void;

    // Customer Memory
    addCustomer: (record: CustomerRecord) => void;
    updateCustomer: (phone: string, changes: Partial<CustomerRecord>) => void;
    getCustomer: (phone: string) => CustomerRecord | undefined;
    getTopCustomers: (limit?: number) => CustomerRecord[];

    // Action Log
    logAction: (action: string, details: string, category: ActionLogEntry['category']) => void;
    getRecentActions: (limit?: number) => ActionLogEntry[];

    // Reset
    resetAll: () => void;
}

const SiteConfigContext = createContext<SiteConfigContextType | null>(null);

// ========================
// 🏗️ PROVIDER
// ========================

const STORAGE_KEY = '<BUSINESS_ID>_config_v1';
const P2P_DB_NODE = '<BUSINESS_ID>';

export function SiteConfigProvider({ children }: { children: ReactNode }) {
    const [config, setConfig] = useState<SiteConfig>(defaultConfig);
    const [isHydrated, setIsHydrated] = useState(false);
    const fromGunRef = useRef(false); // Guard to prevent write-back loop

    // Load from Gun.js (P2P Mesh)
    useEffect(() => {
        // Safety timeout: if Gun.js doesn't respond in 2s, unblock the app anyway
        const timeout = setTimeout(() => setIsHydrated(true), 2000);

        if (!db) { clearTimeout(timeout); setIsHydrated(true); return; }

        // Subscribe to real-time updates from the mesh
        const ref = db.get(P2P_DB_NODE).get('state');

        ref.on((data: unknown) => {
            clearTimeout(timeout);
            if (data && typeof data === 'string') {
                try {
                    const parsed = JSON.parse(data);
                    // Mark this update as coming from Gun to prevent write-back
                    fromGunRef.current = true;
                    // Merge with defaults/prev to ensure schema integrity
                    setConfig(prev => ({
                        ...prev,
                        ...parsed,
                        products: parsed.products?.length ? parsed.products : prev.products,
                        theme: { ...prev.theme, ...parsed.theme },
                        content: {
                            ...prev.content,
                            ...parsed.content,
                            // Always keep default password as fallback if stored one is missing
                            adminPassword: parsed.content?.adminPassword || prev.content.adminPassword,
                        },
                        layout: { ...prev.layout, ...parsed.layout, blockedDates: parsed.layout?.blockedDates || prev.layout.blockedDates },
                    }));
                    setIsHydrated(true);
                } catch (e) {
                    console.error('Failed to parse P2P state:', e);
                    setIsHydrated(true);
                }
            } else {
                // No data or Gun internal object — use defaults
                setIsHydrated(true);
            }
        });
    }, []);

    // Persist to Gun.js on change (only for LOCAL changes, not Gun-originated)
    useEffect(() => {
        if (!isHydrated) return;
        // Skip if this change came from Gun itself (prevents infinite loop)
        if (fromGunRef.current) {
            fromGunRef.current = false;
            return;
        }
        db?.get(P2P_DB_NODE).get('state').put(JSON.stringify(config));
    }, [config, isHydrated]);

    // Apply CSS variables when theme changes
    useEffect(() => {
        if (!isHydrated) return;
        const root = document.documentElement;

        if (config.theme.darkMode) {
            root.classList.add('dark');
            // In dark mode, we let the globals.css variables handle the colors
            // to ensure proper contrast unless we want to allow custom dark colors later.
            root.style.removeProperty('--color-primary');
            root.style.removeProperty('--color-secondary');
            root.style.removeProperty('--color-accent');
            root.style.removeProperty('--color-paper');
            root.style.removeProperty('--background');
            root.style.removeProperty('--foreground');
        } else {
            root.classList.remove('dark');
            root.style.setProperty('--color-primary', config.theme.primary);
            root.style.setProperty('--color-secondary', config.theme.secondary);
            root.style.setProperty('--color-accent', config.theme.accent);
            root.style.setProperty('--color-paper', config.theme.paper);
            root.style.setProperty('--background', config.theme.paper);
            root.style.setProperty('--foreground', config.theme.primary);
        }
    }, [config.theme.darkMode, config.theme.primary, config.theme.secondary, config.theme.accent, config.theme.paper, isHydrated]);

    // ── Products ──
    const updateProduct = useCallback((id: string, changes: Partial<Product>) => {
        setConfig(prev => ({
            ...prev,
            products: prev.products.map(p => p.id === id ? { ...p, ...changes } : p),
        }));
    }, []);

    const addProduct = useCallback((product: Product) => {
        setConfig(prev => ({
            ...prev,
            products: [...prev.products, product],
        }));
    }, []);

    const removeProduct = useCallback((id: string) => {
        setConfig(prev => ({
            ...prev,
            products: prev.products.filter(p => p.id !== id),
        }));
    }, []);

    // ── Coupons ──
    const addCoupon = useCallback((coupon: Coupon) => {
        setConfig(prev => ({
            ...prev,
            coupons: [...prev.coupons.filter(c => c.code !== coupon.code), coupon],
        }));
    }, []);

    const removeCoupon = useCallback((code: string) => {
        setConfig(prev => ({
            ...prev,
            coupons: prev.coupons.filter(c => c.code !== code),
        }));
    }, []);

    const getCoupons = useCallback(() => config.coupons.filter(c => c.active), [config.coupons]);

    // ── Theme ──
    const setThemeConfig = useCallback((changes: Partial<ThemeConfig>) => {
        setConfig(prev => ({
            ...prev,
            theme: { ...prev.theme, ...changes },
        }));
    }, []);

    const resetTheme = useCallback(() => {
        setConfig(prev => ({ ...prev, theme: defaultTheme }));
    }, []);

    // ── Content ──
    const setContentConfig = useCallback((changes: Partial<ContentConfig>) => {
        setConfig(prev => ({
            ...prev,
            content: { ...prev.content, ...changes },
        }));
    }, []);

    const resetContent = useCallback(() => {
        setConfig(prev => ({ ...prev, content: defaultContent }));
    }, []);

    // ── Layout ──
    const setSectionVisibility = useCallback((sectionId: string, visible: boolean) => {
        setConfig(prev => ({
            ...prev,
            layout: {
                ...prev.layout,
                sections: prev.layout.sections.map(s =>
                    s.id === sectionId ? { ...s, visible } : s
                ),
            },
        }));
    }, []);

    const reorderSections = useCallback((sectionId: string, newOrder: number) => {
        setConfig(prev => {
            const sections = [...prev.layout.sections];
            const idx = sections.findIndex(s => s.id === sectionId);
            if (idx === -1) return prev;
            const [item] = sections.splice(idx, 1);
            item.order = newOrder;
            sections.splice(newOrder, 0, item);
            // Re-index orders
            sections.forEach((s, i) => (s.order = i));
            return { ...prev, layout: { ...prev.layout, sections } };
        });
    }, []);

    const setShowNewsletter = useCallback((show: boolean) => {
        setConfig(prev => ({
            ...prev,
            layout: { ...prev.layout, showNewsletter: show },
        }));
    }, []);

    const toggleBlockedDate = useCallback((date: string) => {
        setConfig(prev => {
            const blocked = prev.layout.blockedDates || [];
            const isBlocked = blocked.includes(date);
            return {
                ...prev,
                layout: {
                    ...prev.layout,
                    blockedDates: isBlocked ? blocked.filter(d => d !== date) : [...blocked, date]
                }
            };
        });
    }, []);

    // ── Promotions ──
    const addPromotion = useCallback((promo: Promotion) => {
        setConfig(prev => ({
            ...prev,
            promotions: [...prev.promotions, promo],
        }));
    }, []);

    const removePromotion = useCallback((index: number) => {
        setConfig(prev => ({
            ...prev,
            promotions: prev.promotions.filter((_, i) => i !== index),
        }));
    }, []);

    // ── Delivery Zones ──
    const updateZone = useCallback((name: string, changes: Partial<DeliveryZone>) => {
        setConfig(prev => ({
            ...prev,
            deliveryZones: prev.deliveryZones.map(z =>
                z.name === name ? { ...z, ...changes } : z
            ),
        }));
    }, []);

    const addZone = useCallback((zone: DeliveryZone) => {
        setConfig(prev => ({
            ...prev,
            deliveryZones: [...prev.deliveryZones, zone],
        }));
    }, []);

    const removeZone = useCallback((name: string) => {
        setConfig(prev => ({
            ...prev,
            deliveryZones: prev.deliveryZones.filter(z => z.name !== name),
        }));
    }, []);

    // ── Testimonials ──
    const addTestimonial = useCallback((testimonial: Testimonial) => {
        setConfig(prev => ({
            ...prev,
            testimonials: [...prev.testimonials, testimonial],
        }));
    }, []);

    const removeTestimonial = useCallback((index: number) => {
        setConfig(prev => ({
            ...prev,
            testimonials: prev.testimonials.filter((_, i) => i !== index),
        }));
    }, []);

    // ── Customer Memory ──
    const addCustomer = useCallback((record: CustomerRecord) => {
        setConfig(prev => ({
            ...prev,
            customerMemory: [...prev.customerMemory.filter(c => c.phone !== record.phone), record],
        }));
    }, []);

    const updateCustomer = useCallback((phone: string, changes: Partial<CustomerRecord>) => {
        setConfig(prev => ({
            ...prev,
            customerMemory: prev.customerMemory.map(c =>
                c.phone === phone ? { ...c, ...changes } : c
            ),
        }));
    }, []);

    const getCustomer = useCallback((phone: string) => {
        return config.customerMemory.find(c => c.phone === phone);
    }, [config.customerMemory]);

    const getTopCustomers = useCallback((limit = 5) => {
        return [...config.customerMemory]
            .sort((a, b) => b.totalSpent - a.totalSpent)
            .slice(0, limit);
    }, [config.customerMemory]);

    // ── Action Log ──
    const logAction = useCallback((action: string, details: string, category: ActionLogEntry['category']) => {
        setConfig(prev => ({
            ...prev,
            actionLog: [
                { timestamp: new Date().toISOString(), action, details, category },
                ...prev.actionLog.slice(0, 99), // Keep last 100
            ],
        }));
    }, []);

    const getRecentActions = useCallback((limit = 10) => {
        return config.actionLog.slice(0, limit);
    }, [config.actionLog]);

    // ── Reset All ──
    const resetAll = useCallback(() => {
        setConfig(defaultConfig);
        localStorage.removeItem(STORAGE_KEY);
    }, []);

    const value: SiteConfigContextType = useMemo(() => ({
        config,
        updateProduct, addProduct, removeProduct,
        addCoupon, removeCoupon, getCoupons,
        setTheme: setThemeConfig, resetTheme,
        setContent: setContentConfig, resetContent,
        setSectionVisibility, reorderSections, setShowNewsletter, toggleBlockedDate,
        addPromotion, removePromotion,
        updateZone, addZone, removeZone,
        addTestimonial, removeTestimonial,
        addCustomer, updateCustomer, getCustomer, getTopCustomers,
        logAction, getRecentActions,
        resetAll,
    }), [config, updateProduct, addProduct, removeProduct, addCoupon, removeCoupon, getCoupons, setThemeConfig, resetTheme, setContentConfig, resetContent, setSectionVisibility, reorderSections, setShowNewsletter, toggleBlockedDate, addPromotion, removePromotion, updateZone, addZone, removeZone, addTestimonial, removeTestimonial, addCustomer, updateCustomer, getCustomer, getTopCustomers, logAction, getRecentActions, resetAll]);

    return (
        <SiteConfigContext.Provider value={value}>
            {children}
        </SiteConfigContext.Provider>
    );
}

// ========================
// 🪝 HOOKS
// ========================

export function useSiteConfig() {
    const context = useContext(SiteConfigContext);
    if (!context) throw new Error('useSiteConfig must be used within SiteConfigProvider');
    return context;
}

// Convenience hooks
export function useProducts() {
    const { config, updateProduct, addProduct, removeProduct } = useSiteConfig();
    return { products: config.products, updateProduct, addProduct, removeProduct };
}

export function useCoupons() {
    const { config, addCoupon, removeCoupon, getCoupons } = useSiteConfig();
    return { coupons: config.coupons, addCoupon, removeCoupon, getActiveCoupons: getCoupons };
}

export function useTheme() {
    const { config, setTheme, resetTheme } = useSiteConfig();
    return { theme: config.theme, setTheme, resetTheme };
}

export function useContent() {
    const { config, setContent, resetContent } = useSiteConfig();
    return { content: config.content, setContent, resetContent };
}

export function useLayout() {
    const { config, setSectionVisibility, reorderSections, setShowNewsletter, toggleBlockedDate } = useSiteConfig();
    return { layout: config.layout, setSectionVisibility, reorderSections, setShowNewsletter, toggleBlockedDate };
}

export function useDeliveryZones() {
    const { config, updateZone, addZone, removeZone } = useSiteConfig();
    return { zones: config.deliveryZones, updateZone, addZone, removeZone };
}

export function useTestimonials() {
    const { config, addTestimonial, removeTestimonial } = useSiteConfig();
    return { testimonials: config.testimonials, addTestimonial, removeTestimonial };
}

export function usePromotions() {
    const { config, addPromotion, removePromotion } = useSiteConfig();
    return { promotions: config.promotions.filter(p => p.active), addPromotion, removePromotion };
}
