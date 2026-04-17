import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { pastelitoEngine } from '@/lib/pastelitoEngine';
import { customerKB, customerFlow } from '@/data/chatbot-kb';
import {
    greetings,
    farewells,
    unknownResponses,
    easterEggs,
    customerResponses
} from '@/data/chatbot-responses';

import { ChatOption } from '@/types/chatbot';

interface UseCustomerChatProps {
    addMessage: (text: string, sender: 'bot' | 'user') => void;
    showNode: (nodeId: string) => void;
    handleAction: (action: string) => void;
    router: ReturnType<typeof useRouter>;
    setIsOpen: (isOpen: boolean) => void;
    setCurrentOptions: (options: ChatOption[]) => void;
}

export function useCustomerChat({
    addMessage,
    showNode,
    handleAction,
    router,
    setIsOpen,
    setCurrentOptions
}: UseCustomerChatProps) {

    const handleCustomerMessage = useCallback((text: string) => {
        const result = pastelitoEngine.parse(text, false);

        // Customer NLP responses
        if (customerResponses[result.intent]) {
            const responses = customerResponses[result.intent];
            addMessage(responses[Math.floor(Math.random() * responses.length)], 'bot');
            if (result.intent === 'ver_menu') { router.push('/menu'); setIsOpen(false); }
            if (result.intent === 'rastrear') { router.push('/tracker'); setIsOpen(false); }
            if (result.intent === 'personalizar_torta') { router.push('/builder'); setIsOpen(false); }
            return;
        }

        if (result.intent === 'saludar') {
            addMessage(greetings[Math.floor(Math.random() * greetings.length)], 'bot');
            return;
        }

        if (result.intent === 'despedir') {
            addMessage(farewells[Math.floor(Math.random() * farewells.length)], 'bot');
            return;
        }

        if (easterEggs[result.intent]) {
            addMessage(easterEggs[result.intent][0], 'bot');
            return;
        }

        // Fallback to KB
        const kb = customerKB;
        const flow = customerFlow;
        const lowerText = text.toLowerCase();

        for (const item of kb) {
            if (item.keys.some(k => lowerText.includes(k))) {
                if (item.response && typeof item.response === 'string' && flow[item.response]) {
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

        addMessage(unknownResponses[Math.floor(Math.random() * unknownResponses.length)], 'bot');
        setCurrentOptions(flow['start']?.options || []);
    }, [addMessage, showNode, handleAction, router, setIsOpen, setCurrentOptions]);

    return { handleCustomerMessage };
}
