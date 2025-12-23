/**
 * HowItWorks Component
 * Shows the 3-step process
 */

import React from 'react';

const steps = [
  {
    number: '01',
    title: 'Upload Drawing',
    description: 'Drag & drop your PDF or image. Supports all common engineering drawing formats.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
  {
    number: '02',
    title: 'AI Detection',
    description: 'Our AI identifies all dimensions, assigns balloon numbers, and maps grid zones.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    number: '03',
    title: 'Export Report',
    description: 'Download your AS9102 Form 3 Excel report. Ready for QC inspection.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

export function HowItWorks() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-white text-center mb-4">
          How It Works
        </h2>
        <p className="text-gray-400 text-center mb-16 max-w-2xl mx-auto">
          From blueprint to inspection report in under 60 seconds
        </p>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div 
              key={step.number}
              className="relative bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 hover:border-[#E63946]/50 transition-colors group"
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-[#2a2a2a]" />
              )}

              {/* Step number */}
              <div className="text-[#E63946] text-sm font-bold mb-4 opacity-60">
                STEP {step.number}
              </div>

              {/* Icon */}
              <div className="w-16 h-16 bg-[#E63946]/10 rounded-xl flex items-center justify-center text-[#E63946] mb-6 group-hover:bg-[#E63946]/20 transition-colors">
                {step.icon}
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold text-white mb-3">
                {step.title}
              </h3>
              <p className="text-gray-400 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
