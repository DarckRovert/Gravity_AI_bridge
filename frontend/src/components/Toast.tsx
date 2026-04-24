import { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, X, Info } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

export const ToastContainer = () => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const handleToast = (e: any) => {
      const { type, message } = e.detail;
      const id = Math.random().toString(36).substr(2, 9);
      setToasts(prev => [...prev, { id, type, message }]);
      
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 5000);
    };

    window.addEventListener('gravity-toast' as any, handleToast);
    return () => window.removeEventListener('gravity-toast' as any, handleToast);
  }, []);

  return (
    <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
      {toasts.map(toast => (
        <div 
          key={toast.id}
          className={`pointer-events-auto flex items-center gap-4 px-6 py-4 rounded-2xl border shadow-2xl animate-in slide-in-from-right-8 duration-300
            ${toast.type === 'success' ? 'bg-bg/90 backdrop-blur-xl border-status-success/30 text-status-success' : 
              toast.type === 'error' ? 'bg-bg/90 backdrop-blur-xl border-status-error/30 text-status-error' : 
              'bg-bg/90 backdrop-blur-xl border-accent-primary/30 text-accent-primary'}`}
        >
          {toast.type === 'success' && <CheckCircle size={20} />}
          {toast.type === 'error' && <AlertCircle size={20} />}
          {toast.type === 'info' && <Info size={20} />}
          
          <div className="flex-1">
            <div className="text-xs font-black uppercase tracking-widest opacity-60 mb-0.5">{toast.type}</div>
            <div className="text-sm font-bold text-text-primary">{toast.message}</div>
          </div>
          
          <button 
            onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X size={16} className="text-text-muted" />
          </button>
        </div>
      ))}
    </div>
  );
};

export const showToast = (type: ToastType, message: string) => {
  window.dispatchEvent(new CustomEvent('gravity-toast', { detail: { type, message } }));
};
