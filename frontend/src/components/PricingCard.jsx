/**
 * PricingCard Component
 * Displays the Pro subscription pricing
 */

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL, PRICE_MONTHLY, PRICE_FUTURE } from '../constants/config';

export function PricingCard() {
  const { user, isPro } = useAuth();
  const [email, setEmail] = useState(user?.email || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubscribe = async (e) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/payments/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          callback_url: `${window.location.origin}/success`,
        }),
      });

      const data = await response.json();

      if (data.success && data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        setError(data.message || 'Failed to create checkout');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isPro) {
    return (
      <div id="pricing" className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 max-w-md mx-auto">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-black font-bold px-4 py-2 rounded-full mb-4">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            PRO ACTIVE
          </div>
          <h3 className="text-xl font-bold text-white mb-2">You're all set!</h3>
          <p className="text-gray-400">Enjoy unlimited blueprint processing.</p>
        </div>
      </div>
    );
  }

  return (
    <div id="pricing" className="relative bg-[#161616] border-2 border-[#E63946] rounded-2xl p-8 max-w-md mx-auto">
      {/* Badge */}
      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
        <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-black text-xs font-bold px-4 py-1 rounded-full">
          EARLY ADOPTER PRICING
        </span>
      </div>

      {/* Header */}
      <div className="text-center mb-6 pt-4">
        <h3 className="text-2xl font-bold text-white mb-2">Pro Plan</h3>
        <div className="flex items-baseline justify-center gap-2">
          <span className="text-gray-500 line-through text-lg">${PRICE_FUTURE}</span>
          <span className="text-5xl font-bold text-white">${PRICE_MONTHLY}</span>
          <span className="text-gray-400">/month</span>
        </div>
        <p className="text-amber-500 text-sm mt-2 font-medium">
          🔒 Locked in for life when you subscribe now
        </p>
      </div>

      {/* Features */}
      <ul className="space-y-4 mb-8">
        {[
          'Unlimited blueprint processing',
          'AS9102 Form 3 Excel exports',
          'Permanent history & cloud sync',
          'Priority processing speed',
          'Email support',
        ].map((feature, i) => (
          <li key={i} className="flex items-center gap-3 text-gray-300">
            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {feature}
          </li>
        ))}
      </ul>

      {/* Form */}
      <form onSubmit={handleSubscribe} className="space-y-4">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          className="w-full bg-[#0d0d0d] border border-[#2a2a2a] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#E63946] transition-colors"
          required
        />

        {error && (
          <p className="text-red-500 text-sm text-center">{error}</p>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-[#E63946] hover:bg-[#c62d39] text-white font-bold py-4 rounded-lg transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Processing...' : 'Start 7-Day Free Trial'}
        </button>
      </form>

      <p className="text-center text-gray-500 text-sm mt-4">
        Cancel anytime • No questions asked
      </p>
    </div>
  );
}
