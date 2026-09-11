import React from 'react';

/**
 * Authentic Indian National Flag Banner
 * Full-width, 45px tall banner with 3 equal horizontal bands:
 * - Top: India Saffron (#FF9933)
 * - Middle: White (#FFFFFF) with a centered Navy Blue (#000080) Ashoka Chakra
 *   with 24 spokes sized to ~3/4 of the white band's height
 * - Bottom: India Green (#138808)
 */
export default function FlagBanner() {
  // Generate 24 spokes for the Ashoka Chakra (every 15 degrees)
  const spokes = Array.from({ length: 24 }, (_, i) => i * 15);

  return (
    <div className="w-full h-[45px] shadow-sm relative overflow-hidden flex flex-col select-none border-y border-slate-200" aria-label="Indian National Flag Banner">
      
      {/* 1. Saffron Band (Top 1/3 ~ 15px) */}
      <div className="w-full h-[15px] bg-[#FF9933]"></div>

      {/* 2. White Band (Middle 1/3 ~ 15px) with Centered Ashoka Chakra */}
      <div className="w-full h-[15px] bg-[#FFFFFF] relative flex items-center justify-center">
        
        {/* Navy Blue 24-Spoke Ashoka Chakra (approx 12px diameter = 3/4 of 15px) */}
        <div className="w-[12px] h-[12px] relative flex items-center justify-center">
          <svg 
            viewBox="0 0 100 100" 
            className="w-full h-full text-[#000080]"
            fill="none" 
            stroke="currentColor"
          >
            {/* Outer Rim */}
            <circle cx="50" cy="50" r="46" strokeWidth="6" />
            
            {/* Central Hub */}
            <circle cx="50" cy="50" r="10" fill="#000080" stroke="none" />
            
            {/* 24 Spokes radiating from center */}
            {spokes.map((angle) => {
              const rad = (angle * Math.PI) / 180;
              const x2 = 50 + 46 * Math.sin(rad);
              const y2 = 50 - 46 * Math.cos(rad);
              return (
                <line 
                  key={angle} 
                  x1="50" 
                  y1="50" 
                  x2={x2.toFixed(1)} 
                  y2={y2.toFixed(1)} 
                  strokeWidth="3.2" 
                />
              );
            })}
          </svg>
        </div>

      </div>

      {/* 3. India Green Band (Bottom 1/3 ~ 15px) */}
      <div className="w-full h-[15px] bg-[#138808]"></div>

    </div>
  );
}
