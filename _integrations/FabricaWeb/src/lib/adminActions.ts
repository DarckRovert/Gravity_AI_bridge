// ⚡ AdminActions — Las Manos de Pastelito God Mode
// Ejecuta acciones CRUD sobre SiteConfig basadas en intenciones del NLP

import { Product } from '@/data/products';
import { SiteConfig, Coupon, Promotion, DeliveryZone, Testimonial, ThemeConfig, ContentConfig, ActionLogEntry } from '@/context/SiteConfigContext';
import { themePresets } from '@/lib/themeEngine';
import { adminBrain, Order } from './adminBrain';
import { ExtractedEntities } from './pastelitoEngine';

interface Feedback {
    rating: number;
    comment: string;
    product?: string;
    date?: string;
}

export interface ActionResult {
    success: boolean;
    message: string;
    emoji: string;
}

import { SiteConfigContextType } from '@/context/SiteConfigContext';

type ConfigUpdater = SiteConfigContextType;

export class AdminActions {
    constructor(private ctx: ConfigUpdater) { }

    /**
     * Executes a confirmed intention with extracted entities
     * @param intent The detected intent name
     * @param entities The extracted entities from the user input
     * @returns ActionResult with success status and feedback message
     */
    execute(intent: string, entities: ExtractedEntities): ActionResult {
        switch (intent) {
            // ========== PRODUCTS ==========
            case 'cambiar_precio': return this.changePrice(entities);
            case 'agotar_stock': return this.setStock(entities, 'out_of_stock');
            case 'reponer_stock': return this.setStock(entities, 'available');
            case 'stock_bajo': return this.setStock(entities, 'low');
            case 'destacar': return this.setFeatured(entities, true);
            case 'quitar_destacado': return this.setFeatured(entities, false);
            case 'agregar_producto': return this.addProduct(entities);
            case 'eliminar_producto': return this.deleteProduct(entities);
            case 'listar_productos': return this.listProducts();

            // ========== COUPONS ==========
            case 'crear_cupon': return this.createCoupon(entities);
            case 'eliminar_cupon': return this.deleteCoupon(entities);
            case 'listar_cupones': return this.listCoupons();

            // ========== THEME ==========
            case 'tema_preset': return this.applyPreset(entities);
            case 'cambiar_color': return this.changeColor(entities, 'primary');
            case 'cambiar_secundario': return this.changeColor(entities, 'secondary');
            case 'cambiar_fondo': return this.changeColor(entities, 'paper');
            case 'toggle_dark': return this.toggleDark();
            case 'restaurar_tema': return this.restoreTheme();
            case 'ver_tema': return this.showTheme();

            // ========== CONTENT ==========
            case 'cambiar_hero_titulo': return this.changeContent(entities, 'heroTitle');
            case 'cambiar_hero_sub': return this.changeContent(entities, 'heroSubtitle');
            case 'cambiar_hero_cta': return this.changeContent(entities, 'heroCtaText');
            case 'cambiar_nombre': return this.changeContent(entities, 'businessName');
            case 'cambiar_horario': return this.changeContent(entities, 'scheduleText');
            case 'cambiar_whatsapp': return this.changeContent(entities, 'whatsappNumber');
            case 'cambiar_password': return this.changeContent(entities, 'adminPassword');

            // ========== LAYOUT ==========
            case 'ocultar_seccion': return this.toggleSection(entities, false);
            case 'mostrar_seccion': return this.toggleSection(entities, true);
            case 'listar_secciones': return this.listSections();
            case 'ocultar_newsletter': return this.toggleNewsletter(false);
            case 'mostrar_newsletter': return this.toggleNewsletter(true);

            // ========== BANNERS ==========
            case 'agregar_banner': return this.addBanner(entities);
            case 'quitar_banner': return this.removeBanner();
            case 'listar_banners': return this.listBanners();

            // ========== DELIVERY ==========
            case 'cambiar_precio_zona': return this.changeZonePrice(entities);
            case 'agregar_zona': return this.addDeliveryZone(entities);
            case 'delivery_gratis': return this.setFreeDelivery(entities);

            // ========== TESTIMONIALS ==========
            case 'agregar_testimonio': return this.addTestimonialAction(entities);

            // ========== ANALYTICS ==========
            case 'resumen_ejecutivo': return this.executiveReport();
            case 'ver_ventas': return this.salesReport();
            case 'proyeccion': return this.projectionReport();
            case 'producto_top': return this.topProducts();
            case 'producto_flop': return this.flopProducts();
            case 'exportar_csv': return this.exportCSV();
            case 'historial_cambios': return this.showHistory();
            case 'ver_feedback': return this.readFeedback();

            // ========== ANALYTICS v2.0 ==========
            case 'comparacion_semanal': {
                const orders = this.getOrders();
                const weekly = adminBrain.getWeeklyComparison(orders);
                const icon = weekly.trend === 'up' ? '📈' : weekly.trend === 'down' ? '📉' : '➡️';
                return { success: true, emoji: icon, message: `**Comparación semanal:**\n• Esta semana: **${weekly.thisWeek}**\n• Semana pasada: **${weekly.lastWeek}**\n• Cambio: **${weekly.change > 0 ? '+' : ''}${weekly.change}%**` };
            }
            case 'hora_pico': {
                const orders = this.getOrders();
                const peak = adminBrain.getPeakHour(orders);
                return { success: true, emoji: '⏰', message: `Tu **hora pico** es a las **${peak.label}** con ${peak.count} pedidos registrados.` };
            }
            case 'mejor_dia': {
                const orders = this.getOrders();
                const best = adminBrain.getBestDay(orders);
                return { success: true, emoji: '📅', message: `Tu mejor día es el **${best.day}** con ${best.count} pedidos. ¡Prepárate cada semana!` };
            }
            case 'limpiar_chat':
                return { success: true, emoji: '🗑️', message: 'Historial de conversación limpiado.' };

            // ========== WIZARD ACTIONS ==========
            case 'agregar_producto_wizard': {
                const title = entities.product || entities.text || 'Nuevo Producto';
                const price = entities.price || 0;
                // No need for cast anymore as category is in ExtractedEntities
                const category = entities.category || 'tortas';
                const description = entities.text || `Delicioso ${title} artesanal.`;
                const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

                const newProduct: Product = {
                    id: slug,
                    title,
                    category,
                    price,
                    description,
                    image: entities.image || `/img/products/${slug}.jpg`,
                    stock: 'available',
                    featured: false
                };

                this.ctx.addProduct(newProduct);
                this.ctx.logAction('Producto creado (Wizard)', `${title} a S/${price.toFixed(2)} en ${category}`, 'product');
                return { success: true, emoji: '✅', message: `Producto **${title}** creado exitosamente a **S/${price.toFixed(2)}** en la categoría **${category}**.` };
            }

            // ========== CUSTOMERS ==========
            case 'mejor_cliente': return this.bestCustomer();
            case 'buscar_cliente': return this.findCustomer(entities);

            // ========== SYSTEM ==========
            case 'resetear_todo': return this.resetEverything();
            case 'optimizar_todo': return this.optimizeShop();
            case 'modo_estacional': return this.seasonalMode(entities);
            case 'sugerir_mejoras': return this.suggestImprovements();

            // ========== DISPONIBILIDAD ==========
            case 'bloquear_fecha': return this.toggleDateAction(entities, true);
            case 'desbloquear_fecha': return this.toggleDateAction(entities, false);

            default:
                return { success: false, message: `Acción "${intent}" no implementada aún.`, emoji: '🤔' };
        }
    }

