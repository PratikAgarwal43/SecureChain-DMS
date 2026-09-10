import React from 'react';
import AshokaEmblem from './AshokaEmblem';
import { translations } from '../i18n/translations';

/**
 * Main Header (White/Cream #FFF9F2)
 * Left: Correct Ashoka Stambh Emblem (4 Lions silhouette)
 * Stacked Bilingual Title: Hindi line above, English line below
 * Subtitle: Ministry of Home Affairs, Government of India
 * NO technical or status badges.
 */
export default function MainHeader({ lang = 'en' }) {
  const t = translations[lang] || translations.en;

  return (
    <header className="bg-[#FFF9F2] border-b border-slate-200 py-2.5 sm:py-3.5 px-2 sm:px-4 md:px-6 select-none w-full">
      <div className="w-full flex items-center justify-between">

        {/* Left: Ashoka Stambh + Bilingual Title Stack in the Left Corner */}
        <div className="flex items-center space-x-2.5 sm:space-x-3.5">

          {/* Authentic Ashoka Stambh Silhouette */}
          <AshokaEmblem className="w-11 h-15 sm:w-14 sm:h-18" color="#12161C" />

          {/* Bilingual Title Stack */}
          <div className="flex flex-col justify-center">
            {/* Hindi Line Above */}
            <h1 className="text-sm sm:text-base md:text-lg font-bold text-slate-900 tracking-tight leading-snug font-['Noto_Sans_Devanagari',sans-serif]">
              {t.appTitleHindi}
            </h1>

            {/* English Line Below */}
            <h2 className="text-xs sm:text-sm md:text-base font-extrabold text-[#FF6A1A] tracking-tight leading-tight">
              {t.appTitleEnglish}
            </h2>

            {/* Ministry Subtitle */}
            <p className="text-[10px] sm:text-xs text-slate-600 font-medium mt-0.5">
              {t.appSubtitle}
            </p>
          </div>

        </div>

        {/* Right: National Seal / Digital India Seal Indicator */}
        <div className="hidden lg:flex items-center space-x-3 text-right text-xs">
          <div className="border-r border-slate-300 pr-3">
            <div className="font-bold text-slate-800">गृह मंत्रालय</div>
            <div className="text-[10px] text-slate-500 font-medium">MINISTRY OF HOME AFFAIRS</div>
          </div>
          <div className="text-left pl-1">
            <span className="inline-block px-2 py-0.5 text-[10px] font-bold text-slate-700 bg-amber-100/80 border border-amber-300 rounded">
              GOI Official Portal
            </span>
            <div className="text-[9px] text-slate-500 font-mono mt-0.5">Government Of India</div>
          </div>
        </div>

      </div>
    </header>
  );
}
