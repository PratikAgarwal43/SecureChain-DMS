import React from 'react';
import ashokaStambhImg from '../assets/ashoka_stambh.png';

/**
 * State Emblem of India (Ashoka Stambh / Lion Capital of Sarnath)
 * Uses the exact official emblem graphic provided by the user:
 * Four lions mounted on an abacus with the Dharma Chakra wheel, horse, and bull,
 * over the bell-shaped lotus, with the motto 'सत्यमेव जयते' in Devanagari.
 */
export default function AshokaEmblem({ className = "w-12 h-16", alt = "National Emblem of India - Lion Capital of Ashoka" }) {
  return (
    <div className={`inline-flex items-center justify-center flex-shrink-0 ${className}`}>
      <img 
        src={ashokaStambhImg} 
        alt={alt} 
        className="w-full h-full object-contain select-none pointer-events-none"
        loading="eager"
      />
    </div>
  );
}