    // ── Products ──

    private findProduct(query?: string): Product | null {
        if (!query) return null;
        const norm = query.toLowerCase().trim();
        return this.ctx.config.products.find(p =>
            p.title.toLowerCase().includes(norm) ||
            p.id.toLowerCase().includes(norm) ||
            norm.includes(p.title.toLowerCase())
        ) || null;
    }

    private changePrice(entities: ExtractedEntities): ActionResult {
        const product = this.findProduct(entities.product);
        if (!product) return { success: false, message: `No encontré el producto "${entities.product || '?'}". Intenta con el nombre exacto.`, emoji: '❓' };
        if (!entities.price || entities.price <= 0) return { success: false, message: 'No detecté un precio válido. Ejemplo: "Sube el pionono a S/80"', emoji: '❓' };

        const oldPrice = product.price;
        this.ctx.updateProduct(product.id, { price: entities.price });
        this.ctx.logAction('Cambio de precio', `${product.title}: S/${oldPrice.toFixed(2)} → S/${entities.price.toFixed(2)}`, 'product');
        return { success: true, message: `**${product.title}** actualizado: S/ ${oldPrice.toFixed(2)} → **S/ ${entities.price.toFixed(2)}**`, emoji: '💰' };
    }

    private setStock(entities: ExtractedEntities, stock: 'available' | 'low' | 'out_of_stock'): ActionResult {
        const product = this.findProduct(entities.product);
        if (!product) return { success: false, message: `No encontré ese producto. ¿Cuál quieres modificar?`, emoji: '❓' };

        const labels = { available: 'Disponible ✅', low: 'Pocas unidades ⚠️', out_of_stock: 'Agotado 🔴' };
        this.ctx.updateProduct(product.id, { stock });
        this.ctx.logAction('Cambio de stock', `${product.title} → ${labels[stock]}`, 'product');
        return { success: true, message: `**${product.title}** ahora está: **${labels[stock]}**`, emoji: stock === 'available' ? '✅' : stock === 'low' ? '⚠️' : '🔴' };
    }

