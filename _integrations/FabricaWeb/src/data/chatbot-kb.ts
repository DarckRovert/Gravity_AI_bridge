
export interface KBItem {
    keys: string[];
    response?: string | string[];
    action?: string;
    options?: { text: string; next?: string; action?: string }[];
}

export interface FlowNode {
    text: string;
    options?: { text: string; next?: string; action?: string }[];
    action?: string;
}

// ========================
// 🧁 CUSTOMER KNOWLEDGE BASE (40+ entries)
// ========================

export const customerKB: KBItem[] = [
    // --- Saludos y despedidas ---
    { keys: ['hola', 'buenos', 'buenas', 'hi', 'alo', 'hey', 'buen dia', 'saludos', 'buenas tardes', 'buenas noches', 'oe', 'oye'], response: ["¡Hola! 👋 Soy Antojín. ¿En qué te ayudo?", "¡Hola! Qué gusto verte por aquí. 🍍", "¡Buenos días! Hoy es un buen día para algo delicioso. 🥤", "¡Hey! 👋 Bienvenido a Antojitos Express. ¿Qué te provoca hoy?"] },
    { keys: ['adios', 'chau', 'bye', 'hasta luego', 'nos vemos', 'me voy', 'chaito', 'hasta pronto', 'ciao', 'chao'], response: ["¡Hasta pronto! Endulza tu día. 🍭", "¡Chau! Aquí estaré si se te antoja algo. 🧁", "¡Nos vemos! Fue un placer atenderte. 💛"] },
    { keys: ['como estas', 'como andas', 'que tal', 'como va', 'como te va', 'todo bien', 'que onda', 'que hay', 'que pasa', 'novedad'], response: ["¡Muy bien, gracias por preguntar! 😊 ¿Te antoja algo dulce hoy?", "¡De maravilla! 🧁 Aquí listo para ayudarte. ¿Qué se te ofrece?", "¡Genial! Siempre de buen humor cuando hay postres de por medio. 🍰 ¿En qué te ayudo?", "¡Feliz como un cupcake recién horneado! 🧁 ¿En qué te ayudo?"] },
    { keys: ['que haces', 'que sabes hacer', 'para que sirves', 'que puedes hacer', 'ayuda', 'help', 'opciones', 'capacidades', 'funciones', 'que ofreces', 'menu de opciones'], response: "¡Puedo ayudarte con muchas cosas! 🧁\n• 📜 Ver nuestra **carta de productos**\n• 💰 Consultar **precios**\n• 🛵 Info sobre **delivery**\n• 🎂 **Recomendaciones** para tu evento\n• 📦 **Rastrear** tu pedido\n• 🎨 **Diseñar** tu torta personalizada\n\n¿Qué te interesa?" },

    // --- Navegación principal ---
    { keys: ['carta', 'menu', 'lista', 'catalogo', 'productos', 'que tienen', 'que venden', 'que ofrecen', 'que hay', 'que tienen disponible', 'ver todo', 'mostrar todo', 'que postres', 'variedad', 'surtido'], response: "📜 ¡Te llevo a nuestra carta! Ahí puedes ver todos nuestros productos y agregarlos al carrito. 🛒", action: "menu" },
    { keys: ['comprar', 'pedir', 'quiero', 'ordenar', 'deseo', 'antojo', 'como pido', 'como compro', 'hacer pedido', 'realizar pedido', 'quiero uno', 'me llevas', 'mandame', 'dame uno', 'quiero pedir'], response: "¡Genial! Puedes hacer tu pedido aquí mismo agregando productos al carrito 🛒 y luego ir a Checkout. También puedes escribirnos directo al **WhatsApp**." },
    { keys: ['rastrear', 'donde esta mi pedido', 'estado', 'seguimiento', 'mi pedido', 'rastreo', 'tracking', 'donde va', 'llego', 'cuando llega', 'saber pedido', 'ver pedido'], action: "track_prompt" },

    // --- Productos específicos ---
    { keys: ['jugo', 'jugos', 'zumo', 'batido', 'surtido', 'licuado', 'bebida'], response: "🥤 Tenemos Jugos Especiales, Surtidos, Fresa, Papaya y más. Frescos y licuados al momento desde S/7.00. ¿Quieres verlos en la carta?" },
    { keys: ['empanada', 'empanadas', 'carne', 'pollo', 'queso', 'pastel', 'salado'], response: "🥟 Nuestras empanadas son un hit:\n• **Carne o Pollo** — S/6\n• **Queso** — S/5\n¡Salen calientitas del horno! ¿Agregamos alguna a tu pedido?" },
    { keys: ['pionono', 'piononos', 'brazo gitano', 'rollo'], response: "🍰 Nuestro pionono clásico cuesta S/4.50 la porción. ¡Suavecito y con mucho manjar! ¿Te antojaste?" },
    { keys: ['torta', 'pastel', 'keke', 'cake', 'queque', 'marmoleado'], response: "🎂 Nuestro Queque Marmoleado en porción está S/3.50. Perfecto para el lonchecito. Para pasteles enteros consulta por WhatsApp." },
    { keys: ['alfajor', 'alfajores', 'bocadito', 'bocaditos', 'galleta'], response: "🍪 Los **Alfajores de Maicena** (cajita x10) están a solo **S/15**. ¡Se deshacen en tu boca!" },
    { keys: ['sandwich', 'pan', 'sanguche', 'chicharron', 'pollo', 'palta'], response: "🥪 Sándwiches contundentes:\n• **Pan con Chicharrón** — S/14\n• **Pollo** — S/7\n• **Palta** — S/5\n¡Ideales para el desayuno o almuerzo rápido!" },
    { keys: ['manjar', 'dulce de leche', 'manjarblanco', 'arequipe', 'cajeta', 'con manjar', 'de manjar'], response: "🤎 Si te encanta el manjar, prueba:\n• **Pionono de Manjar y Pecanas** — S/70\n• **Alfajores de Maicena** — S/20 (rellenos de manjar)\n¡Son los favoritos!" },

    // --- Precios ---
    { keys: ['precio', 'costo', 'cuanto', 'vale', 'cotizar', 'cuanto cuesta', 'cuanto sale', 'a cuanto', 'precios', 'tarifa', 'tarifas', 'lista de precios'], response: "💰 Rango de precios:\n• Jugos: S/7 - S/12\n• Sándwiches: S/5 - S/14\n• Empanadas: S/5 - S/6\n• Postres: S/3 - S/15\n¡Súper económicos y ricos! ¿Quieres ver el menú?" },
    { keys: ['mas barato', 'mas economico', 'económico', 'barato', 'accesible', 'economico', 'precio bajo'], response: "💰 ¡Todo es súper accesible! Tenemos Gelatinas a S/3, Pionono clásico a S/4.50 y Empanadas desde S/5. ¡Date un gustito!" },
    { keys: ['mas caro', 'premium', 'mejor', 'lujoso', 'especial', 'lo mejor'], response: "✨ Nuestros platillos estrella son el **Pan con Chicharrón** (S/14) y la caja de **Alfajores x10** (S/15). ¡Buenísimos!" },

    // --- Ingredientes y alérgenos ---
    { keys: ['ingrediente', 'que lleva', 'que contiene', 'de que esta hecho', 'con que'], response: "📋 Todos nuestros postres son **artesanales** y usamos ingredientes de primera calidad: harina, huevos, mantequilla, chocolate importado y manjar blanco casero. Para detalles específicos, escríbenos por **WhatsApp**." },
    { keys: ['gluten', 'celiaco', 'celíaco', 'sin gluten'], response: "🌾 Actualmente todos nuestros productos contienen **gluten** (harina de trigo). Si necesitas una opción sin gluten, contáctanos por **WhatsApp** y vemos cómo ayudarte. 💛" },
    { keys: ['azucar', 'diabetico', 'diabético', 'sin azucar', 'diet', 'light', 'bajo en azucar'], response: "🍬 Por el momento no tenemos línea sin azúcar, pero podemos adaptar algunas recetas con edulcorante. ¡Escríbenos al **WhatsApp** para coordinar! 📱" },
    { keys: ['vegano', 'vegetariano', 'sin huevo', 'sin leche', 'sin lactosa', 'lactosa'], response: "🌱 Actualmente nuestros productos contienen lácteos y huevos. Estamos trabajando en opciones veganas. ¡Síguenos para enterarte cuando las lancemos! 🚀" },
    { keys: ['alergico', 'alergia', 'nuez', 'pecana', 'fruto seco', 'mani'], response: "⚠️ Algunos productos contienen **pecanas** y **frutos rojos**. Si tienes alguna alergia, por favor avísanos por **WhatsApp** antes de hacer tu pedido. Tu seguridad es lo primero. 💛" },

    // --- Tiempos y preparación ---
    { keys: ['cuanto demora', 'tiempo', 'demora', 'cuando llega', 'cuanto tarda', 'rapido'], response: "⏰ El delivery normalmente demora entre **30 minutos y 1 hora** según tu zona. Para pedidos personalizados necesitamos **24 horas de anticipación**." },
    { keys: ['para mañana', 'mañana', 'urgente', 'para hoy', 'mismo dia', 'para ya'], response: "⚡ Pedidos para el **mismo día** están sujetos a disponibilidad. Lo ideal es pedir con **24 horas de anticipación**. ¡Pero escríbenos por WhatsApp y hacemos lo posible! 💪" },
    { keys: ['anticipacion', 'con cuanto tiempo', 'reservar', 'reserva', 'encargar', 'encargo'], response: "📅 Te recomendamos hacer tu pedido con al menos **24 horas de anticipación**, especialmente para tortas y combos. ¡Así te garantizamos frescura total! 🎂" },

    // --- Eventos y ocasiones ---
    { keys: ['cumpleaños', 'cumple', 'birthday', 'fiesta'], response: "🎂 ¡Para cumpleaños te recomiendo el **Combo Cumpleaños** a S/110! Incluye Torta de Chocolate + Pionono + 10 Alfajores. ¡Todo lo que necesitas para celebrar! 🎉" },
    { keys: ['boda', 'matrimonio', 'casamiento'], response: "💒 ¡Qué emoción! Para bodas podemos preparar mesas de postres completas. Escríbenos por **WhatsApp** para una cotización personalizada. 💐" },
    { keys: ['baby shower', 'bautizo', 'primera comunion', 'comunión'], response: "👶 Para eventos especiales como baby showers y bautizos preparamos paquetes personalizados. ¡Contáctanos por **WhatsApp** y armamos algo hermoso! ✨" },
    { keys: ['corporativo', 'empresa', 'oficina', 'regalo empresarial', 'cliente'], response: "🏢 Hacemos pedidos corporativos y regalos empresariales. Las cajitas de alfajores son un éxito para regalar. ¡Pide cotización por **WhatsApp**! 📊" },
    { keys: ['cuantas personas', 'para cuantos', 'porciones', 'alcanza', 'rinde'], response: "🍰 Nuestras tortas (22cm) rinden para **8-10 porciones**. Los piononos para **8 porciones**. Si necesitas para más personas, ¡hacemos tamaños especiales! Consúltanos por **WhatsApp**." },
    { keys: ['evento', 'reunion', 'celebra', 'para evento'], response: "🎉 ¡Hacemos pedidos especiales para eventos! Contáctanos por **WhatsApp** para cotizarte un paquete a tu medida." },

    // --- Delivery y ubicación ---
    { keys: ['delivery', 'envio', 'envío', 'llevan', 'traen', 'reparto', 'distrito', 'cobertura', 'despacho'], response: "🛵 **Zonas de delivery:**\n• **Surco**: GRATIS 🎉\n• **Miraflores/San Borja**: S/5 - S/10\n• **Otras zonas**: Consultar por WhatsApp\n\nPedido mínimo: No hay. ¡Envíos desde 1 producto!" },
    { keys: ['surco', 'santiago de surco'], response: "🏡 ¡Estamos en **Santiago de Surco**! El delivery aquí es **GRATIS**. 🎉" },
    { keys: ['miraflores', 'san isidro', 'barranco', 'san borja'], response: "🚗 Sí hacemos delivery a tu zona. El costo varía entre **S/5 y S/10**. ¡Revisa las zonas en la sección de **Delivery**!" },
    { keys: ['lima norte', 'comas', 'los olivos', 'sjl', 'san juan', 'carabayllo', 'independencia'], response: "📍 Hacemos delivery a Lima Norte pero con un costo adicional. Consulta precios exactos por **WhatsApp**. 🛵" },
    { keys: ['recojo', 'recoger', 'pickup', 'ir a buscar', 'puedo ir'], response: "🏠 ¡Claro! Puedes recoger tu pedido en nuestro taller en **Surco**. Coordinamos hora exacta por **WhatsApp**." },
    { keys: ['ubicacion', 'donde estan', 'donde queda', 'direccion', 'local', 'taller', 'tienda fisica'], response: "📍 Nuestro taller está en **Santiago de Surco, Lima**. Somos una pastelería artesanal con delivery. ¡Te llevamos tus postres a domicilio! 🏡" },

    // --- Horarios ---
    { keys: ['horario', 'hora', 'atienden', 'abierto', 'cerrado', 'abren', 'cierran'], response: "🕒 **Horario de atención:**\nLunes a sábado: **9:00 AM - 8:00 PM**\nDomingos: **Cerrado**\n\n¡Te esperamos! ☀️" },
    { keys: ['domingo', 'domingos', 'fin de semana', 'feriado', 'feriados'], response: "📅 Los **domingos no atendemos**. De lunes a sábado de **9:00 AM a 8:00 PM**. Los feriados pueden variar, consúltanos por WhatsApp. 📱" },

    // --- Pagos ---
    { keys: ['pago', 'pagar', 'yape', 'plin', 'transferencia', 'efectivo', 'metodo de pago', 'forma de pago', 'como pago', 'medios de pago', 'con que pago', 'que aceptan', 'aceptan yape', 'aceptan transferencia', 'aceptan efectivo'], response: "💳 Aceptamos:\n• **Yape** 📱\n• **Plin** 📱\n• **Transferencia bancaria** 🏦\n• **Efectivo** 💵\n¡El que te sea más cómodo!" },
    { keys: ['tarjeta', 'visa', 'mastercard', 'credito', 'debito', 'pago con tarjeta', 'aceptan tarjeta'], response: "💳 Por el momento no aceptamos tarjetas directamente, pero sí puedes pagar con **Yape, Plin o transferencia**. ¡Son igual de fáciles! 📱" },
    { keys: ['factura', 'boleta', 'comprobante', 'sunat', 'ruc', 'facturacion', 'comprobante de pago', 'necesito boleta', 'necesito factura'], response: "🧾 Emitimos **boleta de venta**. Si necesitas factura, indícalo al hacer tu pedido por **WhatsApp** con tu RUC y razón social." },

    // --- Cupones ---
    { keys: ['cupon', 'cupón', 'codigo', 'descuento', 'codigo de descuento', 'promocion', 'promo', 'voucher', 'vale descuento', 'tengo cupon', 'como aplico cupon', 'donde pongo el codigo'], response: "🏷️ ¡Sí tenemos cupones! Aplica tu código en el **Checkout** antes de confirmar el pedido. Si no tienes uno, síguenos en redes para enterarte de las promos. 😉" },

    // --- Contacto ---
    { keys: ['telefono', 'celular', 'whatsapp', 'llamar', 'contacto', 'numero', 'escribir', 'comunicarme', 'hablar con alguien', 'hablar con una persona', 'agente', 'persona real', 'quiero hablar'], action: "whatsapp" },
    { keys: ['instagram', 'facebook', 'redes', 'red social', 'tiktok', 'redes sociales', 'siguenos', 'cuenta de instagram'], response: "📱 ¡Síguenos en nuestras redes sociales para ver novedades, promos y fotos de nuestros postres! También puedes contactarnos por **WhatsApp**." },
    { keys: ['reclamo', 'queja', 'problema', 'mal', 'feo', 'malo', 'roto', 'dañado', 'llego mal', 'se rompio', 'aplastado', 'insatisfecho', 'decepciona', 'no me gusto', 'terrible', 'pesimo'], response: "😔 Lamento que hayas tenido un inconveniente. Contáctanos por **WhatsApp** para resolverlo de inmediato. Tu satisfacción es nuestra prioridad. 💛" },

    // --- Constructor de tortas ---
    { keys: ['personalizar', 'personalizada', 'a mi gusto', 'diseñar', 'diseño', 'custom', 'armar torta', 'constructor', 'torta personalizada', 'a medida', 'con mi nombre', 'con foto', 'tematica', 'temática'], response: "🎨 ¡Puedes diseñar tu propia torta! Usa nuestro **Constructor de Tortas** y elige base, relleno, cobertura y tamaño. ¿Te llevo?", action: "open_builder" },

    // --- Comparaciones ---
    { keys: ['diferencia', 'cual es mejor', 'que me recomiendas', 'recomienda', 'recomendacion', 'sugerencia'], response: "🤔 Depende de lo que busques:\n• **Para chocoadictos** → Cake de Chocolate o Pionono Choco\n• **Para familias** → Combo Dulce Hogar (S/85)\n• **Para fiestas** → Combo Cumpleaños (S/110)\n• **Para regalar** → Alfajores x10 (S/20)\n¿Cuál te tienta? 😋" },
    { keys: ['mas vendido', 'popular', 'favorito', 'bestseller', 'estrella', 'top'], response: "⭐ Nuestros más vendidos son:\n1. 🥇 **Pionono Chocolate y Frutos Rojos**\n2. 🥈 **Cake de Chocolate**\n3. 🥉 **Combo Cumpleaños**\n¡No fallan! 🔥" },
    { keys: ['nuevo', 'novedad', 'nuevo producto', 'lanzamiento', 'que hay de nuevo'], response: "🆕 ¡Siempre estamos innovando! Síguenos en redes para enterarte de nuevos sabores y productos. ¿Mientras tanto, quieres ver nuestra carta actual? 📜" },

    // --- Confianza y calidad ---
    { keys: ['fresco', 'frescura', 'cuando se hizo', 'cuando lo hacen', 'vencimiento'], response: "🌿 Todos nuestros postres se preparan **frescos para cada pedido**. No vendemos productos del día anterior. ¡Calidad artesanal garantizada! ✨" },
    { keys: ['calidad', 'bueno', 'confiable', 'seguro', 'reseña', 'opinion'], response: "⭐ Tenemos un rating promedio de **4.8/5** de nuestros clientes. Usamos ingredientes premium y cada postre se hace con amor. ¡Puedes ver las opiniones en nuestra sección de **Feedback**! 💛" },
    { keys: ['devolucion', 'devolver', 'reembolso', 'cambio', 'garantia'], response: "🔄 Si tu pedido no llega en buen estado, lo reponemos sin costo. Envíanos una foto por **WhatsApp** y lo resolvemos al instante. Tu satisfacción está garantizada. ✅" },

    // --- Venta Cruzada y Sugestiva ---
    { keys: ['algo rico', 'antojito', 'que me recomiendas', 'que puedo probar', 'sugiéreme algo', 'no se que pedir'], response: ["😋 ¡Te recomiendo el **Pan con Chicharrón** (S/14)! O si quieres algo dulce, la **Crema Volteada** (S/6.50) no falla.", "🤤 ¿Un buen **Jugo Especial** acompañado de una **Empanada de Carne**? ¡La mejor combinación!"] },
    { keys: ['desayuno', 'mañana', 'temprano', 'lonche', 'tarde'], response: "☕ ¡Para el desayuno o lonche nada mejor que un Pan con Chicharrón o un Sándwich de Pollo, con su Café Pasado o Jugo! ¿Te antojaste?" },
    { keys: ['sed', 'bebida', 'tomar', 'refresco'], response: "🥤 Para la sed te recomiendo una deliciosa **Chicha Morada de Litro** o un **Maracumango Frozen** si hace mucho calor. ☀️" },
    { keys: ['saludable', 'sano', 'fitness', 'natural', 'sin conservantes'], response: "🌿 Todos nuestros productos son **100% artesanales** — sin conservantes, sin colorantes artificiales. Usamos ingredientes naturales y de primera calidad. ¡Cada postre se prepara fresco para tu pedido! ✨" },

    // --- Personalidad Pastelito ---
    { keys: ['quien eres', 'que eres', 'como te llamas', 'eres robot', 'eres humano', 'eres ia'], response: ["¡Soy Antojín 🍍! Tu asistente virtual de Antojitos Express. Fui creado con amor para endulzar tu día y ayudarte a encontrar el postre perfecto. 💛", "¡Hola! Me llamo Antojín 🍍 y soy el asistente de la pastelería. Conozco cada producto como la palma de mi mano. ¿En qué te ayudo?"] },
    { keys: ['gracias', 'muchas gracias', 'te agradezco', 'genial', 'excelente'], response: ["¡De nada! 💛 Aquí estaré siempre que necesites un antojito. 🧁", "¡Es un placer ayudarte! 😊 Si necesitas algo más, solo pregunta.", "¡Gracias a ti por confiar en nosotros! 🍰 ¡Endulza tu día!"] },
    { keys: ['aburrido', 'aburre', 'malo', 'no sirves', 'inutil', 'tonto'], response: "😅 ¡Lo siento si no fui de mucha ayuda! Soy un asistente especializado en postres y pedidos. Si tu pregunta es muy específica, te puedo conectar con nuestro equipo por **WhatsApp** — ellos te atenderán con gusto. 📱💛" },
    { keys: ['chiste', 'cuentame algo', 'broma', 'algo gracioso', 'entretenme'], response: ["😄 ¿Sabías que la torta de chocolate fue inventada por accidente? Un pastelero mezcló cacao en la masa por error... ¡y nació la magia! 🍫✨", "🧁 ¿Cuál es el postre más trabajador? ¡El pastel de capas, porque siempre está subiendo de nivel! 😂", "🤣 ¿Qué hace una torta cuando se siente sola? ¡Se va a una fiesta de cumpleaños! 🎂"] },
];

