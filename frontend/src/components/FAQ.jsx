/**
 * FAQ Component - Updated with Zero-Storage Security Messaging
 */

import React, { useState } from 'react';

const faqs = [
  {
    question: 'How accurate is the dimension detection?',
    answer: 'Our AI achieves 95%+ accuracy on standard engineering drawings. The system detects decimals, fractions, tolerances, diameter symbols, and thread callouts. You can always manually adjust any missed or incorrect detections before export.'
  },
  {
    question: 'What file formats are supported?',
    answer: 'We support PDF files (single and multi-page), PNG, JPG, and TIFF images. For best results, use high-resolution scans or exports at 300 DPI or higher.'
  },
  {
    question: 'Is my data secure?',
    answer: 'Yes - we use a Zero-Storage security model. Your drawings are processed entirely in memory and immediately deleted after processing. We never store your technical data on our servers. All uploads are encrypted in transit (TLS 1.3). This architecture is designed to be compliant with ITAR, EAR, and NIST 800-171 requirements.'
  },
  {
    question: 'What is AS9102 Form 3?',
    answer: 'AS9102 is the aerospace standard for First Article Inspection (FAI). Form 3 specifically documents the dimensional inspection results - listing each characteristic, its requirement, actual measurement, and pass/fail status. AutoBalloon generates this form automatically with balloon numbers mapped to your drawing zones.'
  },
  {
    question: 'Can I cancel my subscription anytime?',
    answer: 'Absolutely. Cancel anytime with no questions asked. Your access continues until the end of your billing period. We also offer 24-hour passes for one-time needs with no subscription required.'
  },
  {
    question: 'Do you offer team or enterprise plans?',
    answer: 'Yes! Contact us at hello@autoballoon.space for volume pricing, team accounts, and enterprise features like SSO integration and dedicated support. We can also provide compliance documentation for your quality management system.'
  },
  {
    question: 'Where is my processing history stored?',
    answer: 'Your processing history is stored locally in your browser only. We never store your drawings or results on our servers. You can clear your local history anytime from your browser settings. This ensures your intellectual property stays completely under your control.'
  }
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState(null);

  const toggleFaq = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="py-20 px-4 bg-[#0d0d0d]">
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
                onClick={() => toggleFaq(index)}
                className="w-full px-6 py-4 flex items-center justify-between text-left"
              >
                <span className="text-white font-medium">{faq.question}</span>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
              {openIndex === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-400">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FAQ;
