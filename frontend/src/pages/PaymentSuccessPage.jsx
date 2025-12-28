/**
 * PaymentSuccess Page - Fixed Race Condition
 * Handles the redirect after successful payment.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useGuestSession } from '../context/GuestSessionContext';
import { API_BASE_URL } from '../constants/config';

export function PaymentSuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refreshUser } = useAuth();
  const { sessionData, clearSession } = useGuestSession();
  
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'downloading', 'error'
  const [error, setError] = useState(null);

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    handlePaymentSuccess();
  }, []);

  const handlePaymentSuccess = async () => {
    try {
      // 1. Refresh user data to get updated payment status
      await refreshUser();
      
      setStatus('success');
      
      // FIX: Read directly from localStorage to avoid Context race condition
      let dataToDownload = sessionData;
      
      if (!dataToDownload) {
        try {
          const local = localStorage.getItem('autoballoon_guest_session_data');
          if (local) {
            dataToDownload = JSON.parse(local);
            console.log("Recovered session from localStorage");
          }
        } catch(e) {
          console.error("Local storage parse error", e);
        }
      }

      // 2. If we found data, trigger download
      if (dataToDownload && dataToDownload.dimensions?.length > 0) {
        setStatus('downloading');
        await downloadExcelWithData(dataToDownload);
      } 
      // 3. Only try backend if local failed
      else if (sessionId) {
        console.log("No local data, trying backend fetch...");
        setStatus('downloading');
        await fetchAndDownload(sessionId);
      }
      
      // 4. Clear guest session
      clearSession();
      
      // 5. Redirect to editor after brief delay
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 3000);
      
    } catch (err) {
      console.error('Error processing payment success:', err);
      setError(err.message);
      setStatus('error');
    }
  };

  const fetchAndDownload = async (sid) => {
    try {
      const response = await fetch(`${API_BASE_URL}/guest-session/retrieve/${sid}`);
      const data = await response.json();
      
      if (data.success && data.data) {
        await downloadExcelWithData(data.data);
      } else {
        console.error("Backend retrieve failed:", data.message);
      }
    } catch (err) {
      console.error('Failed to fetch session:', err);
    }
  };

  const downloadExcelWithData = async (data) => {
    try {
      const response = await fetch(`${API_BASE_URL}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: 'xlsx',
          template: 'AS9102_FORM3',
          dimensions: data.dimensions,
          total_pages: data.totalPages || 1,
          grid_detected: true,
          filename: data.filename || 'inspection'
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.filename || 'inspection'}_AS9102.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        console.error("Export endpoint failed", response.status);
      }
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0d0d] flex items-center justify-center p-4">
      <div className="bg-[#161616] border border-[#2a2a2a] rounded-2xl p-8 max-w-md w-full text-center">
        {status === 'verifying' && (
          <>
            <div className="w-16 h-16 mx-auto mb-6">
              <svg className="animate-spin w-full h-full text-[#E63946]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Verifying Payment...</h1>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-green-500/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Payment Successful!</h1>
          </>
        )}

        {status === 'downloading' && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 bg-[#E63946]/10 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-[#E63946] animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Downloading File...</h1>
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
