// ⚡ MultiTurnEngine — Pastelito AI v2.0
// Manages guided multi-step conversational flows for complex admin actions

export interface WizardStep {
    id: string;
    prompt: string;
    type: 'text' | 'number' | 'select';
    options?: { text: string; value: string }[];
    validate?: (input: string) => boolean;
    errorMsg?: string;
}

export interface WizardFlow {
    id: string;
    title: string;
    steps: WizardStep[];
    summarize: (data: Record<string, string>) => string;
    buildEntities: (data: Record<string, string>) => Record<string, unknown>;
    executeIntent: string; // The adminActions intent to execute
}

export interface ActiveWizard {
    flowId: string;
    currentStep: number;
    data: Record<string, string>;
}

// ========================
// 📝 WIZARD FLOW DEFINITIONS
// ========================

export const wizardFlows: Record<string, WizardFlow> = {
    // ===== AGREGAR PRODUCTO =====
    agregar_producto: {
        id: 'agregar_producto',
        title: '🧁 Agregar Nuevo Producto',
        steps: [
            {
                id: 'title',
                prompt: '¿Cómo se llama el nuevo producto?',
                type: 'text',
                validate: (v) => v.length >= 3,
                errorMsg: 'El nombre debe tener al menos 3 caracteres.'
            },
            {
                id: 'price',
                prompt: '¿A qué precio? (solo el número, ej: 65)',
                type: 'number',
                validate: (v) => !isNaN(parseFloat(v)) && parseFloat(v) > 0,
                errorMsg: 'Ingresa un precio válido mayor a 0.'
            },
            {
                id: 'category',
                prompt: '¿En qué categoría?',
                type: 'select',
                options: [
                    { text: '🎂 Tortas', value: 'tortas' },
                    { text: '🍫 Piononos', value: 'piononos' },
                    { text: '🍪 Bocaditos', value: 'bocaditos' },
                    { text: '🎉 Combos', value: 'combos' }
                ]
            },
            {
                id: 'description',
                prompt: 'Escribe una descripción breve del producto:',
                type: 'text',
                validate: (v) => v.length >= 10,
                errorMsg: 'La descripción debe tener al menos 10 caracteres.'
            }
        ],
        summarize: (data) =>
            `📋 **Resumen del nuevo producto:**\n• Nombre: **${data.title}**\n• Precio: **S/${parseFloat(data.price).toFixed(2)}**\n• Categoría: **${data.category}**\n• Descripción: ${data.description}`,
        buildEntities: (data) => ({
            product: data.title,
            price: parseFloat(data.price),
            text: data.description,
            category: data.category
        }),
        executeIntent: 'agregar_producto_wizard'
    },

    // ===== CREAR CUPÓN =====
    crear_cupon: {
        id: 'crear_cupon',
        title: '🏷️ Crear Cupón de Descuento',
        steps: [
            {
                id: 'code',
                prompt: '¿Qué código tendrá el cupón? (ej: DULCE20, VERANO50)',
                type: 'text',
                validate: (v) => /^[A-Za-z0-9]{3,20}$/.test(v),
                errorMsg: 'El código debe tener entre 3 y 20 caracteres alfanuméricos, sin espacios.'
            },
            {
                id: 'discount',
                prompt: '¿Qué porcentaje de descuento? (solo el número, ej: 15)',
                type: 'number',
                validate: (v) => {
                    const n = parseInt(v);
                    return !isNaN(n) && n > 0 && n <= 100;
                },
                errorMsg: 'Ingresa un porcentaje entre 1 y 100.'
            },
            {
                id: 'type',
                prompt: '¿Qué tipo de cupón?',
                type: 'select',
                options: [
                    { text: '💯 Porcentaje (%)', value: 'percentage' },
                    { text: '💵 Monto fijo (S/)', value: 'fixed' }
                ]
            }
        ],
        summarize: (data) => {
            const symbol = data.type === 'percentage' ? '%' : 'S/';
            return `📋 **Resumen del cupón:**\n• Código: **${data.code.toUpperCase()}**\n• Descuento: **${data.discount}${symbol}**\n• Tipo: **${data.type === 'percentage' ? 'Porcentaje' : 'Monto fijo'}**`;
        },
        buildEntities: (data) => ({
            couponCode: data.code.toUpperCase(),
            discount: parseInt(data.discount),
            discountType: data.type === 'percentage' ? 'percent' : 'fixed'
        }),
        executeIntent: 'crear_cupon'
    },

    // ===== AGREGAR ZONA DE DELIVERY =====
    agregar_zona: {
        id: 'agregar_zona',
        title: '🛵 Agregar Zona de Delivery',
        steps: [
            {
                id: 'zone',
                prompt: '¿Cómo se llama la nueva zona? (ej: Miraflores, San Borja)',
                type: 'text',
                validate: (v) => v.length >= 3,
                errorMsg: 'El nombre de la zona debe tener al menos 3 caracteres.'
            },
            {
                id: 'price',
                prompt: '¿Cuánto costará el delivery a esta zona? (solo el número, ej: 8)',
                type: 'number',
                validate: (v) => !isNaN(parseFloat(v)) && parseFloat(v) >= 0,
                errorMsg: 'Ingresa un precio válido (0 para gratis).'
            }
        ],
        summarize: (data) => {
            const price = parseFloat(data.price);
            return `📋 **Nueva zona de delivery:**\n• Zona: **${data.zone}**\n• Costo: **${price === 0 ? 'GRATIS 🎉' : `S/${price.toFixed(2)}`}**`;
        },
        buildEntities: (data) => ({
            zone: data.zone,
            price: parseFloat(data.price)
        }),
        executeIntent: 'agregar_zona'
    },

    // ===== CREAR BANNER =====
    agregar_banner: {
        id: 'agregar_banner',
        title: '📢 Crear Banner Promocional',
        steps: [
            {
                id: 'text',
                prompt: '¿Qué texto tendrá el banner? (ej: 🔥 20% OFF en toda la carta)',
                type: 'text',
                validate: (v) => v.length >= 5,
                errorMsg: 'El texto debe tener al menos 5 caracteres.'
            },
            {
                id: 'link',
                prompt: '¿A dónde quieres que lleve el banner? (ej: /menu, /checkout)',
                type: 'select',
                options: [
                    { text: '📜 Carta (/menu)', value: '/menu' },
                    { text: '🛒 Checkout (/checkout)', value: '/checkout' },
                    { text: '🎂 Constructor (/builder)', value: '/builder' },
                    { text: '🏠 Inicio (/)', value: '/' }
                ]
            }
        ],
        summarize: (data) =>
            `📋 **Nuevo banner:**\n• Texto: **${data.text}**\n• Link: **${data.link}**`,
        buildEntities: (data) => ({
            text: data.text,
            bannerLink: data.link
        }),
        executeIntent: 'agregar_banner'
    }
};

