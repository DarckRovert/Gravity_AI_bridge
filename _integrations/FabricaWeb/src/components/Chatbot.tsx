"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useCart } from '@/context/CartContext';
import { useToast } from '@/context/ToastContext';
import { useSiteConfig } from '@/context/SiteConfigContext';
import { useSound } from '@/context/SoundContext';
import { useChatPersistence } from '@/hooks/useChatPersistence';
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition';
import { useChatImageUpload } from '@/hooks/useChatImageUpload';
import { useChatActions } from '@/hooks/useChatActions';
import { useGodMode } from '@/hooks/useGodMode';
import { useCustomerChat } from '@/hooks/useCustomerChat';
import { products as staticProducts } from '@/data/products';
import { customerFlow, adminFlow } from '@/data/chatbot-kb';
import { adminGreetings } from '@/data/chatbot-responses';
import { multiTurnEngine } from '@/lib/multiTurnEngine';
import { AdminActions } from '@/lib/adminActions';
import { recommendationEngine } from '@/lib/recommendationEngine';
import { proactiveAlerts } from '@/lib/proactiveAlerts';
import { getOrdersSync } from '@/lib/firebaseOrders';
import { ChatOption } from '@/types/chatbot';
import { processQuery } from '@/lib/ai/pastelitoNLP';
import { processCustomerQueryStreaming } from '@/lib/ai/fallbackChain';
import { pastelitoEngine, ExtractedEntities } from '@/lib/pastelitoEngine';
import { isValidSessionToken } from '@/lib/auth';
import ChatbotMessages from './ChatbotMessages';