    private setFeatured(entities: ExtractedEntities, featured: boolean): ActionResult {
        const product = this.findProduct(entities.product);
        if (!product) return { success: false, message: `No encontré ese producto.`, emoji: '❓' };

        this.ctx.updateProduct(product.id, { featured });
        this.ctx.logAction(featured ? 'Destacado' : 'Quitado de destacados', product.title, 'product');
        return { success: true, message: featured ? `⭐ **${product.title}** ahora está en **Destacados** en la homepage.` : `**${product.title}** fue quitado de Destacados.`, emoji: featured ? '⭐' : '📦' };
    }

    private deleteProduct(entities: ExtractedEntities): ActionResult {
        const product = this.findProduct(entities.product);
        if (!product) return { success: false, message: `No encontré ese producto.`, emoji: '❓' };

        this.ctx.removeProduct(product.id);
        this.ctx.logAction('Producto eliminado', product.title, 'product');
        return { success: true, message: `🗑️ **${product.title}** ha sido **eliminado** de la tienda.`, emoji: '🗑️' };
    }

    private addProduct(entities: ExtractedEntities): ActionResult {
        const title = entities.product || 'Nuevo Producto';
        const price = entities.price || 0;
        const category = entities.category || 'tortas';
        const description = entities.text || `Delicioso ${title} artesanal.`;
        const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

        const newProduct: Product = {
            id: slug,
            title,
            category,
            price,
            description,
            // Re-use current slug for image placeholder if no image entity
            image: entities.image || `/img/products/${slug}.jpg`,
            stock: 'available',
            featured: false
        };

        this.ctx.addProduct(newProduct);
        this.ctx.logAction('Producto creado', `${title} (S/${price})`, 'product');
        return { success: true, message: `✅ **${title}** agregado exitosamente a la tienda.`, emoji: '🧁' };
    }

    private listProducts(): ActionResult {
        const prods = this.ctx.config.products;
        const lines = prods.map(p => {
            const stockIcon = p.stock === 'available' ? '🟢' : p.stock === 'low' ? '🟡' : '🔴';
            const featIcon = p.featured ? '⭐' : '';
            return `${stockIcon} ${featIcon} **${p.title}** — S/ ${p.price.toFixed(2)}`;
        });
        return { success: true, message: `📦 **${prods.length} productos:**\n${lines.join('\n')}`, emoji: '📦' };
    }

    // ── Coupons ──

    private createCoupon(entities: ExtractedEntities): ActionResult {
        if (!entities.couponCode) return { success: false, message: 'Necesito el código del cupón. Ejemplo: "Crea cupón VERANO20 de 20%"', emoji: '❓' };
        const discount = entities.discount || 10;
        const type = entities.discountType || 'percent';

        this.ctx.addCoupon({ code: entities.couponCode, discount, type, active: true });
        this.ctx.logAction('Cupón creado', `${entities.couponCode} — ${discount}${type === 'percent' ? '%' : ' soles'} OFF`, 'coupon');
        return { success: true, message: `🏷️ Cupón **${entities.couponCode}** creado: **${discount}${type === 'percent' ? '%' : ' soles'}** de descuento.`, emoji: '🏷️' };
    }