// ========================
// 🗺️ CUSTOMER FLOW NODES
// ========================

export const customerFlow: Record<string, FlowNode> = {
    start: {
        text: "¡Hola! Soy Antojín 🍍, tu asistente virtual. ¿En qué puedo endulzarte el día?",
        options: [
            { text: "📜 Ver Carta", action: "menu" },
            { text: "🕒 Horarios", next: "horarios" },
            { text: "🛵 Delivery", next: "delivery" },
            { text: "🎂 Recomiéndame", next: "recommend" },
            { text: "📦 Rastrear Pedido", action: "track_prompt" }
        ]
    },
    prices: {
        text: "💰 Rango de precios aprox:\n• Jugos: S/7 - S/12\n• Sándwiches: S/5 - S/14\n• Empanadas: S/5 - S/6\n• Postres: S/3 - S/15\n¿Quieres ver la carta completa?",
        options: [{ text: "📜 Ver Carta", action: "menu" }, { text: "⬅️ Volver", next: "start" }]
    },
    horarios: {
        text: "🕒 **Horario de atención:**\nLunes a sábado: **9:00 AM - 8:00 PM**\nDomingos: **Cerrado**\n\n¡Te esperamos! ☀️",
        options: [{ text: "⬅️ Volver al inicio", next: "start" }]
    },
    delivery: {
        text: "🛵 **Zonas de delivery:**\n• **Surco**: GRATIS 🎉\n• **Miraflores/San Borja**: S/5 - S/10\n• **Otras zonas**: Consultar por WhatsApp\n\nPedido mínimo: No hay. ¡Envíos desde 1 producto!",
        options: [{ text: "📱 WhatsApp", action: "whatsapp" }, { text: "⬅️ Volver", next: "start" }]
    },
    location: {
        text: "📍 Nuestro taller está en **Santiago de Surco, Lima**. Somos una pastelería artesanal con delivery. ¡Te llevamos tus postres a domicilio! 🏡",
        options: [{ text: "🛵 Ver Zonas de Delivery", next: "delivery" }, { text: "⬅️ Volver", next: "start" }]
    },
    recommend: {
        text: "😋 ¡Mis recomendaciones del día!\n\n🥇 **Pionono Chocolate y Frutos Rojos** (S/75) — Nuestro bestseller\n🥈 **Cake de Chocolate** (S/45) — Puro chocolate, 22cm\n🎉 **Combo Cumpleaños** (S/110) — Torta + Pionono + Alfajores\n\n¿Cuál se te antoja?",
        options: [
            { text: "🛒 Ver Carta", action: "menu" },
            { text: "💰 Ver Precios", next: "prices" },
            { text: "⬅️ Volver", next: "start" }
        ]
    },
    track_prompt: {
        text: "📦 ¡Claro! Para rastrear tu pedido, ingresa tu código (Ej: DM-20260219-ABCD) o usa el botón de abajo.",
        options: [{ text: "🔍 Abrir Rastreador", action: "open_tracker" }, { text: "⬅️ Volver", next: "start" }]
    }
};

