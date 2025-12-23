/**
 * FAQ Component
 * Frequently asked questions accordion
 */

import React, { useState } from 'react';

const faqs = [
  {
    question: 'How accurate is the dimension detection?',
    answer: 'AutoBalloon achieves approximately 95% accuracy on standard engineering drawings. Think of it as a co-pilot, not autopilot — it handles the heavy lifting while you verify the results. You can easily add, remove, or adjust any balloons before exporting.',
  },
  {
    question: 'What file formats are supported?',
    answer: 'We support PDF, PNG, JPEG, and TIFF files up to 25MB. PDFs are converted to high-resolution images (400 DPI) for optimal OCR accuracy. For best results, use clean, high-contrast drawings.',
  },
  {
    question: 'Is my data secure?',
    answer: 'Absolutely. All uploads are encrypted in transit (TLS 1.3) and processed in isolated containers. Free tier files are automatically deleted after 24 hours. Pro users have permanent cloud storage with enterprise-grade encryption at rest.',
  },
  {
    question: 'What is AS9102 Form 3?',
    answer: 'AS9102 is the aerospace standard for First Article Inspection (FAI). Form 3 specifically documents "Characteristic Accountability & Verification" — the list of dimensions to be inspected. AutoBalloon generates this form automatically with balloon numbers, zone references, and dimension values.',
  },
  {
    question: 'Can I cancel my subscription anytime?',
    answer: 'Yes, cancel anytime with no questions asked. Your Pro access continues until the end of your billing period. Note: If you cancel and resubscribe later, you may lose your Early Adopter pricing.',
  },
  {
    question: 'Do you offer team or enterprise plans?',
    answer: 'Not yet, but we\'re working on it! If you need multiple seats or enterprise features (SSO, audit logs, custom integrations), reach out to us and we\'ll work something out.',
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <section id="faq" className="py-20 px-4 bg-[#0a0a0a]">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold text-white text-center mb-4">
          Frequently Asked Questions
        </h2>
        <p className="text-gray-400 text-center mb-12">
          Everything you need to know about AutoBalloon
        </p>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-[#161616] border border-[#2a2a2a] rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 hover:bg-[#1a1a1a] transition-colors"
              >
                <span className="font-medium text-white">{faq.question}</span>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform flex-shrink-0 ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {openIndex === index && (
                <div className="px-6 pb-5">
                  <p className="text-gray-400 leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