    private deleteCoupon(entities: ExtractedEntities): ActionResult {
        if (!entities.couponCode) return { success: false, message: 'Necesito el código del cupón. Ejemplo: "Elimina cupón PRIMERA10"', emoji: '❓' };
        this.ctx.removeCoupon(entities.couponCode);
        this.ctx.logAction('Cupón eliminado', entities.couponCode, 'coupon');
        return { success: true, message: `❌ Cupón **${entities.couponCode}** eliminado.`, emoji: '❌' };
    }

    private listCoupons(): ActionResult {
        const coupons = this.ctx.config.coupons.filter(c => c.active);
        if (coupons.length === 0) return { success: true, message: 'No hay cupones activos.', emoji: '🏷️' };
        const lines = coupons.map(c => `🏷️ **${c.code}** — ${c.discount}${c.type === 'percent' ? '%' : ' soles'} OFF`);
        return { success: true, message: `🏷️ **${coupons.length} cupones activos:**\n${lines.join('\n')}`, emoji: '🏷️' };
    }

    // ── Theme ──

    private applyPreset(entities: ExtractedEntities): ActionResult {
        if (!entities.preset) return { success: false, message: 'No encontré ese tema. Disponibles: ' + Object.values(themePresets).map(p => `${p.emoji} ${p.label}`).join(', '), emoji: '🎨' };
        const preset = themePresets[entities.preset];
        this.ctx.setTheme({ primary: preset.primary, secondary: preset.secondary, accent: preset.accent, paper: preset.paper });
        this.ctx.logAction('Tema aplicado', `${preset.emoji} ${preset.label}`, 'theme');
        return { success: true, message: `${preset.emoji} ¡Tema **${preset.label}** activado!\n• Primario: ${preset.primary}\n• Secundario: ${preset.secondary}\n• Acento: ${preset.accent}`, emoji: preset.emoji };
    }

    private changeColor(entities: ExtractedEntities, target: 'primary' | 'secondary' | 'paper'): ActionResult {
        if (!entities.colorHex) return { success: false, message: 'No reconocí ese color. Prueba: rojo, azul, dorado, rosa, verde, negro...', emoji: '🎨' };
        const labels = { primary: 'principal', secondary: 'secundario', paper: 'fondo' };
        this.ctx.setTheme({ [target]: entities.colorHex });
        this.ctx.logAction('Color cambiado', `${labels[target]} → ${entities.color} (${entities.colorHex})`, 'theme');
        return { success: true, message: `🎨 Color **${labels[target]}** cambiado a **${entities.color}** (${entities.colorHex})`, emoji: '🎨' };
    }

    private toggleDark(): ActionResult {
        const newDark = !this.ctx.config.theme.darkMode;
        this.ctx.setTheme({ darkMode: newDark });
        this.ctx.logAction('Dark mode', newDark ? 'Activado' : 'Desactivado', 'theme');
        return { success: true, message: newDark ? '🌙 **Dark Mode activado**' : '☀️ **Modo claro activado**', emoji: newDark ? '🌙' : '☀️' };
    }

    private restoreTheme(): ActionResult {
        this.ctx.resetTheme();
        this.ctx.logAction('Tema restaurado', 'Colores originales', 'theme');
        return { success: true, message: '🏠 Tema **Original** restaurado. ¡De vuelta a casa!', emoji: '🏠' };
    }

    private showTheme(): ActionResult {
        const t = this.ctx.config.theme;
        return {
            success: true,
            message: `🎨 **Tema actual:**\n• Primario: ${t.primary}\n• Secundario: ${t.secondary}\n• Acento: ${t.accent}\n• Fondo: ${t.paper}\n• Dark Mode: ${t.darkMode ? 'Sí 🌙' : 'No ☀️'}`,
            emoji: '🎨'
        };
    }

    // ── Content ──

    private changeContent(entities: ExtractedEntities, field: keyof ContentConfig): ActionResult {
        if (!entities.text) return { success: false, message: `Necesito el nuevo texto. Ejemplo: "Cambia el título a Feliz Navidad"`, emoji: '❓' };
        const labels: Record<string, string> = {
            heroTitle: 'Título del Hero', heroSubtitle: 'Subtítulo del Hero', heroCtaText: 'Botón principal',
            businessName: 'Nombre del negocio', scheduleText: 'Horario', whatsappNumber: 'WhatsApp',
            adminPassword: '🔑 Contraseña de Admin',
        };
        this.ctx.setContent({ [field]: entities.text });
        this.ctx.logAction('Contenido editado', `${labels[field]} → "${entities.text}"`, 'content');
        return { success: true, message: `✍️ **${labels[field]}** actualizado a: "${entities.text}"`, emoji: '✍️' };
    }

