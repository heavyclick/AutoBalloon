/**
 * Success Page
 * Shown after successful Paystack payment
 * Verifies payment and logs user in
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../constants/config';

export function SuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login, refreshUser } = useAuth();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [error, setError] = useState(null);

  useEffect(() => {
    const reference = searchParams.get('reference') || searchParams.get('trxref');
    
    if (reference) {
      verifyPayment(reference);
    } else {
      // No reference - might be direct navigation
      // Check if user is logged in and pro
      refreshUser().then(user => {
        if (user?.is_pro) {
          setStatus('success');
        } else {
          setStatus('error');
          setError('Payment reference not found.');
        }
      });
    }
  }, [searchParams]);

  const verifyPayment = async (reference) => {
    try {
      const response = await fetch(`${API_BASE_URL}/payments/verify/${reference}`);
      const data = await response.json();

      if (data.success) {
        // If we got a token, log in
        if (data.access_token && data.user) {
          login(data.access_token, data.user);
        } else {
          // Just refresh user state
          await refreshUser();
        }
        setStatus('success');
      } else {
        setStatus('error');
        setError(data.message || 'Payment verification failed.');
      }
    } catch (err) {
      setStatus('error');
      setError('Network error. Please contact support.');
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {status === 'verifying' && (
          <>
            <div className="w-16 h-16 border-4 border-[#E63946] border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h1 className="text-2xl font-bold text-white mb-2">
              Confirming payment...
            </h1>
            <p className="text-gray-400">
              Please wait while we activate your Pro account.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            {/* Celebration animation */}
            <div className="relative w-32 h-32 mx-auto mb-8">
              <div className="absolute inset-0 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full animate-pulse" />
              <div className="absolute inset-2 bg-[#0d0d0d] rounded-full flex items-center justify-center">
                <span className="text-5xl">🎉</span>
              </div>
            </div>

            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-black font-bold px-4 py-2 rounded-full mb-6">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              PRO ACTIVATED
            </div>

            <h1 className="text-3xl font-bold text-white mb-4">
              Welcome to Pro!
            </h1>
            <p className="text-gray-400 mb-8">
              Your Early Adopter pricing is now locked in forever.
              <br />
              Check your email for a login link.
            </p>

            {/* Features unlocked */}
            <div className="bg-[#161616] border border-[#2a2a2a] rounded-xl p-6 mb-8 text-left">
              <h3 className="text-sm font-bold text-gray-400 mb-4">UNLOCKED</h3>
              <ul className="space-y-3">
                {[
                  'Unlimited blueprint processing',
                  'AS9102 Form 3 exports',
                  'Permanent cloud history',
                  'Priority support',
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-white">
                    <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <Link
              to="/"
              className="inline-block bg-[#E63946] hover:bg-[#c62d39] text-white font-bold px-8 py-4 rounded-lg transition-colors"
            >
              Start Processing Blueprints →
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              Something went wrong
            </h1>
            <p className="text-gray-400 mb-8">
              {error}
            </p>
            <div className="space-y-4">
              <a
                href="mailto:support@autoballoon.space"
                className="inline-block bg-[#E63946] hover:bg-[#c62d39] text-white font-bold px-6 py-3 rounded-lg transition-colors"
              >
                Contact Support
              </a>
              <Link
                to="/"
                className="block text-gray-400 hover:text-white transition-colors"
              >
                ← Back to home
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
