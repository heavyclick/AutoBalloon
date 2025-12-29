/**
 * PaywallModal Component
 * The "trap" modal that appears when user hits free limit
 * Cannot be dismissed - must upgrade or login
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL, PRICE_MONTHLY, PRICE_FUTURE } from '../constants/config';

export function PaywallModal({ isOpen, onLoginClick, initialEmail = '', hideLoginLink = false }) {
  const { isPro } = useAuth();
  const [email, setEmail] = useState(initialEmail);
  const [selectedPlan, setSelectedPlan] = useState('pro_monthly');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialEmail) setEmail(initialEmail);
  }, [initialEmail]);

  if (!isOpen || isPro) return null;

  const handleProceedToCheckout = async (plan) => {
    if (!email) {
      setError('Please enter your email to continue');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSelectedPlan(plan);

    try {
      const response = await fetch(`${API_BASE_URL}/payments/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          plan_type: plan,
          callback_url: `${window.location.origin}/success`,
        }),
      });

      const data = await response.json();

      if (data.success && data.checkout_url) {
        // LemonSqueezy redirect
        window.location.href = data.checkout_url;
      } else {
        setError(data.message || 'Failed to initialize payment. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const PlanCard = ({ id, title, price, period, features, badge, onSelect, isSelected }) => (
    <div 
      onClick={() => onSelect(id)}
      className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all ${
        isSelected ? 'border-[#E63946] bg-[#E63946]/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a] bg-[#0d0d0d]'
      }`}
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-max">
          <span className="bg-gradient-to-r from-amber-500 to-orange-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-full">
            {badge}
          </span>
        </div>
      )}
      <div className="text-center mb-3 mt-1">
        <h3 className="text-white font-bold">{title}</h3>
        <div className="text-2xl font-bold text-white mt-1">{price}</div>
        <div className="text-gray-500 text-xs">{period}</div>
      </div>
      <ul className="space-y-2 text-xs text-gray-400 mb-4">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2">
            <svg className="w-3 h-3 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {f}
          </li>
        ))}
      </ul>
      <button
        onClick={(e) => { e.stopPropagation(); handleProceedToCheckout(id); }}
        className={`w-full py-2 rounded-lg text-sm font-bold transition-colors ${
          isSelected ? 'bg-[#E63946] text-white hover:bg-[#d32f3d]' : 'bg-[#2a2a2a] text-gray-300'
        }`}
      >
        {isLoading && isSelected ? 'Processing...' : (id === 'pass_24h' ? 'Buy Pass' : 'Subscribe')}
      </button>
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/90 backdrop-blur-sm" />
      
      <div className="relative bg-[#161616] border border-[#2a2a2a] rounded-2xl p-6 max-w-4xl w-full shadow-2xl overflow-y-auto max-h-[90vh]">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">Subscription Required</h2>
          <p className="text-gray-400 text-sm">Choose a plan to access AutoBalloon</p>
        </div>

        {/* Email Input */}
        <div className="max-w-md mx-auto mb-8">
          <label className="block text-gray-400 text-xs mb-2 uppercase tracking-wide font-bold">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@company.com"
            className="w-full bg-[#0d0d0d] border border-[#2a2a2a] rounded-lg px-4 py-3 text-white focus:border-[#E63946] outline-none transition-colors"
          />
          {error && <p className="text-red-500 text-sm mt-2 text-center">{error}</p>}
        </div>

        {/* Plan Grid */}
        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <PlanCard
            id="pass_24h"
            title="24-Hour Pass"
            price="$49"
            period="One-time"
            features={["24 hours access", "Unlimited exports", "No auto-renewal"]}
            isSelected={selectedPlan === 'pass_24h'}
            onSelect={setSelectedPlan}
          />
          <PlanCard
            id="pro_monthly"
            title="Pro Monthly"
            price="$99"
            period="per month"
            features={["Unlimited access", "Priority queue", "Cancel anytime"]}
            badge="POPULAR"
            isSelected={selectedPlan === 'pro_monthly'}
            onSelect={setSelectedPlan}
          />
          <PlanCard
            id="pro_yearly"
            title="Pro Yearly"
            price="$990"
            period="per year"
            features={["2 months free", "All Pro features", "Best value"]}
            badge="SAVE $198"
            isSelected={selectedPlan === 'pro_yearly'}
            onSelect={setSelectedPlan}
          />
        </div>

        {/* Login Link - Hidden on Login Page */}
        {!hideLoginLink && (
          <p className="text-center text-gray-500 mt-6 text-sm">
            Already have an active account? <button onClick={onLoginClick} className="text-[#E63946] hover:underline">Log in</button>
          </p>
        )}
        
         {/* Security note */}
        <p className="text-center text-gray-600 mt-6 text-xs flex items-center justify-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Secured by LemonSqueezy • 256-bit encryption
        </p>
      </div>
    </div>
  );
}