    // ── Layout ──

    private toggleSection(entities: ExtractedEntities, visible: boolean): ActionResult {
        if (!entities.sectionId) return { success: false, message: 'No encontré esa sección. Opciones: hero, destacados, delivery, nosotros, galería, testimonios, contacto.', emoji: '❓' };
        this.ctx.setSectionVisibility(entities.sectionId, visible);
        this.ctx.logAction(visible ? 'Sección mostrada' : 'Sección ocultada', entities.sectionId, 'layout');
        return { success: true, message: visible ? `👁️ Sección **${entities.sectionId}** ahora es **visible**.` : `🙈 Sección **${entities.sectionId}** ahora está **oculta**.`, emoji: visible ? '👁️' : '🙈' };
    }

    private listSections(): ActionResult {
        const sections = this.ctx.config.layout.sections;
        const lines = sections.map(s => `${s.visible ? '👁️' : '🙈'} **${s.id}** (orden: ${s.order})`);
        return { success: true, message: `🧱 **Secciones de la página:**\n${lines.join('\n')}`, emoji: '🧱' };
    }

    private toggleNewsletter(show: boolean): ActionResult {
        this.ctx.setShowNewsletter(show);
        this.ctx.logAction(show ? 'Newsletter activado' : 'Newsletter desactivado', '', 'layout');
        return { success: true, message: show ? '📧 Popup de **Newsletter activado**.' : '🔕 Popup de **Newsletter desactivado**.', emoji: show ? '📧' : '🔕' };
    }

    // ── Banners ──

    private addBanner(entities: ExtractedEntities): ActionResult {
        const text = entities.text || entities.rawText;
        // No cast needed as bannerLink is in ExtractedEntities now
        const link = entities.bannerLink || '#menu';
        this.ctx.addPromotion({ text, link, active: true });
        this.ctx.logAction('Banner agregado', text, 'promo');
        return { success: true, message: `📢 Banner agregado: "${text}" → **${link}**`, emoji: '📢' };
    }

    private removeBanner(): ActionResult {
        this.ctx.removePromotion(0);
        this.ctx.logAction('Banner eliminado', '', 'promo');
        return { success: true, message: '🗑️ Último banner eliminado.', emoji: '🗑️' };
    }

    private listBanners(): ActionResult {
        const promos = this.ctx.config.promotions.filter(p => p.active);
        if (promos.length === 0) return { success: true, message: 'No hay banners activos.', emoji: '📢' };
        const lines = promos.map((p, i) => `${i + 1}. ${p.text}`);
        return { success: true, message: `📢 **${promos.length} banners activos:**\n${lines.join('\n')}`, emoji: '📢' };
    }

    // ── Delivery ──

    private changeZonePrice(entities: ExtractedEntities): ActionResult {
        if (!entities.zone) return { success: false, message: 'No encontré esa zona. ¿Cuál quieres modificar?', emoji: '❓' };
        if (!entities.price) return { success: false, message: 'Necesito el nuevo precio. Ejemplo: "Delivery a Miraflores S/8"', emoji: '❓' };
        this.ctx.updateZone(entities.zone, { price: `S/ ${entities.price.toFixed(2)}` });
        this.ctx.logAction('Delivery actualizado', `${entities.zone} → S/ ${entities.price.toFixed(2)}`, 'delivery');
        return { success: true, message: `🛵 Delivery a **${entities.zone}** actualizado a **S/ ${entities.price.toFixed(2)}**`, emoji: '🛵' };
    }

    private addDeliveryZone(entities: ExtractedEntities): ActionResult {
        if (!entities.zone) return { success: false, message: 'Necesito el nombre de la zona. Ejemplo: "Agrega zona Barranco a S/10"', emoji: '❓' };
        const price = entities.price ? `S/ ${entities.price.toFixed(2)}` : 'Consultar';
        this.ctx.addZone({ name: entities.zone, icon: '🛵', price, desc: 'Envío estándar', color: 'bg-white' });
        this.ctx.logAction('Zona agregada', `${entities.zone} — ${price}`, 'delivery');
        return { success: true, message: `📍 Zona **${entities.zone}** agregada con precio **${price}**`, emoji: '📍' };
    }

