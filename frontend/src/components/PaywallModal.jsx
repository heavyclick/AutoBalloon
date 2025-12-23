/**
 * PaywallModal Component
 * The "trap" modal that appears when user hits free limit
 * Cannot be dismissed - must upgrade or login
 */

import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL, PRICE_MONTHLY, PRICE_FUTURE } from '../constants/config';

export function PaywallModal({ isOpen, onLoginClick }) {
  const { isPro } = useAuth();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Don't show if Pro or not open
  if (!isOpen || isPro) return null;

  const handleUpgrade = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email');
      return;
    }

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
        // Redirect to Paystack checkout
        window.location.href = data.authorization_url;
      } else {
        setError(data.message || 'Failed to create checkout. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop - blurs the content behind */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />
      
      {/* Modal */}
      <div className="relative bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
        {/* Badge */}
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-black text-xs font-bold px-4 py-1 rounded-full">
            EARLY ADOPTER PRICING
          </span>
        </div>

        {/* Header */}
        <div className="text-center mb-6 pt-4">
          <h2 className="text-2xl font-bold text-white mb-2">
            You've hit your monthly limit
          </h2>
          <p className="text-gray-400">
            You saved approximately <span className="text-green-400 font-semibold">1.5 hours</span> of manual work
          </p>
        </div>

        {/* Pricing */}
        <div className="bg-[#0d0d0d] rounded-xl p-6 mb-6 border border-[#2a2a2a]">
          <div className="flex items-baseline justify-center gap-2 mb-2">
            <span className="text-gray-500 line-through text-lg">${PRICE_FUTURE}</span>
            <span className="text-4xl font-bold text-white">${PRICE_MONTHLY}</span>
            <span className="text-gray-400">/month</span>
          </div>
          <p className="text-center text-gray-500 text-sm">
            Lock in this price forever • Cancel anytime
          </p>
        </div>

        {/* Features */}
        <ul className="space-y-3 mb-6">
          {[
            'Unlimited blueprint processing',
            'AS9102 Form 3 Excel exports',
            'Permanent history storage',
            'Priority processing',
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
        <form onSubmit={handleUpgrade} className="space-y-4">
          <div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full bg-[#0d0d0d] border border-[#2a2a2a] rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#E63946] transition-colors"
              required
            />
          </div>

          {error && (
            <p className="text-red-500 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#E63946] hover:bg-[#c62d39] text-white font-bold py-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Processing...
              </span>
            ) : (
              'Upgrade to Pro'
            )}
          </button>
        </form>

        {/* Login link */}
        <p className="text-center text-gray-500 mt-4 text-sm">
          Already have an account?{' '}
          <button
            onClick={onLoginClick}
            className="text-[#E63946] hover:underline"
          >
            Log in
          </button>
        </p>

        {/* Security note */}
        <p className="text-center text-gray-600 mt-4 text-xs flex items-center justify-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Secured by Paystack • 256-bit encryption
        </p>
      </div>
    </div>
  );
}
