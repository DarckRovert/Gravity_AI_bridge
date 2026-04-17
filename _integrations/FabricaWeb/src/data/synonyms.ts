// ================================================
// 🗣️ SYNONYMS — Mapa de sinónimos del dominio pastelero
// Cada key es el "término canónico" y los values son equivalentes.
// El motor NLP expande cada query con estos sinónimos antes de buscar.
// ================================================

export const SYNONYMS: Record<string, string[]> = {
    // --- Productos ---
    'torta': ['pastel', 'queque', 'bizcocho', 'cake', 'tarta', 'keke', 'keque', 'ponque'],
    'pionono': ['brazo gitano', 'rollo', 'enrollado', 'roll cake', 'brazo de reina'],
    'alfajor': ['alfajores', 'bocadito', 'bocaditos', 'dulcecito', 'galleta rellena'],
    'cupcake': ['cupcakes', 'magdalena', 'muffin', 'muffins', 'ponquecito', 'quequisito'],
    'postre': ['postres', 'dulce', 'dulces', 'golosina', 'reposteria'],
    'chocolate': ['choco', 'cacao', 'chocolatoso'],
    'vainilla': ['vanilla', 'bainilla'],
    'fresa': ['fresas', 'frutilla', 'strawberry'],
    'manjar': ['manjarblanco', 'dulce de leche', 'arequipe', 'cajeta'],
    'combo': ['paquete', 'pack', 'promocion', 'promo', 'oferta', 'bundle'],

    // --- Acciones ---
    'comprar': ['pedir', 'ordenar', 'quiero', 'dame', 'mandame', 'necesito', 'busco', 'deseo'],
    'ver': ['mirar', 'mostrar', 'enseñar', 'muestra', 'muestrame', 'enseñame', 'show'],
    'precio': ['costo', 'valor', 'cuanto', 'cuánto', 'cobra', 'cobran', 'sale', 'costara', 'tarifa', 'rate'],
    'barato': ['economico', 'accesible', 'oferta', 'descuento', 'promocion', 'ganga', 'remate'],
    'caro': ['costoso', 'elevado', 'expensive'],
    'menu': ['carta', 'lista', 'catalogo', 'catálogo', 'productos', 'que tienen', 'que venden'],
    'delivery': ['envio', 'envío', 'reparto', 'llevar', 'domicilio', 'despacho', 'mandar', 'traer'],
    'pagar': ['pago', 'metodo de pago', 'yape', 'plin', 'transferencia', 'efectivo', 'tarjeta'],
    'personalizar': ['custom', 'diseño', 'diseñar', 'a medida', 'personalizado', 'temático', 'tematico'],

    // --- Consultas ---
    'horario': ['hora', 'atienden', 'abierto', 'cerrado', 'abren', 'cierran', 'disponible', 'atencion'],
    'ubicacion': ['donde', 'dónde', 'direccion', 'dirección', 'local', 'tienda', 'taller', 'mapa'],
    'contacto': ['telefono', 'teléfono', 'celular', 'numero', 'número', 'llamar', 'whatsapp', 'escribir'],
    'pedido': ['orden', 'encargo', 'solicitud', 'compra'],
    'rastrear': ['rastreo', 'seguimiento', 'tracking', 'donde esta', 'mi pedido', 'estado'],
    'factura': ['boleta', 'comprobante', 'sunat', 'ruc', 'recibo'],
    'cupon': ['cupón', 'codigo', 'código', 'descuento', 'voucher', 'vale'],
    'ingrediente': ['ingredientes', 'insumo', 'insumos', 'componentes', 'materiales'],
    'alergia': ['alergico', 'alérgico', 'gluten', 'celiaco', 'celíaco', 'intolerante', 'lactosa', 'sin azucar'],
    'vegano': ['vegetariano', 'plant based', 'sin leche', 'sin huevo', 'sin lactosa'],

    // --- Ocasiones ---
    'cumpleaños': ['cumple', 'birthday', 'aniversario'],
    'boda': ['matrimonio', 'casamiento', 'wedding', 'nupcial'],
    'evento': ['reunion', 'celebracion', 'fiesta', 'graduacion'],
    'regalo': ['obsequio', 'presente', 'sorpresa', 'detalle'],

    // --- Conversacional ---
    'hola': ['hi', 'hello', 'hey', 'buenas', 'alo', 'oe', 'oye', 'que tal', 'saludos', 'buen dia', 'buenos dias'],
    'adios': ['chau', 'bye', 'nos vemos', 'hasta luego', 'hasta pronto', 'me voy', 'chaito'],
    'gracias': ['thanks', 'agradezco', 'mil gracias', 'muchas gracias', 'genial', 'perfecto', 'excelente'],
    'ayuda': ['help', 'auxilio', 'no entiendo', 'opciones', 'que puedes hacer', 'como funciona'],
    'si': ['claro', 'dale', 'va', 'ok', 'okey', 'sip', 'por supuesto', 'afirmativo', 'yep', 'ya'],
    'no': ['nop', 'nope', 'nel', 'negativo', 'para nada', 'tampoco'],

    // --- Emociones / Reacciones ---
    'bueno': ['rico', 'delicioso', 'sabroso', 'exquisito', 'divino', 'riquísimo', 'espectacular'],
    'malo': ['feo', 'horrible', 'asqueroso', 'pésimo', 'terrible'],
    'queja': ['reclamo', 'problema', 'mal servicio', 'decepcion', 'insatisfecho'],
    'recomendar': ['recomendacion', 'sugerencia', 'sugerir', 'que me recomiendas', 'popular', 'favorito', 'best seller'],
};

// --- Quick-access reverse lookup (built once at module load) ---
const _reverseMap = new Map<string, string>();
for (const [canonical, syns] of Object.entries(SYNONYMS)) {
    _reverseMap.set(canonical, canonical);
    for (const syn of syns) {
        // Normalize the synonym for lookup
        const norm = syn.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        _reverseMap.set(norm, canonical);
    }
}

/**
 * Given a word, returns the canonical form if it's a known synonym, or the word itself.
 * Example: expandSynonym("pastel") → "torta"
 */
export function getCanonical(word: string): string {
    const norm = word.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    return _reverseMap.get(norm) || word;
}

/**
 * Given a canonical term, return all its synonyms (including itself).
 * Example: getSynonyms("torta") → ["torta", "pastel", "queque", ...]
 */
export function getSynonyms(canonical: string): string[] {
    const syns = SYNONYMS[canonical];
    if (!syns) return [canonical];
    return [canonical, ...syns];
}