// ========================
// 🧠 MULTI-TURN STATE MACHINE
// ========================

export class MultiTurnEngine {
    private activeWizard: ActiveWizard | null = null;

    /**
     * Check if a wizard is currently active.
     */
    isActive(): boolean {
        return this.activeWizard !== null;
    }

    /**
     * Get the ID of the active flow.
     */
    getActiveFlowId(): string | null {
        return this.activeWizard?.flowId || null;
    }

    /**
     * Start a new wizard flow.
     * Returns the first prompt message.
     */
    start(flowId: string): { prompt: string; options?: { text: string; value: string }[] } | null {
        const flow = wizardFlows[flowId];
        if (!flow) return null;

        this.activeWizard = {
            flowId,
            currentStep: 0,
            data: {}
        };

        const step = flow.steps[0];
        return {
            prompt: `${flow.title}\n\n**Paso 1/${flow.steps.length}** — ${step.prompt}`,
            options: step.options
        };
    }

    /**
     * Process user input for the current wizard step.
     * Returns the next prompt, a summary for confirmation, or the final result.
     */
    processInput(input: string): {
        type: 'next_step' | 'summary' | 'error' | 'cancelled';
        message: string;
        options?: { text: string; value: string }[];
        entities?: Record<string, unknown>;
        intent?: string;
    } {
        if (!this.activeWizard) {
            return { type: 'error', message: 'No hay un flujo activo.' };
        }

        // Check for cancellation
        const lower = input.toLowerCase().trim();
        if (['cancelar', 'salir', 'no', 'cancela', 'volver', 'atras', 'atrás'].includes(lower)) {
            this.cancel();
            return { type: 'cancelled', message: '❌ Flujo cancelado. ¿En qué más te ayudo, jefe?' };
        }

        const flow = wizardFlows[this.activeWizard.flowId];
        const stepIndex = this.activeWizard.currentStep;
        const step = flow.steps[stepIndex];

        // Validate input
        if (step.validate && !step.validate(input)) {
            return {
                type: 'error',
                message: `⚠️ ${step.errorMsg || 'Entrada inválida.'} Intenta de nuevo:`,
                options: step.options
            };
        }

        // Store the answer
        this.activeWizard.data[step.id] = input;

        // Check if there are more steps
        const nextStepIndex = stepIndex + 1;
        if (nextStepIndex < flow.steps.length) {
            this.activeWizard.currentStep = nextStepIndex;
            const nextStep = flow.steps[nextStepIndex];

            return {
                type: 'next_step',
                message: `**Paso ${nextStepIndex + 1}/${flow.steps.length}** — ${nextStep.prompt}`,
                options: nextStep.options
            };
        }

        // All steps completed — show summary and ask for confirmation
        const summary = flow.summarize(this.activeWizard.data);
        const entities = flow.buildEntities(this.activeWizard.data);
        const intent = flow.executeIntent;

        return {
            type: 'summary',
            message: `${summary}\n\n✅ ¿Confirmas? Responde **\"sí\"** o **\"no\"**.`,
            entities,
            intent
        };
    }

    /**
     * Confirm the wizard action. Returns entities and intent for execution.
     */
    confirm(): { entities: Record<string, unknown>; intent: string } | null {
        if (!this.activeWizard) return null;

        const flow = wizardFlows[this.activeWizard.flowId];
        const entities = flow.buildEntities(this.activeWizard.data);
        const intent = flow.executeIntent;

        this.activeWizard = null; // Clear the wizard
        return { entities, intent };
    }

    /**
     * Cancel the active wizard.
     */
    cancel(): void {
        this.activeWizard = null;
    }
}

export const multiTurnEngine = new MultiTurnEngine();
