import React from 'react';

export function Skeleton({ className = '' }) {
  return (
    <div
      className={`animate-pulse bg-slate-200 dark:bg-slate-800 rounded-xl ${className}`}
    />
  );
}

export function SkeletonMetrics() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="p-5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-3"
        >
          <div className="flex items-center justify-between">
            <Skeleton className="w-24 h-4" />
            <Skeleton className="w-9 h-9 rounded-2xl" />
          </div>
          <Skeleton className="w-16 h-8" />
          <Skeleton className="w-32 h-3" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <Skeleton className="w-28 h-5 rounded-lg" />
        <Skeleton className="w-20 h-5 rounded-full" />
      </div>
      <Skeleton className="w-3/4 h-5 rounded-md" />
      <Skeleton className="w-full h-12 rounded-lg" />
      <div className="grid grid-cols-3 gap-3 pt-2">
        <Skeleton className="h-4 rounded-md" />
        <Skeleton className="h-4 rounded-md" />
        <Skeleton className="h-4 rounded-md" />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden p-4 space-y-3">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <Skeleton className="w-32 h-4" />
        <Skeleton className="w-24 h-4" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 py-2">
          <Skeleton className="w-16 h-4" />
          <Skeleton className="flex-1 h-4" />
          <Skeleton className="w-24 h-4" />
          <Skeleton className="w-20 h-6 rounded-full" />
        </div>
      ))}
    </div>
  );
}

export default Skeleton;
