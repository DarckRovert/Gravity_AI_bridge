"use client";

import { useEffect, ReactNode, useRef, useState, useMemo } from 'react';
import { create } from 'zustand';
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
    businessName: 'Antojitos Express',
    heroTitle: 'El Sabor que Mereces,\n Rápido y Fresco',
    heroSubtitle: 'La fuente de soda hasta tu casa. Jugos, empanadas, postres y sándwiches frescos y listos para disfrutar.',
    heroImage: '/img/products/pionono-choco-frutos.jpg',
    heroCtaText: 'Ver Menú Completo',
    whatsappNumber: '51965968723',
    scheduleText: '9:00 AM - 10:00 PM',
    footerTagline: 'Fuente de soda dedicada a entregar felicidad rápida y sabrosa.',
    metaDescription: 'Jugos, empanadas, sandwiches, pasteles y postres. Pedido online rápido.',
    adminPassword: 'cd4ba2d8fccb75a30c84f9f4fc697040f7e93c8f8a0198fdb73414bc3e73f0e2',
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
// 🔧 ZUSTAND STORE
// ========================

export interface SiteConfigContextType {
    config: SiteConfig;
    setConfig: (updater: SiteConfig | ((prev: SiteConfig) => SiteConfig)) => void;
    
    updateProduct: (id: string, changes: Partial<Product>) => void;
    addProduct: (product: Product) => void;
    removeProduct: (id: string) => void;

    addCoupon: (coupon: Coupon) => void;
    removeCoupon: (code: string) => void;
    getCoupons: () => Coupon[];

    setTheme: (changes: Partial<ThemeConfig>) => void;
    resetTheme: () => void;

    setContent: (changes: Partial<ContentConfig>) => void;
    resetContent: () => void;

    setSectionVisibility: (sectionId: string, visible: boolean) => void;
    reorderSections: (sectionId: string, newOrder: number) => void;
    setShowNewsletter: (show: boolean) => void;
    toggleBlockedDate: (date: string) => void;

    addPromotion: (promo: Promotion) => void;
    removePromotion: (index: number) => void;

    updateZone: (name: string, changes: Partial<DeliveryZone>) => void;
    addZone: (zone: DeliveryZone) => void;
    removeZone: (name: string) => void;

    addTestimonial: (testimonial: Testimonial) => void;
    removeTestimonial: (index: number) => void;

    addCustomer: (record: CustomerRecord) => void;
    updateCustomer: (phone: string, changes: Partial<CustomerRecord>) => void;
    getCustomer: (phone: string) => CustomerRecord | undefined;
    getTopCustomers: (limit?: number) => CustomerRecord[];

    logAction: (action: string, details: string, category: ActionLogEntry['category']) => void;
    getRecentActions: (limit?: number) => ActionLogEntry[];

    resetAll: () => void;
}

