import React, { useState, useRef, useEffect } from 'react';
import { Send, Search, Shield, Brain, DollarSign, Trash2 } from 'lucide-react';
import type { Message } from '../types';

export const ChatAuditor: React.FC = () => {
  const defaultMessage: Message = {
    role: 'system',
    content: `👋 **Bienvenido a Gravity AI Bridge V12.1 PRO [Organismo Vivo]**\n\nSistema de orquestación unificada en línea con arquitectura React/Vite.\n\n**Módulos Activos:**\n- 🧠 **Gravity Brain**: Telemetría inyectada en tiempo real.\n- 🎨 **Vision Studio**: Renderizado paralelo V12.1 PRO.\n- 🎬 **Video Studio**: FFMPEG orquestado conversacionalmente.\n\n**Atajos rápidos:**\n\`/help\` — Comandos disponibles\n\`/search\` — Búsqueda web\n\`/status\` — Auditoría de sistema`
  };

  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem('gravity_chat_auditor_history');
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    localStorage.setItem('gravity_chat_auditor_history', JSON.stringify(messages));
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMsg = input.trim();
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    
    setMessages(prev => [...prev, { role: 'user', content: userMsg }, { role: 'assistant', content: '' }]);
    setIsStreaming(true);

    try {
      // Usamos el endpoint V11 que procesa contexto y comandos
      const res = await fetch('http://localhost:7860/v1/gravity/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'gravity-brain-v12',
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
    } catch (e) {
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1].content = `❌ Error de conexión: ${e}`;
        return newMsgs;
      });
    } finally {
      setIsStreaming(false);
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

  // Función simple para formatear markdown básico a HTML
  const formatContent = (content: string) => {
    // Escapar HTML básico
    let html = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Negritas
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Código en línea
    html = html.replace(/`(.*?)`/g, '<code class="bg-black/40 text-accent-secondary px-1.5 py-0.5 rounded text-sm">$1</code>');
    // Bloques de código (muy simplificado)
    html = html.replace(/```([\s\S]*?)```/g, '<pre class="bg-[#0d1117] border border-border-subtle p-4 rounded-xl my-3 overflow-x-auto text-sm text-text-muted">$1</pre>');
    // Saltos de línea
    html = html.replace(/\n/g, '<br/>');
    return html;
  };

  return (
    <div className="flex flex-col h-full bg-bg relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 scrollbar-hide">
        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col gap-2 max-w-[85%] animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === 'user' ? 'self-end' : 'self-start'}`}>
            <div className={`p-5 rounded-2xl leading-relaxed text-[15px] shadow-lg border backdrop-blur-md
              ${msg.role === 'user' 
                ? 'bg-user-bubble border-accent-primary/20 rounded-br-sm' 
                : 'bg-ai-bubble border-border-subtle rounded-bl-sm'}`}
              dangerouslySetInnerHTML={{ __html: formatContent(msg.content) + (isStreaming && i === messages.length - 1 ? '<span class="inline-block w-2 h-4 ml-1 bg-accent-primary animate-pulse align-middle"></span>' : '') }}
            />
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
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="bg-gradient-to-br from-accent-primary to-accent-secondary text-white w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_15px_var(--color-glow)] disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none disabled:cursor-not-allowed"
            >
              <Send size={18} />
            </button>
          </div>

          <div className="flex gap-3 mt-4 flex-wrap">
            <button onClick={() => injectHint('/search ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Search size={14} /> Buscar web</button>
            <button onClick={() => injectHint('/verify ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Shield size={14} /> Verificar archivo</button>
            <button onClick={() => injectHint('!aprende ')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><Brain size={14} /> Persistir regla</button>
            <button onClick={() => injectHint('/cost')} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border-subtle text-xs text-text-muted hover:text-text-primary hover:border-accent-primary transition-colors"><DollarSign size={14} /> Ver consumo</button>
            
            <button onClick={() => setMessages([defaultMessage])} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-status-error/10 text-xs text-text-muted hover:text-status-error transition-colors ml-auto"><Trash2 size={14} /> Limpiar Chat</button>
          </div>
        </div>
      </div>
    </div>
  );
};
