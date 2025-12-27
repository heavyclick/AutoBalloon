/**
 * LandingPage Component
 * Updated with ZERO-STORAGE SECURITY messaging
 * Privacy-focused copy for aerospace/defense/medical device customers
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { HowItWorks } from '../components/HowItWorks';
import { PricingCard } from '../components/PricingCard';
import { FAQ } from '../components/FAQ';
import { Footer } from '../components/Footer';
import { DropZone } from '../components/DropZone';
import { PromoRedemption, usePromoCode } from '../components/PromoRedemption';
import { API_BASE_URL } from '../constants/config';

export function LandingPage() {
  const { isPro } = useAuth();
  const { promoCode, clearPromo } = usePromoCode();
  const [hasAccess, setHasAccess] = useState(false);
  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    const checkExistingAccess = async () => {
      const email = localStorage.getItem('autoballoon_user_email');
      if (email) {
        setUserEmail(email);
        try {
          const response = await fetch(`${API_BASE_URL}/access/check?email=${encodeURIComponent(email)}`);
          const data = await response.json();
          if (data.has_access) {
            setHasAccess(true);
          }
        } catch (err) {
          console.error('Access check error:', err);
        }
      }
    };
    checkExistingAccess();
  }, []);

  const handlePromoSuccess = (email) => {
    setUserEmail(email);
    setHasAccess(true);
    clearPromo();
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-white">
      <Navbar />
      
      {promoCode && (
        <PromoRedemption 
          promoCode={promoCode}
          onSuccess={handlePromoSuccess}
          onClose={clearPromo}
        />
      )}
      
      {/* Hero Section */}
      <section className="pt-24 pb-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          {/* Security Trust Badge */}
          <div className="inline-flex items-center gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-full px-4 py-2 mb-8">
            <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span className="text-gray-400 text-sm">Zero-Storage Security • ITAR/EAR Compliant</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Stop Manually Ballooning
            <br />
            <span className="text-[#E63946]">PDF Drawings</span>
          </h1>

          {/* Subheadline */}
          <p className="text-xl text-gray-400 mb-4 max-w-2xl mx-auto">
            Get your AS9102 Excel Report in <span className="text-white font-semibold">10 seconds</span>.
            <br />
            AI-powered dimension detection for First Article Inspection.
          </p>

          {/* Security Promise - NEW */}
          <p className="text-sm text-green-500/80 mb-8 flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Your drawings never touch our servers. Processed in memory, deleted immediately.
          </p>

          {/* Access Status */}
          {hasAccess && (
            <div className="inline-flex items-center gap-2 text-sm mb-8 bg-green-500/10 border border-green-500/30 px-4 py-2 rounded-full">
              <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-400">Free access activated for {userEmail}</span>
            </div>
          )}

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

      {/* Interactive DropZone */}
      <section className="px-4 pb-16">
        <div className="max-w-5xl mx-auto">
          <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-6 md:p-8">
            <DropZone hasPromoAccess={hasAccess} userEmail={userEmail} />
            
            {!isPro && (
              <p className="text-center text-gray-500 text-sm mt-6">
                Try it free • No signup required • Your data is never stored
              </p>
            )}
          </div>
        </div>
      </section>

      {/* SECURITY SECTION - NEW */}
      <section className="py-20 px-4 bg-gradient-to-b from-[#0a0a0a] to-[#0d0d0d]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">
              🔒 Military-Grade Privacy
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Built for aerospace, defense, and medical device manufacturers who can't risk their IP.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {[
              {
                icon: (
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                ),
                title: 'Zero Storage Architecture',
                description: 'Files are processed entirely in RAM and immediately deleted. No disk writes, no database storage, no cloud copies.'
              },
              {
                icon: (
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                ),
                title: 'Local History Only',
                description: 'Your processing history stays in your browser\'s localStorage. We have no access to it. Clear it anytime.'
              },
              {
                icon: (
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                ),
                title: 'Compliance Ready',
                description: 'ITAR, EAR, NIST 800-171, ISO 27001, GDPR compliant by design. We can\'t leak what we don\'t store.'
              },
            ].map((item, i) => (
              <div key={i} className="bg-[#161616] border border-[#2a2a2a] rounded-xl p-6 hover:border-green-500/30 transition-colors">
                <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center text-green-500 mb-4">
                  {item.icon}
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.description}</p>
              </div>
            ))}
          </div>

          {/* Security Quote */}
          <div className="bg-[#161616] border border-green-500/20 rounded-xl p-8 text-center max-w-3xl mx-auto">
            <blockquote className="text-lg text-gray-300 italic mb-4">
              "Unlike other tools, AutoBalloon processes your drawings in real-time and immediately discards them. We never store your technical data on our servers. Your intellectual property remains 100% yours."
            </blockquote>
            <div className="flex items-center justify-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Processing in memory
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Automatic deletion
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                No cloud storage
              </div>
            </div>
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
                  <span className="text-green-400 font-medium">Zero storage = Zero risk</span>
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
                title: 'ITAR/EAR Compliant',
                description: 'Zero-storage architecture means your controlled technical data never leaves your browser.',
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
            No per-drawing fees. No hidden costs. No data storage.
          </p>
          <PricingCard />
        </div>
      </section>

      {/* FAQ */}
      <FAQ />

      {/* Footer */}
      <Footer />
    </div>
  );
}