    private setFreeDelivery(entities: ExtractedEntities): ActionResult {
        if (!entities.zone) return { success: false, message: 'Necesito la zona. Ejemplo: "Envío gratis a San Borja"', emoji: '❓' };
        this.ctx.updateZone(entities.zone, { price: '🎉 ¡GRATIS!', icon: '📍', color: 'bg-green-50', desc: 'Entrega prioritaria' });
        this.ctx.logAction('Delivery gratis', entities.zone, 'delivery');
        return { success: true, message: `🎉 ¡Delivery **GRATIS** para **${entities.zone}**!`, emoji: '🎉' };
    }

    // ── Testimonials ──

    private addTestimonialAction(entities: ExtractedEntities): ActionResult {
        const name = entities.name || 'Cliente Anónimo';
        const text = entities.text || entities.rawText;
        this.ctx.addTestimonial({ name, text, rating: 5 });
        this.ctx.logAction('Testimonio agregado', `${name}: "${text}"`, 'system');
        return { success: true, message: `⭐ Testimonio de **${name}** agregado.`, emoji: '⭐' };
    }

    // ── Analytics ──

    private getOrders(): Order[] {
        if (typeof window === 'undefined') return [];
        try {
            return JSON.parse(localStorage.getItem('dm_orders') || '[]');
        } catch { return []; }
    }

    private executiveReport(): ActionResult {
        const orders = this.getOrders();
        const financials = adminBrain.calculateFinancials(orders);
        const projection = adminBrain.getMonthlyProjection(financials._rawTotal);
        const avgTicket = adminBrain.getAverageTicket(orders);
        const inventory = adminBrain.analyzeInventory(orders);
        const couponsCount = this.ctx.config.coupons.filter(c => c.active).length;
        const productsCount = this.ctx.config.products.length;

        const now = new Date();
        const dateStr = now.toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' });

        return {
            success: true,
            emoji: '📊',
            message: `📊 **RESUMEN EJECUTIVO** — ${dateStr}\n━━━━━━━━━━━━━━━━━━━━━━━\n💰 Ventas totales: **${financials.grossTotal}**\n💵 Utilidad neta: **${financials.netProfit}**\n🇵🇪 IGV: ${financials.igv}\n🎫 Ticket promedio: ${avgTicket}\n📦 Productos: ${productsCount}\n🏷️ Cupones activos: ${couponsCount}\n📈 Pedidos: ${orders.length}\n🔮 Proyección mes: **${projection.projectedTotal}** ${projection.trend === 'up' ? '📈' : '📊'}\n${inventory.criticalItems.length ? `⚠️ Alta demanda: ${inventory.criticalItems.join(', ')}` : '✅ Stock estable'}\n━━━━━━━━━━━━━━━━━━━━━━━`
        };
    }

    private salesReport(): ActionResult {
        const orders = this.getOrders();
        const financials = adminBrain.calculateFinancials(orders);
        return { success: true, message: `💰 **Ventas:** ${financials.grossTotal}\n💵 **Utilidad:** ${financials.netProfit}\n🧾 **Subtotal:** ${financials.subtotal}\n🇵🇪 **IGV:** ${financials.igv}`, emoji: '💰' };
    }

    private projectionReport(): ActionResult {
        const orders = this.getOrders();
        const financials = adminBrain.calculateFinancials(orders);
        const projection = adminBrain.getMonthlyProjection(financials._rawTotal);
        return { success: true, message: `🔮 **Proyección del mes:** ${projection.projectedTotal}\n📈 Tendencia: ${projection.trend === 'up' ? 'Al alza 🚀' : 'Estable 📊'}`, emoji: '🔮' };
    }

