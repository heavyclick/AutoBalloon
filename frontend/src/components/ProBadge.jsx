/**
 * ProBadge Component
 * Gold "PRO" badge shown next to logo for subscribers
 */

import React from 'react';

export function ProBadge({ className = '' }) {
  return (
    <span 
      className={`
        inline-flex items-center
        bg-gradient-to-r from-amber-500 to-orange-500
        text-black text-[10px] font-bold
        px-2 py-0.5 rounded
        uppercase tracking-wider
        ${className}
      `}
    >
      PRO
    </span>
  );
}
