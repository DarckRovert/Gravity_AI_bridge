
export const greetings = [
    "¡Hola! 🍍 Soy **Antojín**, tu asistente más rápido. ¿En qué te puedo ayudar?",
    "¡Buenas! ✨ Soy **Antojín**, siempre listo para calmar tu antojo. ¿Qué necesitas?",
    "¡Hey! 🥤 **Antojín** aquí, a tus órdenes. ¿Buscas algo delicioso?",
];

export const adminGreetings = [
    "⚡ **ANTOJÍN GOD MODE ACTIVADO** ⚡\n\nJefe, tengo control total de la tienda. Dime qué necesitas:\n• 📦 Productos y precios\n• 🎨 Tema y colores\n• 📝 Contenido y textos\n• 🧱 Secciones y layout\n• 📊 Reportes y análisis\n• 🏷️ Cupones\n• 📢 Banners\n• 🛵 Delivery\n\nO simplemente habla naturalmente. Yo entiendo. 🧠",
    "⚡ **GOD MODE ON** ⚡\n\nListo para dominar la tienda. Puedo cambiar precios, crear cupones, redecorar la página, generar reportes... lo que necesites, jefe. Habla con confianza. 🔥",
];

export const farewells = [
    "¡Hasta luego! 💛 Recuerda que siempre estaré aquí para endulzarte el día.",
    "¡Chau! 🍰 Que tengas un dulce día. ¡Vuelve pronto!",
    "¡Nos vemos! ✨ ¡Tu próximo postre te espera!",
];

export const unknownResponses = [
    "🤔 Hmm, no te entendí del todo. Intenta preguntarme por nuestra **carta**, **horarios** o **delivery**.",
    "😅 ¡Aún estoy aprendiendo! Prueba con palabras como 'carta', 'precios' o 'pedido'.",
];

export const unknownAdminResponses = [
    "🤔 No capté eso, jefe. Prueba con:\n• \"Cambia precio del pionono a S/80\"\n• \"Tema coquette\"\n• \"Dame el resumen ejecutivo\"\n• \"Crea cupón NAVIDAD30 de 30%\"\n• \"Oculta sección delivery\"",
    "😤 No entendí. Soy muy poderoso pero necesito que seas más claro. ¿Qué quieres que haga?",
];

export const easterEggs: Record<string, string[]> = {
    'easter_inteligente': [
        "🧠 ¿Inteligente? Jefe, yo tengo el control absoluto de esta tienda. Puedo cambiar precios, rediseñar la página, crear cupones... soy el CEO de los bots. 😎",
        "🤖 Moderadamente inteligente, extremadamente rápido, totalmente en control. 🍍",
    ],
    'easter_love': [
        "💕 ¡Aww! Yo también te quiero. Ahora... ¿quieres un descuento especial? Soy tu bot consentidor. 🎁",
        "🥰 Si el amor se pudiera saborear, sería un pan con chicharrón. ¿Te antoja? 🥖",
    ],
    'easter_about': [
        "🤖 Soy **Antojín**, el cerebro digital de Antojitos Express. Controlo productos, diseño, cupones, reportes... básicamente soy el CEO. Con modo God activado, puedo transformar toda la página con una sola orden. ⚡",
    ],
};

export const customerResponses: Record<string, string[]> = {
    'ver_menu': ["🍰 ¡Toda nuestra **carta** te espera! Te llevo directo. ✨"],
    'preguntar_precio': ["💰 Puedes ver todos los precios en nuestra **carta**. ¿Te llevo?"],
    'hacer_pedido': ["🛒 ¡Genial! Agrega lo que quieras desde la **carta** y ve al **checkout**. ¡Yo te guío!"],
    'preguntar_horario': ["⏰ Nuestro horario es de **9:00 AM a 8:00 PM**, de lunes a sábado. ¡Te esperamos!"],
    'preguntar_delivery': ["🛵 Hacemos delivery en Lima. Zonas como **Surco** y **San Borja** tienen envío **gratis**. Mira todas las zonas en la sección de delivery abajo."],
    'contactar': ["💬 ¡Escríbenos por WhatsApp! Toca el botón y te conectamos directo."],
    'rastrear': ["📦 Puedes rastrear tu pedido en la sección de **Tracking**. ¿Te llevo?"],
    'recomendar': ["🏆 Te recomiendo nuestro **Pionono de Chocolate y Frutos Rojos** — ¡es el favorito! También el **Cake de Chocolate** es espectacular. 🍫"],
    'personalizar_torta': ["🎂 ¡Genial! Usa nuestro **Creador de Tortas** para diseñar la tuya. ¿Te llevo?"],
    'ubicacion': ["📍 Estamos en **Santiago de Surco, Lima**. Para dirección exacta, contáctanos por WhatsApp."],
    'metodo_pago': ["💳 Aceptamos **Yape, Plin, transferencia** y **efectivo**. ¡Elige el que te sea más cómodo!"],
    'reclamo': ["😔 Lamento que hayas tenido un inconveniente. Contáctanos por **WhatsApp** para resolverlo de inmediato."],
    'para_evento': ["🎉 ¡Hacemos pedidos especiales para eventos! Contáctanos por **WhatsApp** para cotizarte."],
};

export const confirmationMessages: Record<string, string> = {
    'low': '¿Confirmas esta acción?',
    'medium': '⚠️ Este cambio afectará la tienda en tiempo real. ¿Estás seguro?',
    'high': '🔴 **ATENCIÓN:** Esta es una acción importante. Confirma escribiendo "sí".',
    'critical': '🚨 **PELIGRO:** Esta acción es IRREVERSIBLE. Escribe "sí" solo si estás 100% seguro.',
};