    private topProducts(): ActionResult {
        const orders = this.getOrders();
        const counts: Record<string, number> = {};
        orders.forEach(o => {
            o.items?.forEach(i => { counts[i.title] = (counts[i.title] || 0) + i.quantity; });
        });
        const sorted = Object.entries(counts).sort(([, a], [, b]) => b - a).slice(0, 5);
        if (sorted.length === 0) return { success: true, message: 'Aún no hay datos de ventas para analizar.', emoji: '📊' };
        const lines = sorted.map(([name, count], i) => `${['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i]} **${name}** — ${count} unidades`);
        return { success: true, message: `🏆 **Top productos:**\n${lines.join('\n')}`, emoji: '🏆' };
    }

    private flopProducts(): ActionResult {
        const orders = this.getOrders();
        const counts: Record<string, number> = {};
        this.ctx.config.products.forEach(p => { counts[p.title] = 0; });
        orders.forEach(o => {
            o.items?.forEach(i => { counts[i.title] = (counts[i.title] || 0) + i.quantity; });
        });
        const sorted = Object.entries(counts).sort(([, a], [, b]) => a - b).slice(0, 3);
        const lines = sorted.map(([name, count]) => `📉 **${name}** — ${count} unidades`);
        return { success: true, message: `📉 **Productos con menos ventas:**\n${lines.join('\n')}`, emoji: '📉' };
    }

    private exportCSV(): ActionResult {
        const orders = this.getOrders();
        adminBrain.exportToCSV(orders);
        return { success: true, message: '📁 Reporte CSV generado y descargado.', emoji: '📁' };
    }

    private showHistory(): ActionResult {
        const actions = this.ctx.config.actionLog.slice(0, 10);
        if (actions.length === 0) return { success: true, message: 'No hay acciones registradas aún.', emoji: '📋' };
        const lines = actions.map(a => {
            const date = new Date(a.timestamp).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' });
            return `🕐 ${date} — **${a.action}**: ${a.details}`;
        });
        return { success: true, message: `📋 **Últimas acciones:**\n${lines.join('\n')}`, emoji: '📋' };
    }

    private readFeedback(): ActionResult {
        if (typeof window === 'undefined') return { success: false, message: 'No puedo leer feedback aquí.', emoji: '❌' };
        const feedbacks: Feedback[] = JSON.parse(localStorage.getItem('dm_feedbacks') || '[]');
        if (feedbacks.length === 0) return { success: true, message: '📭 No hay feedback de clientes por ahora.', emoji: '📭' };

        const last3 = feedbacks.slice(-3).reverse();
        const lines = last3.map(f => {
            const stars = '⭐'.repeat(f.rating);
            return `${stars} **${f.product || 'Cliente'}**: "${f.comment || 'Sin comentario'}"`;
        });

        return { success: true, message: `💬 **Últimos ${lines.length} comentarios:**\n${lines.join('\n')}`, emoji: '💬' };
    }

    // ── System ──

    private toggleDateAction(entities: ExtractedEntities, block: boolean): ActionResult {
        if (!entities.date) return { success: false, message: 'Necesito una fecha válida (ej: 2026-12-25 o DD-MM-YYYY).', emoji: '❓' };

        const currentBlocked = this.ctx.config.layout.blockedDates || [];
        const isBlocked = currentBlocked.includes(entities.date);

        if (block && isBlocked) return { success: true, message: `La fecha **${entities.date}** ya estaba bloqueada.`, emoji: '📅' };
        if (!block && !isBlocked) return { success: true, message: `La fecha **${entities.date}** ya estaba libre.`, emoji: '📅' };

        this.ctx.toggleBlockedDate(entities.date);
        this.ctx.logAction(block ? 'Fecha bloqueada' : 'Fecha liberada', entities.date, 'system');

        return {
            success: true,
            message: block
                ? `📅 Fecha **${entities.date}** bloqueada. Los clientes no podrán pedir entregas ese día.`
                : `📅 Fecha **${entities.date}** liberada. Ahora se pueden recibir pedidos nuevamente.`,
            emoji: block ? '🔒' : '🔓'
        };
    }

    private resetEverything(): ActionResult {
        this.ctx.resetAll();
        return { success: true, message: '⚡ ¡Todo restaurado al estado original! La página ha vuelto a nacer.', emoji: '⚡' };
    }