export const useSiteStore = create<SiteConfigContextType>((set, get) => ({
    config: defaultConfig,
    setConfig: (updater) => set(state => ({ config: typeof updater === 'function' ? updater(state.config) : updater })),

    updateProduct: (id, changes) => set(state => ({ config: { ...state.config, products: state.config.products.map(p => p.id === id ? { ...p, ...changes } : p) } })),
    addProduct: (product) => set(state => ({ config: { ...state.config, products: [...state.config.products, product] } })),
    removeProduct: (id) => set(state => ({ config: { ...state.config, products: state.config.products.filter(p => p.id !== id) } })),

    addCoupon: (coupon) => set(state => ({ config: { ...state.config, coupons: [...state.config.coupons.filter(c => c.code !== coupon.code), coupon] } })),
    removeCoupon: (code) => set(state => ({ config: { ...state.config, coupons: state.config.coupons.filter(c => c.code !== code) } })),
    getCoupons: () => get().config.coupons.filter(c => c.active),

    setTheme: (changes) => set(state => ({ config: { ...state.config, theme: { ...state.config.theme, ...changes } } })),
    resetTheme: () => set(state => ({ config: { ...state.config, theme: defaultTheme } })),

    setContent: (changes) => set(state => ({ config: { ...state.config, content: { ...state.config.content, ...changes } } })),
    resetContent: () => set(state => ({ config: { ...state.config, content: defaultContent } })),

    setSectionVisibility: (sectionId, visible) => set(state => ({ config: { ...state.config, layout: { ...state.config.layout, sections: state.config.layout.sections.map(s => s.id === sectionId ? { ...s, visible } : s) } } })),
    reorderSections: (sectionId, newOrder) => set(state => {
        const sections = [...state.config.layout.sections];
        const idx = sections.findIndex(s => s.id === sectionId);
        if (idx === -1) return state;
        const [item] = sections.splice(idx, 1);
        item.order = newOrder;
        sections.splice(newOrder, 0, item);
        sections.forEach((s, i) => (s.order = i));
        return { config: { ...state.config, layout: { ...state.config.layout, sections } } };
    }),
    setShowNewsletter: (show) => set(state => ({ config: { ...state.config, layout: { ...state.config.layout, showNewsletter: show } } })),
    toggleBlockedDate: (date) => set(state => {
        const blocked = state.config.layout.blockedDates || [];
        const isBlocked = blocked.includes(date);
        return { config: { ...state.config, layout: { ...state.config.layout, blockedDates: isBlocked ? blocked.filter(d => d !== date) : [...blocked, date] } } };
    }),

    addPromotion: (promo) => set(state => ({ config: { ...state.config, promotions: [...state.config.promotions, promo] } })),
    removePromotion: (index) => set(state => ({ config: { ...state.config, promotions: state.config.promotions.filter((_, i) => i !== index) } })),

    updateZone: (name, changes) => set(state => ({ config: { ...state.config, deliveryZones: state.config.deliveryZones.map(z => z.name === name ? { ...z, ...changes } : z) } })),
    addZone: (zone) => set(state => ({ config: { ...state.config, deliveryZones: [...state.config.deliveryZones, zone] } })),
    removeZone: (name) => set(state => ({ config: { ...state.config, deliveryZones: state.config.deliveryZones.filter(z => z.name !== name) } })),

    addTestimonial: (testimonial) => set(state => ({ config: { ...state.config, testimonials: [...state.config.testimonials, testimonial] } })),
    removeTestimonial: (index) => set(state => ({ config: { ...state.config, testimonials: state.config.testimonials.filter((_, i) => i !== index) } })),

    addCustomer: (record) => set(state => ({ config: { ...state.config, customerMemory: [...state.config.customerMemory.filter(c => c.phone !== record.phone), record] } })),
    updateCustomer: (phone, changes) => set(state => ({ config: { ...state.config, customerMemory: state.config.customerMemory.map(c => c.phone === phone ? { ...c, ...changes } : c) } })),
    getCustomer: (phone) => get().config.customerMemory.find(c => c.phone === phone),
    getTopCustomers: (limit = 5) => [...get().config.customerMemory].sort((a, b) => b.totalSpent - a.totalSpent).slice(0, limit),

    logAction: (action, details, category) => set(state => ({ config: { ...state.config, actionLog: [{ timestamp: new Date().toISOString(), action, details, category }, ...state.config.actionLog.slice(0, 99)] } })),
    getRecentActions: (limit = 10) => get().config.actionLog.slice(0, limit),

    resetAll: () => {
        set({ config: defaultConfig });
        localStorage.removeItem('antojitos_express_v2');
    },
}));

// ========================
// 🏗️ PROVIDER (Gun.js Sync & CSS Variables)
// ========================

const P2P_DB_NODE = 'antojitos_express';

