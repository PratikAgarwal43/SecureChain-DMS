import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
    return id;
  }, [removeToast]);

  const toast = {
    success: (msg, dur) => addToast(msg, 'success', dur),
    error: (msg, dur) => addToast(msg, 'error', dur),
    warning: (msg, dur) => addToast(msg, 'warning', dur),
    info: (msg, dur) => addToast(msg, 'info', dur),
    dismiss: removeToast
  };

  return (
    <ToastContext.Provider value={{ toast, addToast, removeToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col space-y-2 pointer-events-none max-w-sm w-full px-3">
        {toasts.map((t) => {
          const typeStyles = {
            success: 'bg-emerald-50 dark:bg-emerald-950/90 border-emerald-300 dark:border-emerald-700 text-emerald-900 dark:text-emerald-100',
            error: 'bg-rose-50 dark:bg-rose-950/90 border-rose-300 dark:border-rose-700 text-rose-900 dark:text-rose-100',
            warning: 'bg-amber-50 dark:bg-amber-950/90 border-amber-300 dark:border-amber-700 text-amber-900 dark:text-amber-100',
            info: 'bg-blue-50 dark:bg-blue-950/90 border-blue-300 dark:border-blue-700 text-blue-900 dark:text-blue-100'
          }[t.type] || 'bg-slate-50 border-slate-300 text-slate-900';

          const Icon = {
            success: CheckCircle2,
            error: AlertCircle,
            warning: AlertTriangle,
            info: Info
          }[t.type] || Info;

          const iconColors = {
            success: 'text-emerald-600 dark:text-emerald-400',
            error: 'text-rose-600 dark:text-rose-400',
            warning: 'text-amber-600 dark:text-amber-400',
            info: 'text-blue-600 dark:text-blue-400'
          }[t.type];

          return (
            <div
              key={t.id}
              className={`pointer-events-auto border rounded-2xl p-3.5 shadow-lg flex items-start gap-3 text-xs font-medium backdrop-blur-md transition-all animate-in fade-in slide-in-from-top-2 duration-200 ${typeStyles}`}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${iconColors}`} />
              <div className="flex-1 leading-snug break-words">
                {t.message}
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-0.5 rounded cursor-pointer"
                title="Dismiss"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context.toast;
}
