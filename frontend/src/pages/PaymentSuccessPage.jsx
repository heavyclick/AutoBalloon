/**
 * PaymentSuccess Page - Auto-Login & Smart Download
 * Handles post-payment flow:
 * 1. Exchanges session_id for login token (auto-login)
 * 2. Auto-downloads the requested file (ZIP/PDF/Excel)
 * 3. Redirects to dashboard with Pro access WITHOUT clearing the file
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useGuestSession } from '../context/GuestSessionContext';
import { API_BASE_URL } from '../constants/config';

export function PaymentSuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  // Note: We access sessionData but intentionally do NOT use clearSession
  // so the user can land back on their work.
  const { sessionData } = useGuestSession();
  
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [restoredData, setRestoredData] = useState(null);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [message, setMessage] = useState('Verifying your payment...');
  const [autoRedirectTimer, setAutoRedirectTimer] = useState(null);

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (sessionId) {
      handlePostPaymentFlow();
    } else {
      setError('No session ID found.');
      setStatus('error');
    }
    
    // Cleanup timer on unmount
    return () => {
      if (autoRedirectTimer) clearTimeout(autoRedirectTimer);
    };
  }, [sessionId]);

  const handlePostPaymentFlow = async () => {
    try {
      // 1. Auto-Login: Exchange Session ID for JWT
      setMessage('Activating your account...');
      try {
        const authRes = await fetch(`${API_BASE_URL}/auth/exchange-session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId })
        });
        
        if (authRes.ok) {
          const authData = await authRes.json();
          // Log user in immediately!
          login(authData.access_token, authData.user);
          console.log("Auto-login successful");
        } else {
          console.warn("Auto-login skipped: Session not yet confirmed paid via webhook");
        }
      } catch (e) {
        console.warn("Auto-login error:", e);
      }

      // 2. Restore Data for Download
      setMessage('Preparing your files...');
      let data = sessionData;
      
      if (!data) {
        // Try localStorage backup
        const local = localStorage.getItem('autoballoon_guest_session_data');
        if (local) data = JSON.parse(local);
      }
      
      if (!data && sessionId) {
        // Try fetching from backend
        const res = await fetch(`${API_BASE_URL}/guest-session/retrieve/${sessionId}`);
        const json = await res.json();
        if (json.success && json.data) data = json.data;
      }

      if (data) {
        setRestoredData(data);
        setStatus('success');
        
        // 3. Auto-Download based on Preference
        const pref = localStorage.getItem('autoballoon_download_preference') || 'zip';
        setMessage(`Starting ${pref.toUpperCase()} download...`);
        
        // Trigger download automatically
        const downloadSuccess = await handleDownload(pref, data);
        
        if (downloadSuccess) {
          // CRITICAL CHANGE: We do NOT clear session here.
          // We want the data to persist so the user sees it when they land on dashboard.
          
          setMessage('Payment successful! Redirecting you back to your drawing...');
          
          // Redirect to dashboard after a short delay
          const timer = setTimeout(() => {
            navigate('/');
          }, 3000);
          setAutoRedirectTimer(timer);
        } else {
          setMessage('Auto-download prevented. Click a button below to download.');
        }
        
      } else {
        // Payment valid, but data gone (rare)
        setStatus('success');
        setMessage('Payment successful! Redirecting to dashboard...');
        setTimeout(() => navigate('/'), 3000);
      }
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
      setStatus('error');
    }
  };

  const handleDownload = async (type, dataOverride = null) => {
    const data = dataOverride || restoredData;
    if (!data) return false;
    
    setIsDownloading(true);

    try {
      let endpoint = '/export'; // Default
      let payload = {};
      let filename = data.filename || 'inspection';

      // Validate data before sending to prevent crashes
      if (!data.pages || data.pages.length === 0) {
        throw new Error("Drawing data is incomplete.");
      }

      if (type === 'pdf') {
        endpoint = '/download/pdf';
        filename += '_ballooned.pdf';
        payload = {
          pages: data.pages || [],
          part_name: filename
        };
      } else if (type === 'zip') {
        endpoint = '/download/zip';
        filename += '_bundle.zip';
        payload = {
          pages: data.pages || [],
          grid_detected: true
        };
      } else {
        // Excel
        endpoint = '/export';
        filename += '_AS9102.xlsx';
        payload = {
          format: 'xlsx',
          template: 'AS9102_FORM3',
          dimensions: data.dimensions,
          total_pages: data.totalPages || 1,
          grid_detected: true
        };
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        return true;
      } else {
        console.error("Download failed status:", response.status);
        return false;
      }
    } catch (e) {
      console.error("Download exception:", e);
      return false;
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center p-4">
      <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 max-w-md w-full text-center">
        
        {status === 'verifying' && (
          <div className="py-8">
            <div className="w-12 h-12 mx-auto mb-4 border-4 border-[#E63946] border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-xl font-bold text-white">Processing...</h2>
            <p className="text-gray-400 mt-2">{message}</p>
          </div>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-green-500/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            
            <h1 className="text-2xl font-bold text-white mb-2">Payment Successful!</h1>
            <p className="text-gray-400 mb-6">
              {message}
            </p>

            {restoredData ? (
              <div className="space-y-3">
                <p className="text-sm text-gray-500 uppercase tracking-wider font-bold mb-3">Download Again</p>
                
                <button
                  onClick={() => handleDownload('pdf')}
                  disabled={isDownloading}
                  className="w-full flex items-center justify-center gap-2 bg-[#2a2a2a] hover:bg-[#3a3a3a] text-white py-3 rounded-lg transition-colors font-medium border border-gray-700"
                >
                  <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  PDF
                </button>

                <button
                  onClick={() => handleDownload('excel')}
                  disabled={isDownloading}
                  className="w-full flex items-center justify-center gap-2 bg-[#2a2a2a] hover:bg-[#3a3a3a] text-white py-3 rounded-lg transition-colors font-medium border border-gray-700"
                >
                  <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Excel
                </button>

                <button
                  onClick={() => handleDownload('zip')}
                  disabled={isDownloading}
                  className="w-full flex items-center justify-center gap-2 bg-[#E63946] hover:bg-[#c62d39] text-white py-3 rounded-lg transition-colors font-bold shadow-lg shadow-red-900/20"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Bundle (ZIP)
                </button>
              </div>
            ) : null}

            <button
              onClick={() => navigate('/')}
              className="mt-6 text-gray-500 hover:text-white text-sm transition-colors"
            >
              Return to Dashboard
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-red-500/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Something Went Wrong</h1>
            <p className="text-gray-400 mb-4">{error}</p>
            <button onClick={() => navigate('/')} className="bg-[#E63946] px-6 py-2 rounded text-white">Dashboard</button>
          </>
        )}
      </div>
    </div>
  );
}
