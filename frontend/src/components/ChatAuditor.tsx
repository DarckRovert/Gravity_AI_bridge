import React, { useState, useRef, useEffect } from 'react';
import { Send, Search, Shield, Brain, DollarSign, Trash2, Square } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types';

export const ChatAuditor: React.FC = () => {
  const defaultMessage: Message = {
    role: 'system',
    content: `🤖 **Gravity AI V16.3 PRO [Agentic Core Edition] — En Línea**

Sistema de orquestación unificada con capacidades de Agente Autónomo de Sistema.

**Módulos Activos:**
- 🧠 **Gravity Brain V16.3**: LLM con conciencia sistémica total.
- 📁 **Agentic ToolEngine**: Acceso directo al SO y sistema de archivos.
- 🎥 **Video Studio**: Fábrica de monetización autónoma + YouTube auto-upload.
- 📹 **V2V Live Studio**: Transformación de cámara en tiempo real vía DirectML.
- 💰 **Revenue Tracker**: Afiliados CPA inyectados en cada descripción.

**Comandos Estándar:**
\`/help\` — Lista completa de comandos
\`/status\` — Auditoría del sistema en vivo
\`/video crear <tema>\` — Encola un video

**Herramientas Agentic [V16.3 PRO]:**
\`/fs_ver <ruta>\` — Lee cualquier archivo del proyecto
\`/fs_listar <ruta>\` — Lista un directorio
\`/fs_buscar <texto> <ruta>\` — Busca en el código fuente
\`/terminal <comando>\` — Ejecuta comandos del sistema operativo`
  };

  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem('gravity_chat_auditor_history_v16');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error("Failed to parse chat history:", e);
    }
    return [defaultMessage];
  });
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    localStorage.setItem('gravity_chat_auditor_history_v16', JSON.stringify(messages));
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg = input.trim();
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    
    if (userMsg.toLowerCase() === '/limpiar' || userMsg.toLowerCase() === '/reset') {
      setMessages([defaultMessage]);
      return;
    }
    
    setMessages(prev => [...prev, { role: 'user', content: userMsg }, { role: 'assistant', content: '' }]);
    setIsStreaming(true);

    // AbortController con timeout de 90s — si el backend no responde, no quedamos colgados
    abortControllerRef.current = new AbortController();
    const timeoutId = setTimeout(() => {
      abortControllerRef.current?.abort();
    }, 90000);

    try {
      // Usamos el endpoint V11 que procesa contexto y comandos
      const res = await fetch('/v1/gravity/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal,
        body: JSON.stringify({
          model: 'gravity-brain-v16',
          messages: [...messages, { role: 'user', content: userMsg }].filter(m => m.role !== 'system'),
          stream: true
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let isFirstChunk = true;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunkStr = decoder.decode(value);
          const lines = chunkStr.split('\n').filter(l => l.startsWith('data: '));
          
          for (const line of lines) {
            const dataStr = line.replace('data: ', '');
            if (dataStr === '[DONE]') continue;
            try {
              const data = JSON.parse(dataStr);
              const delta = data.choices?.[0]?.delta?.content || '';
              if (delta) {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const lastIndex = newMsgs.length - 1;
                  // Si es el primer chunk, reemplazamos el contenido en lugar de concatenar si estaba vacío
                  if (isFirstChunk) {
                    newMsgs[lastIndex].content = delta;
                    isFirstChunk = false;
                  } else {
                    newMsgs[lastIndex].content += delta;
                  }
                  return newMsgs;
                });
              }
            } catch (e) {
              // Parse error
            }
          }
        }
      }
    } catch (e: any) {
      clearTimeout(timeoutId);
      if (e.name === 'AbortError') {
        // Puede ser timeout de 90s o cancelación manual del usuario
        setMessages(prev => {
          const newMsgs = [...prev];
          const last = newMsgs[newMsgs.length - 1];
          if (!last.content) {
            newMsgs[newMsgs.length - 1].content = `⏱ Tiempo de espera agotado. El motor de IA puede estar ocupado procesando otra tarea. Reintenta en unos segundos.`;
          }
          return newMsgs;
        });
      } else {
        setMessages(prev => {
          const newMsgs = [...prev];
          const errMsg = e?.message?.includes('fetch') 
            ? `❌ Motor ocupado o sin respuesta. Reintenta en unos segundos. (${e})`
            : `❌ Error de conexión: ${e}`;
          newMsgs[newMsgs.length - 1].content = errMsg;
          return newMsgs;
        });
      }
    } finally {
      clearTimeout(timeoutId);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  const injectHint = (cmd: string) => {
    setInput(cmd);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full bg-bg relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 scrollbar-hide">
        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col gap-2 max-w-[85%] animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === 'user' ? 'self-end' : 'self-start'}`}>
            <div className={`p-5 rounded-2xl leading-relaxed text-[15px] shadow-lg border backdrop-blur-md relative
              ${msg.role === 'user' 
                ? 'bg-user-bubble border-accent-primary/20 rounded-br-sm' 
                : 'bg-ai-bubble border-border-subtle rounded-bl-sm'}`}
            >
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  ul: ({node, ...props}: any) => <ul className="list-disc pl-5 my-2 space-y-1" {...props} />,
                  ol: ({node, ...props}: any) => <ol className="list-decimal pl-5 my-2 space-y-1" {...props} />,
                  a: ({node, ...props}: any) => <a className="text-accent-primary hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                  p: ({node, ...props}: any) => <p className="mb-2 last:mb-0" {...props} />,
                  code({node, inline, className, children, ...props}: any) {
                    return !inline ? (
                      <pre className="bg-[#0d1117] border border-border-subtle p-4 rounded-xl my-3 overflow-x-auto text-sm text-text-muted font-mono" {...props}>
                        <code>{children}</code>
                      </pre>
                    ) : (
                      <code className="bg-black/40 text-accent-secondary px-1.5 py-0.5 rounded text-sm" {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {msg.content}
              </ReactMarkdown>
              {isStreaming && i === messages.length - 1 && (
                <span className="inline-block w-2 h-4 ml-1 bg-accent-primary animate-pulse align-middle absolute bottom-5 right-5"></span>
              )}
            </div>
            <span className={`text-xs text-text-muted font-medium ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
              {msg.role === 'user' ? 'Tú' : 'System Auditor'}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-6 bg-surface/80 backdrop-blur-xl border-t border-border-subtle">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-3 bg-card border border-border-subtle rounded-2xl p-2 transition-all duration-300 focus-within:border-accent-primary focus-within:shadow-[0_0_0_2px_rgba(99,102,241,0.2)]">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ordena al Cerebro Sistémico... (Enter = enviar, Shift+Enter = salto)"
              className="flex-1 bg-transparent border-none text-text-primary p-2 text-[15px] resize-none outline-none max-h-[200px] min-h-[24px] scrollbar-hide"
              rows={1}
            />
            <button
              onClick={isStreaming ? handleStop : handleSend}
              disabled={(!input.trim() && !isStreaming)}
              className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 ${isStreaming ? 'bg-status-error/80 hover:bg-status-error text-white' : 'bg-gradient-to-br from-accent-primary to-accent-secondary text-white hover:scale-105 hover:shadow-[0_0_15px_var(--color-glow)]'} disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none disabled:cursor-not-allowed`}
            >
              {isStreaming ? <Square size={18} fill="currentColor" /> : <Send size={18} />}
            </button>
          </div>

          <div className="flex gap-3 mt-4 flex-wrap">
            <button onClick={() => injectHint('/fs_buscar ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Search size={14} /> Buscar código</button>
            <button onClick={() => injectHint('/fs_ver ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Shield size={14} /> Verificar archivo</button>
            <button onClick={() => injectHint('/fs_listar .')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Brain size={14} /> Listar proyecto</button>
            <button onClick={() => injectHint('/terminal ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><DollarSign size={14} /> Terminal</button>
            <button onClick={() => injectHint('!aprende ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Brain size={14} /> Persistir regla</button>
            
            <button onClick={() => setMessages([defaultMessage])} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-status-error/10 text-xs text-text-muted hover:text-status-error transition-colors ml-auto"><Trash2 size={14} /> Limpiar Chat</button>
          </div>
        </div>
      </div>
    </div>
  );
};