// ========================
// 🛡️ ADMIN KB (CFO Mode)
// ========================

export const adminKB: KBItem[] = [
    { keys: ['hola', 'jefe', 'admin'], response: "admin_start" },
    { keys: ['ventas', 'dinero', 'ingresos', 'facturacion', 'facturación', 'revenue'], action: "calc_sales" },
    { keys: ['utilidad', 'ganancia', 'rentabilidad', 'margen', 'profit'], action: "calc_profit" },
    { keys: ['impuesto', 'igv', 'sunat', 'tributario'], action: "calc_tax" },
    { keys: ['proyeccion', 'proyección', 'meta', 'forecast', 'estimacion'], action: "calc_projection" },
    { keys: ['inventario', 'stock', 'disponibilidad', 'almacen'], action: "calc_inventory" },
    { keys: ['ticket', 'ticket promedio', 'gasto promedio'], action: "calc_ticket" },
    // v2.0 — Advanced Analytics
    { keys: ['semana', 'semanal', 'comparar semana', 'esta semana'], action: "calc_weekly" },
    { keys: ['hora pico', 'hora fuerte', 'cuando vendo mas', 'mejor hora'], action: "calc_peak" },
    { keys: ['mejor dia', 'dia fuerte', 'que dia vendo'], action: "calc_bestday" },
    // v2.0 — Wizards
    { keys: ['agregar producto', 'nuevo producto', 'crear producto'], action: "start_wizard_producto" },
    { keys: ['crear cupon', 'nuevo cupon', 'agregar cupon'], action: "start_wizard_cupon" },
    { keys: ['nueva zona', 'agregar zona', 'zona delivery'], action: "start_wizard_zona" },
    { keys: ['nuevo banner', 'crear banner', 'agregar banner'], action: "start_wizard_banner" },
    { keys: ['conectar wallet', 'como conecto', 'world coin', 'world app', 'metamask', 'web3', 'billetera'], action: "guide_wallet" },
    // v2.0 — Utilities
    { keys: ['limpiar chat', 'borrar conversacion', 'borrar historial'], action: "clear_chat" },
    // v3.0 — Smart CEO
    { keys: ['reporte', 'reporte completo', 'reporte ejecutivo', 'dame un resumen', 'como va el negocio', 'como vamos', 'resumen general'], action: "calc_smart_report" },
    { keys: ['ranking', 'ranking de productos', 'que producto se vende mas', 'productos mas vendidos', 'top productos', 'mejor producto'], action: "calc_ranking" },
    { keys: ['anomalia', 'alertas', 'problemas', 'algo raro', 'que esta mal', 'revisar alertas'], action: "calc_anomalies" },
    { keys: ['sugerencia', 'consejo', 'que me sugieres', 'ideas', 'que puedo hacer', 'como mejorar', 'ayudame a mejorar'], action: "calc_insights" },
    { keys: ['prediccion', 'predecir demanda', 'cuanto voy a vender', 'estimacion demanda', 'mañana cuanto', 'demanda'], action: "calc_demand" },
    { keys: ['exportar', 'descargar', 'csv', 'excel', 'descargar datos', 'bajar datos'], action: "export_csv" },
];

