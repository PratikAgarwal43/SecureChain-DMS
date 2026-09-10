import React from 'react';
import { FolderSearch, Inbox, Search, FileX2 } from 'lucide-react';

export default function EmptyState({
  title = 'No Records Found',
  description = 'There are no active records matching the current filters or query.',
  icon: CustomIcon,
  actionLabel,
  onAction,
  className = ''
}) {
  const Icon = CustomIcon || Inbox;

  return (
    <div className={`p-10 sm:p-14 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl text-center space-y-4 max-w-lg mx-auto my-6 shadow-xs ${className}`}>
      <div className="w-16 h-16 rounded-2xl bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800/60 text-[#FF6A1A] mx-auto flex items-center justify-center">
        <Icon className="w-8 h-8" />
      </div>
      <div className="space-y-1.5">
        <h4 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          {title}
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
          {description}
        </p>
      </div>
      {actionLabel && onAction && (
        <div className="pt-2">
          <button
            type="button"
            onClick={onAction}
            className="px-4 py-2 bg-[#FF6A1A] hover:bg-[#E85B0E] text-white text-xs font-bold rounded-xl shadow-sm transition-all cursor-pointer inline-flex items-center gap-1.5"
          >
            {actionLabel}
          </button>
        </div>
      )}
    </div>
  );
}
