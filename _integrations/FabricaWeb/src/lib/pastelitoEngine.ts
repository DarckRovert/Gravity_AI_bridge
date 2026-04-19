// ⚡ PastelitoEngine — El Cerebro God Mode
// Motor NLP con 60+ intenciones, extracción de entidades, y memoria conversacional

import { themeEngine } from './themeEngine';

// ========================
// 📦 TYPES
// ========================

export interface ExtractedEntities {
    product?: string;
    price?: number;
    color?: string;
    colorHex?: string;
    preset?: string;
    couponCode?: string;
    discount?: number;
    discountType?: 'percent' | 'fixed';
    zone?: string;
    sectionId?: string;
    text?: string;
    period?: 'today' | 'week' | 'month' | 'all';
    name?: string;
    rating?: number;
    category?: string;
    bannerLink?: string;
    image?: string;
    date?: string; // YYYY-MM-DD
    rawText: string;
}

export interface ParseResult {
    intent: string;
    entities: ExtractedEntities;
    confidence: number;
    requiresConfirmation: boolean;
    riskLevel: 'none' | 'low' | 'medium' | 'high' | 'critical';
}

interface IntentPattern {
    name: string;
    patterns: string[];
    requiresAdmin: boolean;
    riskLevel: 'none' | 'low' | 'medium' | 'high' | 'critical';
    entityExtractors?: string[]; // Which entities to try to extract
}

export interface PendingAction {
    intent: string;
    entities: ExtractedEntities;
    description: string;
    riskLevel: string;
}

export interface ConversationMemory {
    lastIntent: string | null;
    pendingAction: PendingAction | null;
    context: Record<string, string>;
    // 🧠 Intelligence upgrade — contextual memory
    lastProduct: string | null;
    lastCategory: string | null;
    lastAction: string | null;
    conversationHistory: { role: 'user' | 'bot'; text: string; timestamp: number }[];
}

// ========================
// 🧠 INTENT DEFINITIONS
// ========================