export const adminFlow: Record<string, FlowNode> = {
    admin_wallet_guide: {
        text: "🦊 **Asistente Web3** — Para conectar tu identidad digital:\n\n1. **PC (Metamask):** Haz clic en 'Conectar Wallet' y elige la extensión.\n2. **Móvil (World App):** Elige 'WalletConnect' y escanea el QR.\n\n⚠️ **Importante:** Necesitas configurar el `Project ID` en el código para que funcione el QR. ¿Quieres ver la guía técnica?",
        options: [
            { text: "📝 Ver Guía Técnica", action: "open_web3_guide" },
            { text: "✅ Ya entendí", next: "admin_start" }
        ]
    },
    admin_start: {
        text: "¡Hola Jefe! 🕵️‍♂️ Soy Antojín Admin (Modo CEO). ¿Qué quieres revisar hoy?",
        options: [
            { text: "💰 Ver Ventas", action: "calc_sales" },
            { text: "📉 Rentabilidad", action: "calc_profit" },
            { text: "🔮 Proyección", action: "calc_projection" },
            { text: "📦 Inventario", action: "calc_inventory" },
            { text: "📊 Analytics v2.0", next: "admin_analytics" },
            { text: "🧙 Wizards (paso a paso)", next: "admin_wizards" }
        ]
    },
    admin_analytics: {
        text: "📊 **Analytics Avanzados v2.0** — ¿Qué quieres analizar?",
        options: [
            { text: "📈 Comparación Semanal", action: "calc_weekly" },
            { text: "⏰ Hora Pico", action: "calc_peak" },
            { text: "📅 Mejor Día", action: "calc_bestday" },
            { text: "🎟️ Ticket Promedio", action: "calc_ticket" },
            { text: "🇵🇪 Impuestos (IGV)", action: "calc_tax" },
            { text: "⬅️ Volver", next: "admin_start" }
        ]
    },
    admin_wizards: {
        text: "🧙 **Wizards** — Elige qué quieres crear paso a paso:",
        options: [
            { text: "🧁 Agregar Producto", action: "start_wizard_producto" },
            { text: "🏷️ Crear Cupón", action: "start_wizard_cupon" },
            { text: "🛵 Agregar Zona Delivery", action: "start_wizard_zona" },
            { text: "📢 Crear Banner", action: "start_wizard_banner" },
            { text: "⬅️ Volver", next: "admin_start" }
        ]
    }
};