export function SiteConfigProvider({ children }: { children: ReactNode }) {
    const { config, setConfig } = useSiteStore();
    const [isHydrated, setIsHydrated] = useState(false);
    const fromGunRef = useRef(false);

    // Load from Gun.js
    useEffect(() => {
        const timeout = setTimeout(() => setIsHydrated(true), 2000);
        if (!db) { clearTimeout(timeout); setIsHydrated(true); return; }

        const ref = db.get(P2P_DB_NODE).get('state');
        ref.on((data: unknown) => {
            clearTimeout(timeout);
            if (data && typeof data === 'string') {
                try {
                    const parsed = JSON.parse(data);
                    fromGunRef.current = true;
                    setConfig(prev => ({
                        ...prev,
                        ...parsed,
                        products: parsed.products?.length ? parsed.products : prev.products,
                        coupons: parsed.coupons || prev.coupons,
                        promotions: parsed.promotions || prev.promotions,
                        deliveryZones: parsed.deliveryZones || prev.deliveryZones,
                        testimonials: parsed.testimonials || prev.testimonials,
                        customerMemory: parsed.customerMemory || prev.customerMemory,
                        actionLog: parsed.actionLog || prev.actionLog,
                        theme: { ...prev.theme, ...parsed.theme },
                        content: { ...prev.content, ...parsed.content, adminPassword: parsed.content?.adminPassword || prev.content.adminPassword },
                        layout: { ...prev.layout, ...parsed.layout, blockedDates: parsed.layout?.blockedDates || prev.layout.blockedDates },
                    }));
                    setIsHydrated(true);
                } catch (e) {
                    console.error('Failed to parse P2P state:', e);
                    setIsHydrated(true);
                }
            } else {
                setIsHydrated(true);
            }
        });
    }, []);

    // Persist to Gun.js
    useEffect(() => {
        if (!isHydrated) return;
        if (fromGunRef.current) {
            fromGunRef.current = false;
            return;
        }
        db?.get(P2P_DB_NODE).get('state').put(JSON.stringify(config));
    }, [config, isHydrated]);

    // Apply CSS variables
    useEffect(() => {
        if (!isHydrated) return;
        const root = document.documentElement;

        if (config.theme.darkMode) {
            root.classList.add('dark');
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

    return <>{children}</>;
}

// ========================
// 🪝 HOOKS (Backwards Compatibility using Zustand Selectors)
// ========================

// Deprecated generic hook, provided for complete backwards compatibility
export function useSiteConfig() {
    return useSiteStore();
}

export function useProducts() {
    const products = useSiteStore(state => state.config.products);
    const updateProduct = useSiteStore(state => state.updateProduct);
    const addProduct = useSiteStore(state => state.addProduct);
    const removeProduct = useSiteStore(state => state.removeProduct);
    return { products, updateProduct, addProduct, removeProduct };
}

export function useCoupons() {
    const coupons = useSiteStore(state => state.config.coupons);
    const addCoupon = useSiteStore(state => state.addCoupon);
    const removeCoupon = useSiteStore(state => state.removeCoupon);
    const getActiveCoupons = useSiteStore(state => state.getCoupons);
    return { coupons, addCoupon, removeCoupon, getActiveCoupons };
}

export function useTheme() {
    const theme = useSiteStore(state => state.config.theme);
    const setTheme = useSiteStore(state => state.setTheme);
    const resetTheme = useSiteStore(state => state.resetTheme);
    return { theme, setTheme, resetTheme };
}

export function useContent() {
    const content = useSiteStore(state => state.config.content);
    const setContent = useSiteStore(state => state.setContent);
    const resetContent = useSiteStore(state => state.resetContent);
    return { content, setContent, resetContent };
}

export function useLayout() {
    const layout = useSiteStore(state => state.config.layout);
    const setSectionVisibility = useSiteStore(state => state.setSectionVisibility);
    const reorderSections = useSiteStore(state => state.reorderSections);
    const setShowNewsletter = useSiteStore(state => state.setShowNewsletter);
    const toggleBlockedDate = useSiteStore(state => state.toggleBlockedDate);
    return { layout, setSectionVisibility, reorderSections, setShowNewsletter, toggleBlockedDate };
}

export function useDeliveryZones() {
    const zones = useSiteStore(state => state.config.deliveryZones);
    const updateZone = useSiteStore(state => state.updateZone);
    const addZone = useSiteStore(state => state.addZone);
    const removeZone = useSiteStore(state => state.removeZone);
    return { zones, updateZone, addZone, removeZone };
}

export function useTestimonials() {
    const testimonials = useSiteStore(state => state.config.testimonials);
    const addTestimonial = useSiteStore(state => state.addTestimonial);
    const removeTestimonial = useSiteStore(state => state.removeTestimonial);
    return { testimonials, addTestimonial, removeTestimonial };
}

export function usePromotions() {
    const allPromotions = useSiteStore(state => state.config.promotions);
    const promotions = useMemo(() => allPromotions.filter(p => p.active), [allPromotions]);
    const addPromotion = useSiteStore(state => state.addPromotion);
    const removePromotion = useSiteStore(state => state.removePromotion);
    return { promotions, addPromotion, removePromotion };
}