    private suggestImprovements(): ActionResult {
        const suggestions: string[] = [];
        const products = this.ctx.config.products;
        if (products.some(p => p.stock === 'out_of_stock')) suggestions.push('• Hay productos agotados. ¿Quieres reponer stock?');
        if (this.ctx.config.coupons.length === 0) suggestions.push('• No hay cupones activos. Crea uno para impulsar ventas.');
        if (!this.ctx.config.layout.showNewsletter) suggestions.push('• El newsletter está oculto. Actívalo para captar leads.');

        if (suggestions.length === 0) return { success: true, message: '✨ Todo parece estar en orden. ¡Buen trabajo!', emoji: '✨' };
        return { success: true, message: `💡 **Sugerencias de mejora:**\n${suggestions.join('\n')}`, emoji: '💡' };
    }

    private optimizeShop(): ActionResult {
        // 1. Activate all products
        this.ctx.config.products.forEach(p => {
            if (p.stock !== 'available') this.ctx.updateProduct(p.id, { stock: 'available' });
        });

        // 2. Add generic promo if none
        if (this.ctx.config.coupons.length === 0) {
            this.ctx.addCoupon({ code: 'PROMO10', discount: 10, type: 'percent', active: true });
        }

        this.ctx.logAction('Optimización automática', 'Stock restaurado + Cupón creado', 'system');
        return { success: true, message: '🚀 **Tienda Optimizada**:\n• Stock reabastecido al 100%\n• Cupón PROMO10 creado\n• Listo para vender.', emoji: '🚀' };
    }

    private seasonalMode(entities: ExtractedEntities): ActionResult {
        const text = (entities.text || entities.rawText || '').toLowerCase();
        let presetKey = 'original';

        if (text.includes('navidad')) presetKey = 'navidad';
        else if (text.includes('verano') || text.includes('playa')) presetKey = 'tropical';
        else if (text.includes('amor') || text.includes('valentin')) presetKey = 'valentin';
        else if (text.includes('patrio') || text.includes('peru')) presetKey = 'patrio';
        else if (text.includes('noche') || text.includes('lujo')) presetKey = 'midnight';
        else if (text.includes('oceano') || text.includes('mar')) presetKey = 'oceano';
        else if (text.includes('rosa') || text.includes('coquette')) presetKey = 'coquette';

        // Apply theme
        const preset = themePresets[presetKey] || themePresets.original;
        this.ctx.setTheme({ primary: preset.primary, secondary: preset.secondary, accent: preset.accent, paper: preset.paper });

        // Add banner
        this.ctx.addPromotion({ text: `🎉 ¡Modo ${preset.label} Activo! Aprovecha las ofertas.`, link: '#menu', active: true });

        this.ctx.logAction('Modo Estacional', preset.label, 'system');
        return { success: true, message: `🎉 **Modo ${preset.label} activado**\n• Tema visual aplicado\n• Banner promocional creado`, emoji: preset.emoji };
    }

    // ── Customers ──

    private bestCustomer(): ActionResult {
        const orders = this.getOrders();
        if (orders.length === 0) return { success: true, message: 'Aún no hay pedidos para analizar.', emoji: '👥' };

        const spend: Record<string, number> = {};
        orders.forEach(o => {
            const email = o.customer || 'Anonimo';
            spend[email] = (spend[email] || 0) + (o.total || 0);
        });

        const sorted = Object.entries(spend).sort(([, a], [, b]) => b - a);
        const top = sorted[0];

        return { success: true, message: `🏆 **Mejor Cliente:**\n${top[0]} — S/ ${top[1].toFixed(2)} gastados.`, emoji: '🏆' };
    }

    private findCustomer(entities: ExtractedEntities): ActionResult {
        const name = entities.name || entities.text;
        if (!name) return { success: false, message: 'Necesito el nombre del cliente.', emoji: '❓' };

        const orders = this.getOrders();
        const matches = orders.filter(o =>
            (o.customer || '').toLowerCase().includes(name.toLowerCase())
        );

        if (matches.length === 0) return { success: true, message: `No encontré pedidos de "${name}".`, emoji: '🤷' };

        const totalSpent = matches.reduce((sum, o) => sum + (o.total || 0), 0);
        const lastOrder = matches[matches.length - 1];

        return {
            success: true,
            message: `👤 **Cliente encontrado:** ${name}\n📦 Pedidos: ${matches.length}\n💰 Total gastado: S/ ${totalSpent.toFixed(2)}\n📅 Último pedido: ${new Date(lastOrder.date).toLocaleDateString()}`,
            emoji: '👤'
        };
    }
}
