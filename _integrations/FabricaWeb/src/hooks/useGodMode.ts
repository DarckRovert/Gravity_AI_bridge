import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { pastelitoEngine } from '@/lib/pastelitoEngine';
import { AdminActions } from '@/lib/adminActions';
import { themePresets } from '@/lib/themeEngine';
import { adminKB, adminFlow } from '@/data/chatbot-kb';
import {
    adminGreetings,
    farewells,
    unknownAdminResponses,
    easterEggs,
    customerResponses,
    confirmationMessages
} from '@/data/chatbot-responses';

import { ChatOption } from '@/types/chatbot';
import { SiteConfigContextType } from '@/context/SiteConfigContext';

interface UseGodModeProps {
    siteConfig: SiteConfigContextType;
    addMessage: (text: string, sender: 'bot' | 'user', isGodMode?: boolean) => void;
    showToast: (message: string, type: 'success' | 'error' | 'info') => void;
    router: ReturnType<typeof useRouter>;
    showNode: (nodeId: string) => void;
    handleAction: (action: string) => void;
    startWizard: (flowId: string) => void;
    clearHistory: () => void;
    setCurrentOptions: (options: ChatOption[]) => void;
}

export function useGodMode({
    siteConfig,
    addMessage,
    showToast,
    router,
    showNode,
    handleAction,
    startWizard,
    clearHistory,
    setCurrentOptions
}: UseGodModeProps) {

    const handleGodMode = useCallback((text: string) => {
        const result = pastelitoEngine.parse(text, true);

        // Handle confirmation responses
        if (result.intent === 'confirm_action') {
            const pending = result.entities;
            const actions = new AdminActions(siteConfig);
            // Re-parse the original intent (stored context)
            const lastIntent = pastelitoEngine.recall('lastConfirmedIntent');
            if (lastIntent) {
                const actionResult = actions.execute(lastIntent, pending);
                addMessage(`${actionResult.emoji} ${actionResult.message}`, 'bot', true);
                showToast(actionResult.success ? '✅ Acción ejecutada' : '❌ Error', actionResult.success ? 'success' : 'error');
            }
            return;
        }

        if (result.intent === 'cancel_action') {
            addMessage("❌ Acción cancelada. ¿Qué más necesitas, jefe?", 'bot', true);
            return;
        }

        // limpiar_chat — must be handled here (not in adminActions) to clear actual state
        if (result.intent === 'limpiar_chat') {
            clearHistory();
            addMessage("🗑️ Historial de conversación limpiado. ¿En qué puedo ayudarte?", 'bot');
            return;
        }

        // Wizard triggers — start guided multi-step flows
        const wizardMap: Record<string, string> = {
            'wizard_producto': 'agregar_producto',
            'wizard_cupon': 'crear_cupon',
            'wizard_zona': 'agregar_zona',
            'wizard_banner': 'agregar_banner'
        };
        if (wizardMap[result.intent]) {
            startWizard(wizardMap[result.intent]);
            return;
        }

        // Easter eggs
        if (easterEggs[result.intent]) {
            const responses = easterEggs[result.intent];
            addMessage(responses[Math.floor(Math.random() * responses.length)], 'bot', true);
            return;
        }

        // Customer-type queries that work in admin too
        if (customerResponses[result.intent]) {
            const responses = customerResponses[result.intent];
            const baseResponse = responses[Math.floor(Math.random() * responses.length)];

            // 🧠 Navigation-aware responses — confirm admin mode persists
            const navRoutes: Record<string, string> = {
                'ver_menu': '/menu',
                'rastrear': '/tracker',
                'personalizar_torta': '/builder',
            };

            if (navRoutes[result.intent]) {
                router.push(navRoutes[result.intent]);
                addMessage(`${baseResponse}\n\n🔓 _Sigo en modo admin, jefe. Pregúntame lo que necesites._`, 'bot', true);
            } else {
                addMessage(baseResponse, 'bot');
            }
            return;
        }

        // Greetings
        if (result.intent === 'saludar') {
            addMessage(adminGreetings[Math.floor(Math.random() * adminGreetings.length)], 'bot', true);
            return;
        }

        // Farewells
        if (result.intent === 'despedir') {
            addMessage(farewells[Math.floor(Math.random() * farewells.length)], 'bot');
            return;
        }

        // Unknown
        if (result.intent === 'unknown') {
            // Try fallback to chatbot-kb
            const kb = adminKB;
            const lowerText = text.toLowerCase();
            for (const item of kb) {
                if (item.keys.some(k => lowerText.includes(k))) {
                    if (item.response && typeof item.response === 'string' && adminFlow[item.response]) {
                        showNode(item.response);
                    } else if (item.response) {
                        const respText = Array.isArray(item.response)
                            ? item.response[Math.floor(Math.random() * item.response.length)]
                            : item.response;
                        addMessage(respText, 'bot');
                        if (item.options) setCurrentOptions(item.options);
                    }
                    if (item.action) handleAction(item.action);
                    return;
                }
            }

            // 🧠 Smart fallback — suggest similar commands using NLP engine
            const suggestions = pastelitoEngine.getSuggestions(text, true);
            if (suggestions.length > 0) {
                const intentLabels: Record<string, string> = {
                    'cambiar_precio': '💰 Cambiar precio',
                    'cambiar_stock': '📦 Cambiar stock',
                    'agregar_producto': '🆕 Agregar producto',
                    'eliminar_producto': '🗑️ Eliminar producto',
                    'aplicar_tema': '🎨 Cambiar tema',
                    'ver_ventas': '📊 Ver ventas',
                    'crear_cupon': '🏷️ Crear cupón',
                    'toggle_seccion': '👁️ Mostrar/ocultar sección',
                    'ver_menu': '📋 Ver menú',
                    'destacar_producto': '⭐ Destacar producto',
                    'cambiar_titulo': '✏️ Cambiar título',
                    'exportar_datos': '📂 Exportar datos',
                };
                const suggestionList = suggestions
                    .map(s => intentLabels[s] || s)
                    .join('\n• ');
                addMessage(`🤔 No entendí bien, jefe. ¿Quisiste decir alguno de estos?\n\n• ${suggestionList}\n\n_Sé más específico y te ayudo._`, 'bot', true);
            } else {
                addMessage(unknownAdminResponses[Math.floor(Math.random() * unknownAdminResponses.length)], 'bot', true);
            }
            return;
        }

        // Admin action — check if needs confirmation
        if (result.requiresConfirmation && result.riskLevel !== 'none') {
            const actions = new AdminActions(siteConfig);
            // Generate confirmation message
            const confirmMsg = confirmationMessages[result.riskLevel] || '¿Confirmas?';
            const descParts: string[] = [];
            if (result.entities.product) descParts.push(`Producto: ${result.entities.product}`);
            if (result.entities.price) descParts.push(`Precio: S/${result.entities.price.toFixed(2)}`);
            if (result.entities.preset) descParts.push(`Tema: ${themePresets[result.entities.preset]?.label || result.entities.preset}`);
            if (result.entities.color) descParts.push(`Color: ${result.entities.color}`);
            if (result.entities.couponCode) descParts.push(`Cupón: ${result.entities.couponCode}`);
            if (result.entities.sectionId) descParts.push(`Sección: ${result.entities.sectionId}`);
            if (result.entities.text) descParts.push(`Texto: "${result.entities.text}"`);
            if (result.entities.zone) descParts.push(`Zona: ${result.entities.zone}`);

            const details = descParts.length > 0 ? `\n📋 ${descParts.join(' | ')}` : '';
            addMessage(`${confirmMsg}${details}\n\n👉 Responde **"sí"** para confirmar o **"no"** para cancelar.`, 'bot', true);

            pastelitoEngine.remember('lastConfirmedIntent', result.intent);
            pastelitoEngine.setPending(result.intent, result.entities, details, result.riskLevel);
            return;
        }

        // Execute directly (no-risk actions)
        const actions = new AdminActions(siteConfig);
        const actionResult = actions.execute(result.intent, result.entities);
        addMessage(`${actionResult.emoji} ${actionResult.message}`, 'bot', true);
        if (actionResult.success) {
            showToast('✅ Hecho', 'success');
        }

    }, [siteConfig, addMessage, showToast, router, showNode, handleAction, startWizard, clearHistory, setCurrentOptions]);

    return { handleGodMode };
}