const adminIntents: IntentPattern[] = [
    // 🛒 Productos
    { name: 'cambiar_precio', patterns: ['sube precio', 'baja precio', 'cambia precio', 'cambiar precio', 'nuevo precio', 'pon precio', 'precio a', 'precio del', 'ponle precio', 'a s/', 'a s/.', 'soles'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['product', 'price'] },
    { name: 'agotar_stock', patterns: ['agota', 'sin stock', 'agotar', 'no hay', 'ya no hay', 'se acabo', 'se acabó', 'fuera de stock', 'no disponible'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['product'] },
    { name: 'reponer_stock', patterns: ['reponer', 'repón', 'repon', 'hay stock', 'disponible', 'volvio', 'volvió', 'ya hay', 'reabastecer'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['product'] },
    { name: 'stock_bajo', patterns: ['pocas unidades', 'stock bajo', 'ultimas unidades', 'últimas unidades', 'poco stock', 'se estan acabando', 'se están acabando'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['product'] },
    { name: 'destacar', patterns: ['destaca', 'destacar', 'pon en destacados', 'destacado', 'featured', 'resaltar', 'portada'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['product'] },
    { name: 'quitar_destacado', patterns: ['quita de destacados', 'quitar de destacados', 'quitar destacado', 'ya no destacar', 'no destacar', 'quita destacado'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['product'] },
    { name: 'agregar_producto', patterns: ['agrega producto', 'agregar producto', 'nuevo producto', 'crear producto', 'añadir producto', 'añade producto', 'agrega el', 'agrega la', 'agrega un', 'agrega una', 'añade el', 'añade la', 'sube esta imagen', 'pon esta foto', 'agrega esto a', 'ponla en', 'ponlo en', 'agregar a bocaditos', 'agregar a tortas', 'agregar a piononos', 'agregar a combos', 'agrega a bocaditos', 'agrega a tortas', 'agrega a piononos', 'agrega a combos', 'mete en', 'pon en bocaditos', 'pon en tortas', 'pon en piononos', 'pon en combos'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['product', 'price', 'category'] },
    { name: 'eliminar_producto', patterns: ['elimina producto', 'eliminar producto', 'borra producto', 'borrar producto', 'quita producto', 'quitar producto', 'elimina el', 'borra el'], requiresAdmin: true, riskLevel: 'high', entityExtractors: ['product'] },
    { name: 'cambiar_descripcion', patterns: ['cambia descripcion', 'cambiar descripción', 'nueva descripcion', 'descripcion del', 'pon descripcion'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['product', 'text'] },
    { name: 'listar_productos', patterns: ['que productos', 'qué productos', 'lista productos', 'listar productos', 'cuantos productos', 'cuántos productos', 'mis productos', 'ver productos', 'todos los productos'], requiresAdmin: true, riskLevel: 'none' },

    // 🏷️ Cupones
    { name: 'crear_cupon', patterns: ['crea cupon', 'crear cupón', 'nuevo cupon', 'nuevo cupón', 'agrega cupon', 'agregar cupón', 'cupon de', 'cupón de'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['couponCode', 'discount'] },
    { name: 'eliminar_cupon', patterns: ['elimina cupon', 'eliminar cupón', 'borra cupon', 'borrar cupón', 'desactiva cupon', 'desactivar cupón', 'quita cupon', 'quitar cupón'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['couponCode'] },
    { name: 'listar_cupones', patterns: ['que cupones', 'qué cupones', 'lista cupones', 'listar cupones', 'cupones activos', 'ver cupones', 'cuantos cupones'], requiresAdmin: true, riskLevel: 'none' },

    // 🎨 Visual
    { name: 'tema_preset', patterns: ['tema', 'ponle tema', 'modo', 'estilo', 'cambia tema', 'cambiar tema', 'activa tema', 'diseño', 'apariencia', 'look'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['preset'] },
    { name: 'cambiar_color', patterns: ['color principal', 'cambia color', 'cambiar color', 'color primario', 'pon color'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['color'] },
    { name: 'cambiar_secundario', patterns: ['color secundario', 'secundario a', 'cambia el dorado', 'cambia el secundario'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['color'] },
    { name: 'cambiar_fondo', patterns: ['fondo', 'background', 'color de fondo', 'cambia fondo'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['color'] },
    { name: 'toggle_dark', patterns: ['dark mode', 'modo oscuro', 'modo claro', 'activa dark', 'desactiva dark', 'oscuro', 'noche'], requiresAdmin: true, riskLevel: 'low' },
    { name: 'restaurar_tema', patterns: ['restaura tema', 'restaurar tema', 'tema original', 'colores originales', 'resetea tema', 'resetear tema', 'vuelve al original', 'diseño original'], requiresAdmin: true, riskLevel: 'medium' },
    { name: 'ver_tema', patterns: ['que tema', 'qué tema', 'tema actual', 'colores actuales', 'que colores', 'qué colores'], requiresAdmin: true, riskLevel: 'none' },

    // 📝 Contenido
    { name: 'cambiar_hero_titulo', patterns: ['cambia titulo', 'cambiar título', 'titulo a', 'título a', 'titulo del hero', 'cambia el titulo', 'nuevo titulo', 'pon de titulo'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['text'] },
    { name: 'cambiar_hero_sub', patterns: ['cambia subtitulo', 'cambiar subtítulo', 'subtitulo a', 'subtítulo a', 'nuevo subtitulo', 'pon de subtitulo'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['text'] },
    { name: 'cambiar_hero_cta', patterns: ['boton principal', 'botón principal', 'texto del boton', 'cambia el boton', 'cta', 'call to action', 'boton a'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['text'] },
    { name: 'cambiar_nombre', patterns: ['cambia nombre', 'cambiar nombre', 'renombra', 'renombrar', 'nuevo nombre', 'nombre a', 'nombre de la pasteleria', 'nombre del negocio'], requiresAdmin: true, riskLevel: 'high', entityExtractors: ['text'] },
    { name: 'cambiar_horario', patterns: ['cambia horario', 'cambiar horario', 'nuevo horario', 'horario a', 'atiende de', 'abre a', 'cierra a'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['text'] },
    { name: 'cambiar_whatsapp', patterns: ['cambia whatsapp', 'cambiar whatsapp', 'nuevo whatsapp', 'numero de whatsapp', 'nuevo numero', 'telefono a', 'celular a'], requiresAdmin: true, riskLevel: 'high', entityExtractors: ['text'] },

    // 🧱 Layout
    { name: 'ocultar_seccion', patterns: ['oculta seccion', 'ocultar sección', 'esconde seccion', 'esconder sección', 'quita seccion', 'desactiva seccion'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['sectionId'] },
    { name: 'mostrar_seccion', patterns: ['muestra seccion', 'mostrar sección', 'activa seccion', 'activar sección', 'pon seccion'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['sectionId'] },
    { name: 'listar_secciones', patterns: ['que secciones', 'qué secciones', 'lista secciones', 'secciones de la pagina', 'ver secciones'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'ocultar_newsletter', patterns: ['desactiva newsletter', 'oculta newsletter', 'quita newsletter', 'desactiva popup', 'quita popup', 'no newsletter', 'no popup'], requiresAdmin: true, riskLevel: 'low' },
    { name: 'mostrar_newsletter', patterns: ['activa newsletter', 'muestra newsletter', 'pon newsletter', 'activa popup'], requiresAdmin: true, riskLevel: 'low' },

    // 📢 Banners
    { name: 'agregar_banner', patterns: ['agrega banner', 'agregar banner', 'nuevo banner', 'crea banner', 'pon banner', 'añade banner'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['text'] },
    { name: 'quitar_banner', patterns: ['quita banner', 'quitar banner', 'elimina banner', 'borra banner'], requiresAdmin: true, riskLevel: 'low' },
    { name: 'listar_banners', patterns: ['que banners', 'qué banners', 'ver banners', 'lista banners', 'banners activos'], requiresAdmin: true, riskLevel: 'none' },

    // 🛵 Delivery
    { name: 'cambiar_precio_zona', patterns: ['delivery a', 'envio a', 'envío a', 'precio delivery', 'cambia delivery', 'cambia envio'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['zone', 'price'] },
    { name: 'agregar_zona', patterns: ['agrega zona', 'agregar zona', 'nueva zona', 'añade zona'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['zone', 'price'] },
    { name: 'delivery_gratis', patterns: ['delivery gratis', 'envio gratis', 'envío gratis', 'gratis a'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['zone'] },

    //  Testimonios
    { name: 'agregar_testimonio', patterns: ['agrega testimonio', 'agregar testimonio', 'nuevo testimonio', 'añade testimonio'], requiresAdmin: true, riskLevel: 'low', entityExtractors: ['name', 'text'] },

    // 📊 Análisis
    { name: 'resumen_ejecutivo', patterns: ['resumen ejecutivo', 'resumen del dia', 'resumen del día', 'como vamos', 'cómo vamos', 'dame el resumen', 'reporte', 'informe', 'status', 'estado'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'ver_ventas', patterns: ['ventas', 'cuanto vendi', 'cuánto vendí', 'ingresos', 'dinero', 'facturacion', 'facturación', 'cuánto llevo', 'cuanto llevo'], requiresAdmin: true, riskLevel: 'none', entityExtractors: ['period'] },
    { name: 'ver_feedback', patterns: ['feedback', 'que dicen', 'qué dicen', 'opiniones', 'comentarios', 'quejas', 'reseñas', 'leer feedback'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'proyeccion', patterns: ['proyeccion', 'proyección', 'como cerramos', 'cómo cerramos', 'meta del mes', 'cerrar el mes', 'forecast'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'producto_top', patterns: ['mas vendido', 'más vendido', 'top producto', 'producto estrella', 'que se vende mas', 'qué se vende más', 'best seller', 'bestseller'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'producto_flop', patterns: ['no se vende', 'menos vendido', 'que no se vende', 'qué no se vende', 'peor producto', 'no vende'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'exportar_csv', patterns: ['exporta', 'exportar', 'descargar', 'excel', 'csv', 'descarga reporte', 'bajar datos'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'historial_cambios', patterns: ['historial', 'que cambios', 'qué cambios', 'log', 'registro de cambios', 'que hice', 'qué hice'], requiresAdmin: true, riskLevel: 'none' },

    // 📊 Analytics v2.0
    { name: 'comparacion_semanal', patterns: ['semana pasada', 'comparado con', 'comparacion semanal', 'comparación semanal', 'esta semana vs', 'versus semana', 'como van las ventas', 'cómo van las ventas'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'hora_pico', patterns: ['hora pico', 'hora fuerte', 'mejor hora', 'cuando vendo mas', 'cuándo vendo más', 'a que hora', 'a qué hora'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'mejor_dia', patterns: ['mejor dia', 'mejor día', 'que dia vendo mas', 'qué día vendo más', 'dia fuerte', 'día fuerte', 'mejor dia de la semana'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'limpiar_chat', patterns: ['limpia chat', 'limpiar chat', 'borra conversacion', 'borrar conversación', 'limpiar historial', 'borrar historial', 'limpia conversacion'], requiresAdmin: false, riskLevel: 'none' },

    // 👥 Clientes
    { name: 'mejor_cliente', patterns: ['mejor cliente', 'top cliente', 'mejores clientes', 'clientes vip', 'quien compra mas', 'quién compra más'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'buscar_cliente', patterns: ['busca cliente', 'buscar cliente', 'info de', 'datos de', 'quien es', 'quién es'], requiresAdmin: true, riskLevel: 'none', entityExtractors: ['name'] },

    // 🤖 AutoPilot
    { name: 'optimizar_todo', patterns: ['optimiza', 'optimizar', 'optimiza la tienda', 'mejora todo', 'hazlo mejor'], requiresAdmin: true, riskLevel: 'medium' },
    { name: 'sugerir_mejoras', patterns: ['que mejoro', 'qué mejoro', 'sugerencias', 'que deberia', 'qué debería', 'recomienda', 'que harías', 'qué harías'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'modo_estacional', patterns: ['prepara para', 'arma para', 'preparar para', 'armar para', 'campaña', 'prepara todo'], requiresAdmin: true, riskLevel: 'medium' },

    // Reset
    { name: 'resetear_todo', patterns: ['resetea todo', 'resetear todo', 'restaurar todo', 'volver al inicio', 'restablecer'], requiresAdmin: true, riskLevel: 'critical' },

    // 📅 Disponibilidad
    { name: 'bloquear_fecha', patterns: ['bloquear fecha', 'bloquea fecha', 'bloquea el', 'cierra el', 'cerrar el', 'no atenderemos el', 'marca como lleno', 'sin capacidad el'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['date'] },
    { name: 'desbloquear_fecha', patterns: ['desbloquear fecha', 'desbloquea fecha', 'desbloquea el', 'abre el', 'abrir el', 'ya podemos atender el', 'quita el bloqueo', 'libera el'], requiresAdmin: true, riskLevel: 'medium', entityExtractors: ['date'] },

    // 🧙 Wizards (Multi-Turn)
    { name: 'wizard_producto', patterns: ['agregar producto paso a paso', 'wizard producto', 'nuevo producto paso a paso', 'guiame para agregar', 'guíame para agregar', 'crear producto nuevo'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'wizard_cupon', patterns: ['crear cupon paso a paso', 'wizard cupon', 'wizard cupón', 'nuevo cupon paso a paso', 'guiame cupon', 'guíame cupón'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'wizard_zona', patterns: ['agregar zona paso a paso', 'wizard zona', 'nueva zona paso a paso', 'guiame zona', 'guíame zona'], requiresAdmin: true, riskLevel: 'none' },
    { name: 'wizard_banner', patterns: ['crear banner paso a paso', 'wizard banner', 'nuevo banner paso a paso', 'guiame banner', 'guíame banner'], requiresAdmin: true, riskLevel: 'none' },

    // 🔒 Seguridad
    { name: 'cambiar_password', patterns: ['cambiar contraseña', 'cambia la clave', 'nueva contraseña', 'cambiar password', 'actualiza el acceso'], requiresAdmin: true, riskLevel: 'critical', entityExtractors: ['text'] },
];

const customerIntents: IntentPattern[] = [
    { name: 'saludar', patterns: ['hola', 'buenos', 'buenas', 'hi', 'alo', 'hey', 'que tal', 'qué tal'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'despedir', patterns: ['adios', 'adiós', 'chau', 'bye', 'gracias', 'hasta luego', 'nos vemos'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'ver_menu', patterns: ['carta', 'menu', 'menú', 'lista', 'catalogo', 'catálogo', 'productos', 'que tienen', 'qué tienen'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'preguntar_precio', patterns: ['precio', 'costo', 'cuanto', 'cuánto', 'vale', 'cotizar', 'cuanto cuesta', 'cuánto cuesta'], requiresAdmin: false, riskLevel: 'none', entityExtractors: ['product'] },
    { name: 'hacer_pedido', patterns: ['comprar', 'pedir', 'quiero', 'ordenar', 'deseo', 'antojo', 'quiero pedir', 'como compro', 'cómo compro'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'preguntar_horario', patterns: ['horario', 'hora', 'atienden', 'abierto', 'cerrado', 'a que hora', 'a qué hora'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'preguntar_delivery', patterns: ['delivery', 'envio', 'envío', 'llevan', 'traen', 'reparto', 'distrito', 'cobertura', 'llegan a'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'contactar', patterns: ['telefono', 'teléfono', 'celular', 'whatsapp', 'llamar', 'contacto', 'contactar'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'rastrear', patterns: ['rastrear', 'pedido', 'donde esta', 'dónde está', 'estado', 'seguimiento', 'tracking'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'recomendar', patterns: ['recomienda', 'recomiéndame', 'que me recomiendas', 'qué me recomiendas', 'sugiere', 'sugiéreme', 'el mejor'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'personalizar_torta', patterns: ['personalizar', 'personalizada', 'diseñar', 'diseña', 'crea tu torta', 'mi torta', 'a mi gusto'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'ubicacion', patterns: ['ubicacion', 'ubicación', 'donde estan', 'dónde están', 'donde queda', 'dónde queda', 'direccion', 'dirección', 'local', 'taller'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'metodo_pago', patterns: ['yape', 'plin', 'tarjeta', 'efectivo', 'pago', 'como pago', 'cómo pago', 'metodo de pago', 'método de pago'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'reclamo', patterns: ['reclamo', 'queja', 'problema', 'mal', 'error', 'defectuoso', 'no llego', 'no llegó'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'para_evento', patterns: ['cumpleaños', 'cumpleanos', 'boda', 'aniversario', 'evento', 'celebracion', 'celebración', 'fiesta', 'graduacion'], requiresAdmin: false, riskLevel: 'none' },

    // Easter eggs
    { name: 'easter_inteligente', patterns: ['eres inteligente', 'que tan inteligente', 'qué tan inteligente'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'easter_love', patterns: ['te quiero', 'te amo', 'te adoro'], requiresAdmin: false, riskLevel: 'none' },
    { name: 'easter_about', patterns: ['quien eres', 'quién eres', 'hablame de ti', 'háblame de ti', 'que eres', 'qué eres'], requiresAdmin: false, riskLevel: 'none' },
];

// Section name aliases
const sectionAliases: Record<string, string> = {
    'hero': 'hero', 'banner': 'hero', 'portada': 'hero', 'principal': 'hero',
    'featured': 'featured', 'destacados': 'featured', 'especialidades': 'featured',
    'delivery': 'delivery', 'envio': 'delivery', 'envío': 'delivery', 'zonas': 'delivery', 'reparto': 'delivery',
    'nosotros': 'nosotros', 'historia': 'nosotros', 'about': 'nosotros', 'sobre nosotros': 'nosotros',
    'gallery': 'gallery', 'galeria': 'gallery', 'galería': 'gallery', 'instagram': 'gallery', 'fotos': 'gallery',
    'testimonials': 'testimonials', 'testimonios': 'testimonials', 'opiniones': 'testimonials', 'reseñas': 'testimonials',
    'contact': 'contact', 'contacto': 'contact', 'info': 'contact', 'informacion': 'contact',
};

// ========================
// 🧠 ENGINE CLASS
// ========================

export class PastelitoEngine {
    private memory: ConversationMemory = {
        lastIntent: null,
        pendingAction: null,
        context: {},
        lastProduct: null,
        lastCategory: null,
        lastAction: null,
        conversationHistory: [],
    };

    /**
     * Normalize text — remove accents, lowercase, trim extra whitespace
     */
    normalize(text: string): string {
        return text
            .toLowerCase()
            .trim()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
            .replace(/\s+/g, ' ');
    }

    /**
     * Parse user input, detect intent and extract entities
     */
    parse(text: string, isAdmin: boolean): ParseResult {
        const normalized = this.normalize(text);

        // Check for confirmation/denial if there's a pending action
        if (this.memory.pendingAction) {
            if (/^(si|sí|ok|dale|confirmo|confirmar|hazlo|claro|por supuesto|yes|listo|adelante)$/i.test(normalized.trim())) {
                const pending = this.memory.pendingAction;
                this.memory.pendingAction = null;
                return {
                    intent: 'confirm_action',
                    entities: { ...pending.entities, rawText: text },
                    confidence: 1.0,
                    requiresConfirmation: false,
                    riskLevel: 'none',
                };
            }
            if (/^(no|cancelar|cancela|nel|nah|nop|mejor no|dejalo|déjalo)$/i.test(normalized.trim())) {
                this.memory.pendingAction = null;
                return {
                    intent: 'cancel_action',
                    entities: { rawText: text },
                    confidence: 1.0,
                    requiresConfirmation: false,
                    riskLevel: 'none',
                };
            }
        }

        // Search through intents
        const allIntents = isAdmin ? [...adminIntents, ...customerIntents] : customerIntents;
        let bestMatch: { intent: IntentPattern; score: number } | null = null;

        for (const intent of allIntents) {
            for (const pattern of intent.patterns) {
                const patternNorm = this.normalize(pattern);
                if (normalized.includes(patternNorm)) {
                    const score = patternNorm.length / normalized.length;
                    if (!bestMatch || score > bestMatch.score) {
                        bestMatch = { intent, score };
                    }
                }
            }
        }

        if (!bestMatch) {
            return {
                intent: 'unknown',
                entities: { rawText: text },
                confidence: 0,
                requiresConfirmation: false,
                riskLevel: 'none',
            };
        }

        // Extract entities
        const entities = this.extractEntities(normalized, bestMatch.intent, text);
        const needsConfirmation = bestMatch.intent.riskLevel !== 'none';

        // 🧠 Pronoun resolution — fill in missing product from context
        if (!entities.product && bestMatch.intent.entityExtractors?.includes('product')) {
            if (this.memory.lastProduct) {
                entities.product = this.memory.lastProduct;
            }
        }

        // 🧠 Auto-context tracking — remember what was mentioned
        if (entities.product) {
            this.memory.lastProduct = entities.product;
        }
        if (entities.category) {
            this.memory.lastCategory = entities.category;
        }
        this.memory.lastIntent = bestMatch.intent.name;
        this.memory.lastAction = bestMatch.intent.name;

        // 🧠 Conversation history — keep last 5 turns
        this.addToHistory('user', text);

        return {
            intent: bestMatch.intent.name,
            entities,
            confidence: Math.min(bestMatch.score + 0.3, 1.0),
            requiresConfirmation: needsConfirmation,
            riskLevel: bestMatch.intent.riskLevel,
        };
    }

    /**
     * Extract entities from text based on what the intent expects
     */
    private extractEntities(normalized: string, intent: IntentPattern, rawText: string): ExtractedEntities {
        const entities: ExtractedEntities = { rawText };
        const extractors = intent.entityExtractors || [];

        if (extractors.includes('price')) {
            // Match S/XX, S/.XX, XX soles, or plain number after "a" 
            const priceMatch = normalized.match(/s\/\.?\s*(\d+(?:\.\d{1,2})?)|(\d+(?:\.\d{1,2})?)\s*soles?|(?:a\s+)(\d+(?:\.\d{1,2})?)/);
            if (priceMatch) {
                entities.price = parseFloat(priceMatch[1] || priceMatch[2] || priceMatch[3]);
            }
        }

        if (extractors.includes('product')) {
            // Try to extract product name — everything that's not a number/keyword
            const cleaned = normalized
                .replace(/s\/\.?\s*\d+(?:\.\d{1,2})?/g, '')
                .replace(/\d+\s*soles?/g, '')
                .replace(/a\s+\d+/g, '');

            // Remove intent patterns from the text to isolate the product name
            let productName = cleaned;
            for (const pattern of intent.patterns) {
                productName = productName.replace(this.normalize(pattern), '');
            }
            // Remove stop words and category keywords so they don't become the product name
            productName = productName.replace(/\b(el|la|los|las|del|de|al|un|una|en|a)\b/g, '').trim();
            // Strip category names from product name to avoid 'bocaditos' becoming the product
            const categoryKeywords = ['bocaditos', 'piononos', 'tortas', 'combos', 'postres', 'pastel', 'pasteles'];
            for (const cat of categoryKeywords) {
                productName = productName.replace(new RegExp(`\\b${cat}\\b`, 'gi'), '').trim();
            }
            if (productName.length > 1) {
                entities.product = productName;
            }
        }

        if (extractors.includes('color')) {
            // Try color extraction from text
            const colorWords = Object.keys(themeEngine.parseColor('') ? {} : {});
            // Use themeEngine to parse
            const words = normalized.split(' ');
            for (let i = words.length - 1; i >= 0; i--) {
                // Try 2-word combinations first (e.g., "azul marino")
                if (i > 0) {
                    const twoWord = `${words[i - 1]} ${words[i]}`;
                    const hex = themeEngine.parseColor(twoWord);
                    if (hex) {
                        entities.color = twoWord;
                        entities.colorHex = hex;
                        break;
                    }
                }
                const hex = themeEngine.parseColor(words[i]);
                if (hex) {
                    entities.color = words[i];
                    entities.colorHex = hex;
                    break;
                }
            }
        }

        if (extractors.includes('preset')) {
            const preset = themeEngine.findPreset(normalized);
            if (preset) {
                entities.preset = preset.name;
            }
        }

        if (extractors.includes('couponCode')) {
            // Match uppercase code patterns
            const codeMatch = rawText.match(/\b([A-Z][A-Z0-9_]{2,15})\b/);
            if (codeMatch) {
                entities.couponCode = codeMatch[1];
            }
        }

        if (extractors.includes('discount')) {
            const discountMatch = normalized.match(/(\d+)\s*(%|por ?ciento|porciento)/);
            if (discountMatch) {
                entities.discount = parseInt(discountMatch[1]);
                entities.discountType = 'percent';
            } else {
                const fixedMatch = normalized.match(/s\/\.?\s*(\d+(?:\.\d{1,2})?)\s*(?:de descuento|off|menos)/);
                if (fixedMatch) {
                    entities.discount = parseFloat(fixedMatch[1]);
                    entities.discountType = 'fixed';
                }
            }
        }

        if (extractors.includes('zone')) {
            // Try to find zone name in the text
            const zoneNames = ['surco', 'san borja', 'miraflores', 'san isidro', 'la molina', 'barranco', 'chorrillos',
                'san miguel', 'jesus maria', 'lince', 'magdalena', 'pueblo libre', 'breña', 'lima'];
            for (const zone of zoneNames) {
                if (normalized.includes(zone)) {
                    entities.zone = zone.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    break;
                }
            }
        }

        if (extractors.includes('sectionId')) {
            for (const [alias, id] of Object.entries(sectionAliases)) {
                if (normalized.includes(this.normalize(alias))) {
                    entities.sectionId = id;
                    break;
                }
            }
        }

        if (extractors.includes('text')) {
            // Extract text after common prepositions: "a", ":", "que diga"
            const textMatch = rawText.match(/(?:a |que diga |pon |: )["']?(.+?)["']?\s*$/i);
            if (textMatch) {
                entities.text = textMatch[1].trim();
            }
        }

        if (extractors.includes('category')) {
            // Mapeo de categorías conocidas del menú
            const categoryMap: Record<string, string> = {
                'bocaditos': 'bocaditos', 'bocadito': 'bocaditos', 'snacks': 'bocaditos',
                'piononos': 'piononos', 'pionono': 'piononos',
                'tortas': 'tortas', 'torta': 'tortas', 'pastel': 'tortas', 'pasteles': 'tortas', 'cake': 'tortas',
                'combos': 'combos', 'combo': 'combos', 'paquete': 'combos', 'pack': 'combos',
                'postres': 'bocaditos', 'postre': 'bocaditos',
                'chocotejas': 'bocaditos', 'chocoteja': 'bocaditos',
                'alfajores': 'bocaditos', 'alfajor': 'bocaditos',
                'brownies': 'bocaditos', 'brownie': 'bocaditos',
                'galletas': 'bocaditos', 'galleta': 'bocaditos', 'cookies': 'bocaditos',
                'cupcakes': 'bocaditos', 'cupcake': 'bocaditos',
                'empanadas': 'bocaditos', 'empanada': 'bocaditos',
            };
            for (const [keyword, category] of Object.entries(categoryMap)) {
                if (normalized.includes(keyword)) {
                    entities.category = category;
                    break;
                }
            }
        }

        if (extractors.includes('period')) {
            if (normalized.includes('hoy') || normalized.includes('dia') || normalized.includes('día')) entities.period = 'today';
            else if (normalized.includes('semana')) entities.period = 'week';
            else if (normalized.includes('mes')) entities.period = 'month';
            else entities.period = 'all';
        }

        if (extractors.includes('name')) {
            // Try to extract a name after "de" or at the end
            const nameMatch = rawText.match(/(?:de\s+|a\s+|que\s+)([A-Z][a-záéíóú]+(?:\s+[A-Z][a-záéíóú]+)*)/);
            if (nameMatch) {
                entities.name = nameMatch[1];
            }
        }

        if (extractors.includes('date')) {
            // Regex for YYYY-MM-DD or DD-MM-YYYY or DD/MM/YYYY
            const dateMatch = rawText.match(/\b(\d{2,4}[-/]\d{2}[-/]\d{2,4})\b/);
            if (dateMatch) {
                let d = dateMatch[1].replace(/\//g, '-');
                const parts = d.split('-');
                if (parts[0].length === 2 && parts[2].length === 4) {
                    // Turn DD-MM-YYYY into YYYY-MM-DD
                    d = `${parts[2]}-${parts[1]}-${parts[0]}`;
                }
                entities.date = d;
            } else {
                // Try today/tomorrow
                if (normalized.includes('mañana')) {
                    const t = new Date(); t.setDate(t.getDate() + 1);
                    entities.date = t.toISOString().split('T')[0];
                } else if (normalized.includes('hoy')) {
                    entities.date = new Date().toISOString().split('T')[0];
                }
            }
        }

        return entities;
    }

    /**
     * Set a pending action requiring confirmation
     */
    setPending(intent: string, entities: ExtractedEntities, description: string, riskLevel: string): void {
        this.memory.pendingAction = { intent, entities, description, riskLevel };
    }

    /**
     * Get pending action (if any)
     */
    getPending(): PendingAction | null {
        return this.memory.pendingAction;
    }

    /**
     * Clear pending action
     */
    clearPending(): void {
        this.memory.pendingAction = null;
    }

    /**
     * Remember a context variable
     */
    remember(key: string, value: string): void {
        this.memory.context[key] = value;
    }

    /**
     * Recall a context variable
     */
    recall(key: string): string | undefined {
        return this.memory.context[key];
    }

    /**
     * Get fuzzy suggestions for unknown input
     */
    getSuggestions(text: string, isAdmin: boolean): string[] {
        const normalized = this.normalize(text);
        const allIntents = isAdmin ? [...adminIntents, ...customerIntents] : customerIntents;
        const suggestions: { name: string; score: number }[] = [];

        for (const intent of allIntents) {
            for (const pattern of intent.patterns) {
                const patternNorm = this.normalize(pattern);
                // Simple character overlap score
                let overlap = 0;
                for (const word of normalized.split(' ')) {
                    if (patternNorm.includes(word) && word.length > 2) overlap += word.length;
                }
                if (overlap > 0) {
                    suggestions.push({ name: intent.name, score: overlap });
                }
            }
        }

        return [...new Set(suggestions.sort((a, b) => b.score - a.score).slice(0, 3).map(s => s.name))];
    }

    /**
     * 🧠 Add a message to conversation history (keeps last 5 turns)
     */
    addToHistory(role: 'user' | 'bot', text: string): void {
        this.memory.conversationHistory.push({ role, text, timestamp: Date.now() });
        if (this.memory.conversationHistory.length > 10) {
            this.memory.conversationHistory = this.memory.conversationHistory.slice(-10);
        }
    }

    /**
     * 🧠 Get last mentioned product (for pronoun resolution)
     */
    getLastProduct(): string | null {
        return this.memory.lastProduct;
    }

    /**
     * 🧠 Get last mentioned category
     */
    getLastCategory(): string | null {
        return this.memory.lastCategory;
    }

    /**
     * 🧠 Get conversation history for LLM context
     */
    getHistory(): Array<{ role: 'user' | 'bot'; text: string }> {
        return this.memory.conversationHistory.map(h => ({ role: h.role, text: h.text }));
    }

    /**
     * 🧠 Get full context snapshot
     */
    getContext(): { lastProduct: string | null; lastCategory: string | null; lastAction: string | null; historyLength: number } {
        return {
            lastProduct: this.memory.lastProduct,
            lastCategory: this.memory.lastCategory,
            lastAction: this.memory.lastAction,
            historyLength: this.memory.conversationHistory.length,
        };
    }
}

export const pastelitoEngine = new PastelitoEngine();
