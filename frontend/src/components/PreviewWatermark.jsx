/**
 * PreviewWatermark Component
 * Displays a diagonal "PREVIEW MODE - AUTOBALLOON" watermark
 * over the canvas when user hasn't paid yet.
 */

import React from 'react';

export function PreviewWatermark({ isVisible = true }) {
  if (!isVisible) return null;

  return (
    <div 
      className="absolute inset-0 pointer-events-none overflow-hidden z-10"
      style={{ userSelect: 'none' }}
    >
      {/* Multiple watermark instances for coverage */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="whitespace-nowrap text-[80px] font-bold tracking-wider opacity-[0.07] select-none"
          style={{
            transform: 'rotate(-35deg)',
            color: '#E63946',
            textShadow: '0 0 20px rgba(230, 57, 70, 0.3)',
          }}
        >
          PREVIEW MODE
        </div>
      </div>
      
      {/* Top-left instance */}
      <div className="absolute -top-20 -left-20 flex items-center justify-center">
        <div 
          className="whitespace-nowrap text-[60px] font-bold tracking-wider opacity-[0.05] select-none"
          style={{
            transform: 'rotate(-35deg)',
            color: '#E63946',
          }}
        >
          AUTOBALLOON
        </div>
      </div>
      
      {/* Bottom-right instance */}
      <div className="absolute -bottom-20 -right-20 flex items-center justify-center">
        <div 
          className="whitespace-nowrap text-[60px] font-bold tracking-wider opacity-[0.05] select-none"
          style={{
            transform: 'rotate(-35deg)',
            color: '#E63946',
          }}
        >
          AUTOBALLOON
        </div>
      </div>

      {/* Center secondary text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div 
          className="whitespace-nowrap text-[30px] font-medium tracking-widest opacity-[0.04] select-none mt-32"
          style={{
            transform: 'rotate(-35deg)',
            color: '#ffffff',
          }}
        >
          EXPORT TO UNLOCK
        </div>
      </div>
    </div>
  );
}

/**
 * SessionTimer Component
 * Shows remaining time for the guest session
 */
export function SessionTimer({ timeRemaining, className = '' }) {
  if (!timeRemaining) return null;

  const isExpired = timeRemaining === 'Expired';
  const isLow = !isExpired && timeRemaining.startsWith('00:'); // Less than 1 hour

  return (
    <div 
      className={`flex items-center gap-2 text-sm ${
        isExpired 
          ? 'text-red-500' 
          : isLow 
          ? 'text-amber-500' 
          : 'text-gray-500'
      } ${className}`}
    >
      <svg 
        className="w-4 h-4" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" 
        />
      </svg>
      <span>
        {isExpired ? (
          'Session expired'
        ) : (
          <>Session expires in <span className="font-mono">{timeRemaining}</span></>
        )}
      </span>
    </div>
  );
}

/**
 * LockedFeatureBadge Component
 * Shows a lock icon next to premium features
 */
export function LockedFeatureBadge({ children, isLocked = true }) {
  if (!isLocked) {
    return <>{children}</>;
  }

  return (
    <div className="relative inline-flex items-center gap-1">
      <span className="blur-sm select-none">{children}</span>
      <svg 
        className="w-3 h-3 text-gray-500 absolute right-0 top-0" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" 
        />
      </svg>
    </div>
  );
}
