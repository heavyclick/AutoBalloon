/**
 * Verify Page
 * Handles magic link verification and auto-login
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../constants/config';

export function VerifyPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setError('Invalid login link. Please request a new one.');
      return;
    }

    verifyToken(token);
  }, [searchParams]);

  const verifyToken = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      const data = await response.json();

      if (data.success && data.access_token) {
        // Login successful
        login(data.access_token, data.user);
        setStatus('success');
        
        // Redirect to home after a brief delay
        setTimeout(() => {
          navigate('/');
        }, 1500);
      } else {
        setStatus('error');
        setError(data.message || 'Invalid or expired login link.');
      }
    } catch (err) {
      setStatus('error');
      setError('Network error. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {status === 'verifying' && (
          <>
            <div className="w-16 h-16 border-4 border-[#E63946] border-t-transparent rounded-full animate-spin mx-auto mb-6" />
            <h1 className="text-2xl font-bold text-white mb-2">
              Verifying...
            </h1>
            <p className="text-gray-400">
              Please wait while we sign you in.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              You're in!
            </h1>
            <p className="text-gray-400">
              Redirecting you to AutoBalloon...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">
              Link expired
            </h1>
            <p className="text-gray-400 mb-8">
              {error}
            </p>
            <Link
              to="/login"
              className="inline-block bg-[#E63946] hover:bg-[#c62d39] text-white font-bold px-6 py-3 rounded-lg transition-colors"
            >
              Request new link
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
