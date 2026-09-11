import React from 'react';
import { Globe, Eye, Contrast, PhoneCall, Sun, Moon, Keyboard } from 'lucide-react';
import { translations } from '../i18n/translations';

/**
 * Top Micro-Strip (~28px-30px dark navy bar #0B1220)
 * Per Master Spec Section 2:
 * - "Government of India" label
 * - language toggle (English/हिन्दी)
 * - accessibility contrast buttons (A- A A+)
 * - DARK MODE TOGGLE (sun/moon icon)
 * - national helpline
 * - single sign out exists in Navbar only — redundant sign out removed from here.
 */
export default function TopMicroStrip({ 
  lang = 'en', 
  onToggleLang, 
  fontSizeLevel = 0, 
  onChangeFontSize, 
  highContrast = false, 
  onToggleHighContrast,
  darkMode = false,
  onToggleDarkMode,
  onOpenShortcuts
}) {
  const t = translations[lang] || translations.en;

  return (
    <div className="bg-[#0B1220] text-slate-200 text-[11px] h-[30px] px-2 sm:px-4 flex items-center justify-between border-b border-slate-800 select-none z-50 w-full overflow-x-hidden">
      
      {/* Left: Government of India & Ministry */}
      <div className="flex items-center space-x-2 sm:space-x-3 truncate">
        <span className="font-semibold text-white tracking-wider flex items-center gap-1">
          <span>🇮🇳</span>
          <span className="truncate">{t.govtOfIndia}</span>
        </span>
        <span className="text-slate-500 hidden md:inline">|</span>
        <span className="text-slate-400 hidden lg:inline truncate">
          {t.ministryHeader}
        </span>
      </div>

      {/* Right: Controls (NO redundant sign out button) */}
      <div className="flex items-center space-x-1.5 sm:space-x-3 flex-shrink-0">
        
        {/* National Emergency Helpline */}
        <div className="hidden sm:flex items-center gap-1.5 text-amber-400 font-bold bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40" title="National Emergency Helpline">
          <PhoneCall className="w-3 h-3" />
          <span>112</span>
        </div>

        {/* Accessibility Contrast */}
        <button
          onClick={onToggleHighContrast}
          className={`flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-slate-800 transition-colors ${highContrast ? 'text-amber-400 font-bold' : 'text-slate-400'} cursor-pointer`}
          title="Toggle High Contrast Mode"
        >
          <Contrast className="w-3 h-3" />
          <span className="hidden md:inline">{highContrast ? t.contrastHigh : t.contrastStandard}</span>
        </button>

        {/* Keyboard Shortcuts Trigger Button */}
        <button
          onClick={onOpenShortcuts}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-slate-800 text-slate-400 hover:text-amber-300 transition-colors cursor-pointer"
          title="Keyboard Shortcuts Guide (Press '?')"
        >
          <Keyboard className="w-3 h-3" />
          <span className="hidden lg:inline">Shortcuts</span>
        </button>

        {/* Dark Mode Toggle */}
        <button
          onClick={onToggleDarkMode}
          className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800/90 hover:bg-slate-700 text-amber-400 border border-slate-700 hover:border-amber-400/60 transition-all cursor-pointer"
          title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {darkMode ? <Sun className="w-3 h-3 text-amber-300" /> : <Moon className="w-3 h-3 text-slate-300" />}
          <span className="hidden sm:inline font-semibold text-[10px] text-slate-200">
            {darkMode ? "Light" : "Dark"}
          </span>
        </button>

        {/* Font Scaling (A- / A / A+) */}
        <div className="flex items-center space-x-1 border-l border-slate-700 pl-1.5 sm:pl-3">
          <button 
            onClick={() => onChangeFontSize(-1)} 
            className={`px-1 rounded hover:bg-slate-800 ${fontSizeLevel === -1 ? 'text-amber-400 font-bold' : 'text-slate-400'} cursor-pointer`}
            title="Decrease Font Size"
          >
            A-
          </button>
          <button 
            onClick={() => onChangeFontSize(0)} 
            className={`px-1 rounded hover:bg-slate-800 ${fontSizeLevel === 0 ? 'text-amber-400 font-bold' : 'text-slate-400'} cursor-pointer`}
            title="Reset Font Size"
          >
            A
          </button>
          <button 
            onClick={() => onChangeFontSize(1)} 
            className={`px-1 rounded hover:bg-slate-800 ${fontSizeLevel === 1 ? 'text-amber-400 font-bold' : 'text-slate-400'} cursor-pointer`}
            title="Increase Font Size"
          >
            A+
          </button>
        </div>

        {/* Full Bilingual Toggle Button (English <-> हिन्दी) */}
        <button
          onClick={onToggleLang}
          className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 font-bold border border-slate-700 hover:border-amber-400 transition-all cursor-pointer text-[10px] sm:text-[11px]"
          title="Toggle Sitewide Language / भाषा बदलें"
        >
          <Globe className="w-3 h-3 text-amber-400" />
          <span className="hidden sm:inline">{lang === 'en' ? 'हिन्दी' : 'English'}</span>
          <span className="sm:hidden">{lang === 'en' ? 'HI' : 'EN'}</span>
        </button>

      </div>

    </div>
  );
}
