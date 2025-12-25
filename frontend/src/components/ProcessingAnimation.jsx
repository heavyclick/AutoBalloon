/**
 * ProcessingAnimation Component
 * Shows a professional "working" animation while processing.
 * This builds perceived value by showing technical steps.
 */

import React from 'react';
import { useGuestSession } from '../context/GuestSessionContext';

export function ProcessingAnimation({ isVisible }) {
  const { processingStep } = useGuestSession();
  
  if (!isVisible) return null;

  const steps = [
    { id: 1, text: 'Scanning document...', icon: '📄' },
    { id: 2, text: 'Identifying GD&T frames...', icon: '🔍' },
    { id: 3, text: 'Extracting dimensions...', icon: '📏' },
    { id: 4, text: 'Mapping grid zones...', icon: '🗺️' },
    { id: 5, text: 'Generating AS9102 data...', icon: '📊' },
    { id: 6, text: 'Finalizing...', icon: '✨' },
  ];

  // Determine which step is active based on processingStep text
  const getStepStatus = (stepText) => {
    const currentIndex = steps.findIndex(s => s.text === processingStep);
    const stepIndex = steps.findIndex(s => s.text === stepText);
    
    if (stepIndex < currentIndex) return 'complete';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
      <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#E63946]/10 rounded-full mb-4">
            <svg 
              className="w-8 h-8 text-[#E63946] animate-spin" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            Processing Your Drawing
          </h2>
          <p className="text-gray-400 text-sm">
            AI is analyzing your blueprint...
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {steps.map((step) => {
            const status = getStepStatus(step.text);
            
            return (
              <div 
                key={step.id}
                className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                  status === 'active' 
                    ? 'bg-[#E63946]/10 border border-[#E63946]/30' 
                    : status === 'complete'
                    ? 'bg-green-500/10 border border-green-500/30'
                    : 'bg-[#0d0d0d] border border-transparent'
                }`}
              >
                {/* Status indicator */}
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                  status === 'active'
                    ? 'bg-[#E63946] animate-pulse'
                    : status === 'complete'
                    ? 'bg-green-500'
                    : 'bg-gray-700'
                }`}>
                  {status === 'complete' ? (
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : status === 'active' ? (
                    <div className="w-2 h-2 bg-white rounded-full" />
                  ) : (
                    <div className="w-2 h-2 bg-gray-500 rounded-full" />
                  )}
                </div>
                
                {/* Step text */}
                <span className={`text-sm ${
                  status === 'active'
                    ? 'text-white font-medium'
                    : status === 'complete'
                    ? 'text-green-400'
                    : 'text-gray-500'
                }`}>
                  {step.text}
                </span>
                
                {/* Loading dots for active step */}
                {status === 'active' && (
                  <div className="ml-auto flex gap-1">
                    <div className="w-1.5 h-1.5 bg-[#E63946] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-[#E63946] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-[#E63946] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer note */}
        <p className="text-center text-gray-500 text-xs mt-6">
          This typically takes 5-10 seconds depending on drawing complexity
        </p>
      </div>
    </div>
  );
}