export default function Chatbot() {
    // ── UI State ──────────────────────────────────────────────
    const [isOpen, setIsOpen] = useState(false);
    const [showPromo, setShowPromo] = useState(false);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [currentOptions, setCurrentOptions] = useState<ChatOption[]>([]);
    const [isAdmin, setIsAdmin] = useState(false);
    const [typingText, setTypingText] = useState('Escribiendo...');
    const [streamingText, setStreamingText] = useState('');
    const lastMessageTime = useRef<number>(0);

    // ── Refs & Context ────────────────────────────────────────
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { showToast } = useToast();
    const router = useRouter();
    const pathname = usePathname();
    const siteConfig = useSiteConfig();
    const { playSound } = useSound();

    // ── Custom Hooks ──────────────────────────────────────────
    const { messages, setMessages, clearHistory } = useChatPersistence();
    const { isListening, text: voiceText, startListening, stopListening, hasSupport: voiceSupported } = useVoiceRecognition();
    const { selectedFile, fileInputRef, handleFileSelect, openFilePicker, clearFile, processFile } = useChatImageUpload();

    // ── Voice → Input ─────────────────────────────────────────
    useEffect(() => { if (voiceText) setInput(voiceText); }, [voiceText]);

    // ── Admin Auth ────────────────────────────────────────────
    useEffect(() => {
        const session = localStorage.getItem('dm_admin_session');
        setIsAdmin(isValidSessionToken(session));
    }, [pathname]);

    // ── Helper: Add Message ──────────────────────────────────
    const addMessage = useCallback((text: string, sender: 'bot' | 'user', isGodMode = false) => {
        setMessages(prev => [...prev, { id: Date.now().toString() + Math.random(), text, sender, isGodMode }]);
        if (sender === 'bot') {
            playSound('ding');
            pastelitoEngine.addToHistory('bot', text);
        }
    }, [setMessages, playSound]);

    // ── Helper: Show Flow Node ───────────────────────────────
    const showNode = useCallback((nodeId: string) => {
        setIsTyping(true);
        setCurrentOptions([]);
        const flow = isAdmin ? adminFlow : customerFlow;
        const node = flow[nodeId];
        setTimeout(() => {
            if (node) {
                addMessage(node.text, 'bot');
                setCurrentOptions(node.options || []);
                if (node.action) handleAction(node.action);
            }
            setIsTyping(false);
        }, 600);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isAdmin, addMessage]);

    // ── Helper: Start Wizard ─────────────────────────────────
    const startWizard = useCallback((flowId: string) => {
        const result = multiTurnEngine.start(flowId);
        if (result) {
            addMessage(result.prompt, 'bot', true);
            if (result.options) {
                setCurrentOptions(result.options.map(o => ({ text: o.text, action: `wizard_select_${o.value}` })));
            }
        }
    }, [addMessage]);

    // ── Logic Hooks ──────────────────────────────────────────
    const { handleAction } = useChatActions({
        router, addMessage, showNode, siteConfig, startWizard, setIsOpen, setCurrentOptions, clearHistory
    });

    const { handleGodMode } = useGodMode({
        siteConfig, addMessage, showToast, router, showNode, handleAction, startWizard, clearHistory, setCurrentOptions
    });

    const { handleCustomerMessage } = useCustomerChat({
        addMessage, showNode, handleAction, router, setIsOpen, setCurrentOptions
    });

    // ── Effect: Engagement Promo ─────────────────────────────
    useEffect(() => {
        const timer = setTimeout(() => { if (!isOpen) setShowPromo(true); }, 20000);
        return () => clearTimeout(timer);
    }, [isOpen]);

    // ── Effect: Auto-scroll ──────────────────────────────────
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping, currentOptions, streamingText]);

    // ── Effect: Page-contextual greeting on open ─────────────
    useEffect(() => {
        if (isOpen && messages.length === 0) {
            if (isAdmin) {
                addMessage(adminGreetings[Math.floor(Math.random() * adminGreetings.length)], 'bot', true);
                setTimeout(() => {
                    const products = siteConfig?.config?.products || staticProducts;
                    const orders = getOrdersSync();
                    const alerts = proactiveAlerts.getAlerts(products, orders);
                    if (alerts.length > 0) addMessage(proactiveAlerts.formatAlertsSummary(alerts), 'bot', true);
                }, 1200);
            } else {
                const products = siteConfig?.config?.products || staticProducts;
                const orders = getOrdersSync();
                const rec = recommendationEngine.getSmartRecommendation(products, orders);
                const recText = rec ? ` Hoy te recomiendo el **${rec.title}** 😋` : '';

                if (pathname === '/menu') {
                    addMessage(`¡Hola! 🍍 Veo que estás explorando la carta.${recText} ¿Necesitas ayuda eligiendo?`, 'bot');
                    setCurrentOptions([
                        { text: "🔥 Más Vendidos", next: "recommend" },
                        { text: "💰 Ver Precios", next: "prices" },
                        { text: "🎉 Ver Combos", next: "start" },
                    ]);
                } else if (pathname === '/checkout') {
                    addMessage("¡Ya casi! 🛒 ¿Tienes alguna duda con tu pedido? Puedo ayudarte con **cupones** o **métodos de pago**.", 'bot');
                    setCurrentOptions([
                        { text: "🏷️ ¿Tienen cupones?", next: "start" },
                        { text: "💳 Métodos de pago", next: "start" },
                        { text: "🛵 Costo de Delivery", next: "delivery" },
                    ]);
                } else if (pathname === '/builder') {
                    addMessage("🎨 ¡Estás diseñando tu torta! Las de **chocolate** son las favoritas. ¿Necesitas ideas?", 'bot');
                    setCurrentOptions([
                        { text: "🎂 Recomiéndame", next: "recommend" },
                        { text: "📜 Ver Carta", action: "menu" },
                    ]);
                } else if (pathname === '/tracker') {
                    addMessage("📦 ¿Buscas tu pedido? Ingresa tu código arriba o escríbeme si necesitas ayuda.", 'bot');
                    setCurrentOptions([
                        { text: "📱 Contactar por WhatsApp", action: "whatsapp" },
                        { text: "⬅️ Volver al inicio", next: "start" },
                    ]);
                } else if (pathname === '/feedback') {
                    addMessage("🙏 ¡Gracias por tomarte el tiempo de darnos tu opinión! Tu feedback nos ayuda a mejorar cada día. 💛", 'bot');
                } else {
                    if (rec && window.scrollY > 400) {
                        addMessage(`¡Veo que estás explorando! 🍰${recText}`, 'bot');
                        setCurrentOptions([
                            { text: "🛒 Ver Carta", action: "menu" },
                            { text: "🤔 Recomiéndame", next: "recommend" },
                        ]);
                    } else {
                        showNode('start');
                    }
                }
            }
            setShowPromo(false);
        }
    }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Handler: Send Message ────────────────────────────────
    const handleSend = useCallback(() => {
        if (!input.trim() && !selectedFile) return;

        // Rate Limiting preventivo (1 seg)
        const now = Date.now();
        if (now - lastMessageTime.current < 1000) {
            showToast('Espera un momento, sigo pensando... ⏳', 'error');
            return;
        }
        lastMessageTime.current = now;

        const text = input.trim();

        // ─ File upload branch ─
        if (selectedFile) {
            addMessage(`📂 Subiendo archivo: ${selectedFile.name}${text ? ` — "${text}"` : ''}...`, 'user');
            setTimeout(async () => {
                if (selectedFile.type.startsWith('image/') && isAdmin) {
                    addMessage("📸 Procesando imagen...", 'bot', true);
                }
                const result = await processFile(selectedFile, text, isAdmin);
                addMessage(result.message, 'bot', isAdmin);
                clearFile();
            }, 500);
            setInput('');
            setCurrentOptions([]);
            return;
        }

        // ─ Text message branch ─
        addMessage(text, 'user');
        setInput('');
        if (fileInputRef.current) fileInputRef.current.value = '';
        setCurrentOptions([]);
        setIsTyping(true);

        setTimeout(async () => {
            // Wizard flow
            if (multiTurnEngine.isActive()) {
                const lower = text.toLowerCase().trim();

                if (['sí', 'si', 'yes', 'confirmar', 'dale', 'ok', 'confirmo'].includes(lower)) {
                    const result = multiTurnEngine.confirm();
                    if (result) {
                        const actions = new AdminActions(siteConfig);
                        const entities: ExtractedEntities = { ...result.entities, rawText: '' } as ExtractedEntities;
                        const actionResult = actions.execute(result.intent, entities);
                        addMessage(`${actionResult.emoji} ${actionResult.message}`, 'bot', true);
                        if (actionResult.success) showToast('✅ Hecho', 'success');
                    }
                    setIsTyping(false);
                    return;
                }

                const stepResult = multiTurnEngine.processInput(text);
                if (stepResult.type === 'cancelled' || stepResult.type === 'error' || stepResult.type === 'next_step' || stepResult.type === 'summary') {
                    addMessage(stepResult.message, 'bot', true);
                    if (stepResult.options) {
                        setCurrentOptions(stepResult.options.map(o => ({ text: o.text, action: `wizard_select_${o.value}` })));
                    }
                }
                setIsTyping(false);
                return;
            }

            // Admin mode
            if (isAdmin) {
                handleGodMode(text);
                setIsTyping(false);
                return;
            }

            // Customer: intelligent streaming fallback chain
            const liveProducts = siteConfig?.config?.products || staticProducts;
            const waNumber = siteConfig?.config?.content?.whatsappNumber || '51965968723';

            setTypingText('Antojín está pensando... 🧠');
            const ctx = {
                products: liveProducts,
                deliveryZones: siteConfig?.config?.deliveryZones || [],
                coupons: siteConfig?.config?.coupons || [],
                isAdmin: false,
                currentPage: pathname || '/',
                businessHours: 'Lunes a Sábado 9am - 8pm',
                whatsappNumber: waNumber,
                conversationHistory: pastelitoEngine.getHistory?.() || [],
            };

            let accumulated = '';
            try {
                for await (const { chunk, done, source, action } of processCustomerQueryStreaming(text, ctx)) {
                    if (!done) {
                        accumulated += chunk;
                        setStreamingText(accumulated);
                        if (source === 'semantic') setTypingText('🧠 Semantic AI');
                        else if (source === 'local-brain') setTypingText('⚡ Local Brain');
                    } else {
                        if (chunk) accumulated += chunk;
                        setStreamingText('');
                        if (accumulated) addMessage(accumulated, 'bot');
                        if (action) handleAction(action);
                        else if (!accumulated) handleCustomerMessage(text);
                    }
                }
            } catch {
                setStreamingText('');
                const nlpResult = processQuery(text, liveProducts, waNumber);
                addMessage(nlpResult.response, 'bot');
            }
            setIsTyping(false);
        }, 600);
    }, [input, selectedFile, isAdmin, addMessage, handleGodMode, handleCustomerMessage, handleAction, siteConfig, showToast, playSound, processFile, clearFile, pathname, fileInputRef]);

    // ── Handler: Option Click ────────────────────────────────
    const handleOptionClick = useCallback((opt: ChatOption) => {
        addMessage(opt.text, 'user');
        setCurrentOptions([]);
        if (opt.next) showNode(opt.next);
        else if (opt.action) handleAction(opt.action);
    }, [addMessage, showNode, handleAction]);

    // ── Handler: Download History ────────────────────────────
    const handleDownloadHistory = useCallback(() => {
        const historyText = messages.map(m => `[${m.sender === 'bot' ? 'Antojín' : 'Cliente'}] (${new Date().toLocaleTimeString()}): ${m.text}`).join('\n');
        const blob = new Blob([historyText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-history-${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Historial descargado 📥', 'success');
    }, [messages, showToast]);

    // ── JSX ──────────────────────────────────────────────────
    return (
        <>
            {/* Engagement Promo Pill */}
            {showPromo && !isOpen && (
                <div className="fixed bottom-24 right-6 z-50 animate-fade-up">
                    <div className="bg-white/80 backdrop-blur-2xl p-4 pr-10 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.15)] border border-white/40 flex items-center gap-4 group hover:scale-105 transition-all cursor-pointer relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-2xl shadow-inner">🤖</div>
                        <div>
                            <p className="text-sm font-bold text-primary leading-tight">¿En qué puedo ayudarte?</p>
                            <p className="text-xs text-gray-500 font-medium">{'<BRAND_MASCOT>'} está listo para atenderte ✨</p>
                        </div>
                        <button onClick={(e) => { e.stopPropagation(); setShowPromo(false); }} className="absolute top-3 right-4 text-gray-400 hover:text-primary transition-colors p-1">✕</button>
                        <button onClick={() => { setIsOpen(true); setShowPromo(false); }} className="absolute inset-0 w-full h-full opacity-0" />
                    </div>
                </div>
            )}

            {/* Toggle Button */}
            <button
                onClick={() => { setIsOpen(!isOpen); setShowPromo(false); }}
                className={`fixed bottom-6 right-6 z-50 ${isAdmin ? 'bg-gradient-to-r from-purple-600 to-pink-600' : 'bg-accent'} text-white p-4 rounded-full shadow-lg hover:scale-110 transition-transform ${isAdmin ? 'animate-pulse' : 'animate-bounce'}`}
            >
                <span className="text-2xl">{isAdmin ? '⚡' : '🍍'}</span>
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed inset-0 z-[60] flex flex-col bg-white md:inset-auto md:bottom-24 md:right-6 md:w-96 md:h-[600px] md:rounded-3xl shadow-2xl md:border md:border-primary/20 overflow-hidden animate-reveal">
                    {/* Header */}
                    <div className={`${isAdmin ? 'bg-gradient-to-r from-purple-900 to-pink-800' : 'bg-primary'} text-paper p-5 flex justify-between items-center shadow-md relative z-10`}>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-xl shadow-inner">
                                {isAdmin ? '⚡' : '🍍'}
                            </div>
                            <div>
                                <h3 className="font-bold leading-tight">{isAdmin ? 'Antojín CEO' : 'Antojín'}</h3>
                                <p className="text-[10px] opacity-80 uppercase tracking-widest font-bold">
                                    {isAdmin ? 'God Mode Active ⚡' : 'Asistente Mágico'}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleDownloadHistory}
                                className="p-2 hover:bg-white/10 rounded-full transition-colors text-xl hidden sm:block"
                                title="Descargar Historial"
                            >
                                📥
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 hover:bg-white/10 rounded-full transition-colors text-xl md:hidden"
                                aria-label="Minimizar chat"
                                title="Minimizar"
                            >
                                ─
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 hover:bg-white/10 rounded-full transition-colors text-xl"
                                aria-label="Cerrar chat"
                                title="Cerrar"
                            >
                                ✕
                            </button>
                        </div>
                    </div>

                    {/* Messages (extracted component) */}
                    <ChatbotMessages
                        messages={messages}
                        streamingText={streamingText}
                        isTyping={isTyping}
                        typingText={typingText}
                        isAdmin={isAdmin}
                        currentOptions={currentOptions}
                        messagesEndRef={messagesEndRef}
                        onOptionClick={handleOptionClick}
                    />

                    {/* Input Bar */}
                    <div className="p-4 bg-white border-t border-primary/5 flex gap-3 items-center pb-8 md:pb-4">
                        {isAdmin && (
                            <>
                                <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} accept="image/*,.pdf,.doc,.docx" />
                                <button
                                    onClick={openFilePicker}
                                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${selectedFile ? 'bg-green-100 text-green-600' : 'bg-gray-50 text-gray-400 hover:text-primary hover:bg-primary/5'}`}
                                    title="Adjuntar recurso"
                                >
                                    {selectedFile ? '📎' : '➕'}
                                </button>
                            </>
                        )}
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                placeholder={isAdmin ? '⚡ Ordena algo, jefe...' : isListening ? 'Escuchando... 🎤' : 'Escribe aquí...'}
                                className={`w-full bg-gray-50 border border-gray-100 rounded-2xl px-5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:bg-white transition-all ${isListening ? 'animate-pulse ring-2 ring-red-200 bg-red-50' : ''}`}
                            />
                        </div>

                        {voiceSupported && (
                            <button
                                onClick={isListening ? stopListening : startListening}
                                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isListening ? 'bg-red-500 text-white shadow-lg animate-pulse' : 'bg-gray-50 text-gray-400 hover:text-primary hover:bg-primary/5'}`}
                                title="Hablar"
                            >
                                {isListening ? '⏹️' : '🎤'}
                            </button>
                        )}

                        <button
                            onClick={handleSend}
                            className={`rounded-full w-10 h-10 flex items-center justify-center transition-all shadow-md active:scale-90
                                ${isAdmin
                                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                                    : 'bg-primary text-paper hover:bg-secondary'}`}
                        >
                            ➤
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}
