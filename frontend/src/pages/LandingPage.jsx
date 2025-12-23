/**
 * LandingPage Component
 * "The Mullet" - Party on top (the tool), Business on bottom (marketing)
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useUsage } from '../hooks/useUsage';
import { Navbar } from '../components/Navbar';
import { HowItWorks } from '../components/HowItWorks';
import { PricingCard } from '../components/PricingCard';
import { FAQ } from '../components/FAQ';
import { Footer } from '../components/Footer';
import { PaywallModal } from '../components/PaywallModal';
import { DropZone } from '../components/DropZone';
import { FREE_TIER_LIMIT } from '../constants/config';

export function LandingPage() {
  const navigate = useNavigate();
  const { isPro } = useAuth();
  const { usage, shouldShowPaywall } = useUsage();
  const [showPaywall, setShowPaywall] = useState(false);

  // Called before processing starts
  const handleBeforeProcess = () => {
    if (shouldShowPaywall()) {
      setShowPaywall(true);
      return false; // Prevent processing
    }
    return true; // Allow processing
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-white">
      <Navbar />
      
      {/* Hero Section */}
      <section className="pt-24 pb-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          {/* Trust badge */}
          <div className="inline-flex items-center gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-full px-4 py-2 mb-8">
            <span className="text-green-500">●</span>
            <span className="text-gray-400 text-sm">Trusted by aerospace & manufacturing QC teams</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Stop Manually Ballooning
            <br />
            <span className="text-[#E63946]">PDF Drawings</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
            Get your AS9102 Excel Report in <span className="text-white font-semibold">10 seconds</span>.
            <br />
            AI-powered dimension detection for First Article Inspection.
          </p>

          {/* Usage indicator for free users */}
          {!isPro && (
            <div className="inline-flex items-center gap-2 text-sm text-gray-500 mb-8">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {usage.remaining > 0 ? (
                <span>
                  {usage.remaining} free {usage.remaining === 1 ? 'drawing' : 'drawings'} remaining this month
                </span>
              ) : (
                <span className="text-amber-500">Free limit reached</span>
              )}
            </div>
          )}

          {/* Pro indicator */}
          {isPro && (
            <div className="inline-flex items-center gap-2 text-sm mb-8">
              <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-black font-bold px-2 py-0.5 rounded text-xs">
                PRO
              </span>
              <span className="text-gray-400">Unlimited processing enabled</span>
            </div>
          )}
        </div>
      </section>

      {/* Interactive DropZone - THE TOOL */}
      <section className="px-4 pb-16">
        <div className="max-w-5xl mx-auto">
          <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-6 md:p-8">
            <DropZone onBeforeProcess={handleBeforeProcess} />
            
            {/* No signup required text */}
            {!isPro && (
              <p className="text-center text-gray-500 text-sm mt-6">
                No credit card required • {FREE_TIER_LIMIT} free drawings/month
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Problem / Solution */}
      <section className="py-20 px-4 bg-[#0a0a0a]">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* The Old Way */}
            <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8">
              <div className="text-red-500 text-sm font-bold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                THE OLD WAY
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">4+ Hours Per Drawing</h3>
              <ul className="space-y-3 text-gray-400">
                <li className="flex items-start gap-3">
                  <span className="text-red-500 mt-1">•</span>
                  Manually count and circle every dimension
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 mt-1">•</span>
                  Hand-write balloon numbers on printouts
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 mt-1">•</span>
                  Type each dimension into Excel spreadsheet
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 mt-1">•</span>
                  Cross-reference grid zones manually
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-red-500 mt-1">•</span>
                  Prone to human error and missed dimensions
                </li>
              </ul>
            </div>

            {/* The New Way */}
            <div className="bg-[#161616] border-2 border-[#E63946] rounded-2xl p-8 relative">
              <div className="absolute -top-3 -right-3 bg-[#E63946] text-white text-xs font-bold px-3 py-1 rounded-full">
                AutoBalloon
              </div>
              <div className="text-green-500 text-sm font-bold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                THE NEW WAY
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">5 Minutes, Done</h3>
              <ul className="space-y-3 text-gray-400">
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  Drop PDF → AI detects all dimensions instantly
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  Automatic balloon numbering with drag-to-adjust
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  One-click AS9102 Form 3 Excel export
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  Grid zones auto-detected and assigned
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-green-500 mt-1">✓</span>
                  Review, adjust, export — it's that simple
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <HowItWorks />

      {/* Compliance Section */}
      <section className="py-20 px-4 bg-[#0a0a0a]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Built for Compliance
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: 'AS9102 Form 3',
                description: 'Export directly to FAI Form 3 format with balloon numbers, zone references, and requirements.',
                icon: '📋',
              },
              {
                title: 'ISO 13485 Ready',
                description: 'Medical device manufacturers trust AutoBalloon for their quality documentation.',
                icon: '🏥',
              },
              {
                title: 'Secure Processing',
                description: 'Enterprise-grade encryption. Files auto-delete after 24h (free) or stored securely (Pro).',
                icon: '🔒',
              },
            ].map((item, i) => (
              <div key={i} className="bg-[#161616] border border-[#2a2a2a] rounded-xl p-6 text-center">
                <div className="text-4xl mb-4">{item.icon}</div>
                <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-gray-400 mb-12">
            No per-drawing fees. No hidden costs. Just unlimited processing.
          </p>
          <PricingCard />
        </div>
      </section>

      {/* FAQ */}
      <FAQ />

      {/* Footer */}
      <Footer />

      {/* Paywall Modal */}
      <PaywallModal 
        isOpen={showPaywall} 
        onLoginClick={() => {
          setShowPaywall(false);
          navigate('/login');
        }}
      />
    </div>
  );
}
