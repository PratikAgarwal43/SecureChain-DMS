import React from 'react';
import { Command, X, Keyboard, Search, Moon, Home, LogIn, ArrowUp, FileCheck2, LayoutDashboard } from 'lucide-react';

export default function ShortcutsModal({
  isOpen,
  onClose,
  onToggleDarkMode,
  onNavigateHome,
  onNavigateLogin,
  onOpenSearch
}) {
  if (!isOpen) return null;

  const shortcutsList = [
    { key: '/', desc: 'Focus search bar across views', icon: Search },
    { key: 'g then d', desc: 'Go to Dashboard Home', icon: LayoutDashboard },
    { key: 'g then a', desc: 'Go to Quorum Approvals Queue (/approvals)', icon: FileCheck2 },
    { key: 'Alt + D', desc: 'Toggle Dark / Light visual theme', icon: Moon },
    { key: 'Alt + H', desc: 'Navigate to Public Homepage', icon: Home },
    { key: '?', desc: 'Open this keyboard shortcuts guide', icon: Keyboard },
    { key: 'Esc', desc: 'Close any active modal or review dialog', icon: X }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl max-w-md w-full p-6 space-y-5 animate-in zoom-in-95 duration-150 text-slate-900 dark:text-slate-100">
        
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-orange-100 dark:bg-orange-950 text-[#FF6A1A] flex items-center justify-center">
              <Keyboard className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">Keyboard Navigation Shortcuts</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">Section 14 rapid productivity commands</p>
            </div>
          </div>
          <button
            onClick={() => onClose(false)}
            className="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-2">
          {shortcutsList.map((item, index) => {
            const Icon = item.icon;
            return (
              <div 
                key={index}
                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-700 dark:text-slate-300 font-medium">{item.desc}</span>
                </div>
                <kbd className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-[11px] font-mono font-bold text-slate-800 dark:text-slate-200 shadow-xs">
                  {item.key}
                </kbd>
              </div>
            );
          })}
        </div>

        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 text-center">
          Press <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded font-mono">Esc</kbd> anytime to dismiss.
        </div>

      </div>
    </div>
  );
}
