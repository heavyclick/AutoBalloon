/**
 * DownloadMenu.jsx
 * Export dropdown menu for PDF, ZIP, and Excel formats
 */

import React, { useState, useEffect, useRef } from 'react';

export function DownloadMenu({ onDownloadPDF, onDownloadZIP, onDownloadExcel, isDownloading, totalPages, totalDimensions, isPro }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = (action) => {
    action();
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isDownloading}
        className="flex items-center gap-2 px-4 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg transition-colors disabled:opacity-50"
      >
        {isDownloading ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : !isPro ? (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        )}
        <span>{isDownloading ? 'Preparing...' : (isPro ? 'Download' : 'Export (Pro)')}</span>
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && !isDownloading && (
        <div className="absolute right-0 mt-2 w-72 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl shadow-2xl overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-[#2a2a2a] bg-[#161616]">
            <p className="text-sm font-medium text-white">Export Options</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {totalPages} page{totalPages !== 1 ? 's' : ''} • {totalDimensions} dimension{totalDimensions !== 1 ? 's' : ''}
            </p>
          </div>

          <div className="p-2">
            <button
              onClick={() => handleDownload(onDownloadPDF)}
              className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] transition-colors text-left group"
            >
              <div className="p-2 rounded-lg bg-[#E63946]/10 text-[#E63946] group-hover:bg-[#E63946]/20">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">Ballooned PDF</p>
                <p className="text-xs text-gray-400 mt-0.5">All pages with balloon markers</p>
              </div>
              {!isPro && (
                <svg className="w-4 h-4 text-gray-500 self-center" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => handleDownload(onDownloadZIP)}
              className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] transition-colors text-left group"
            >
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">FAI Package (ZIP)</p>
                <p className="text-xs text-gray-400 mt-0.5">Images + AS9102 Excel + README</p>
              </div>
              {isPro ? (
                <span className="text-[10px] font-medium text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full self-center">
                  RECOMMENDED
                </span>
              ) : (
                <svg className="w-4 h-4 text-gray-500 self-center" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => handleDownload(onDownloadExcel)}
              className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] transition-colors text-left group"
            >
              <div className="p-2 rounded-lg bg-green-500/10 text-green-400 group-hover:bg-green-500/20">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">AS9102 Excel Only</p>
                <p className="text-xs text-gray-400 mt-0.5">Form 3 spreadsheet</p>
              </div>
              {!isPro && (
                <svg className="w-4 h-4 text-gray-500 self-center" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              )}
            </button>
          </div>

          <div className="px-4 py-2.5 border-t border-[#2a2a2a] bg-[#0a0a0a]">
            <p className="text-[11px] text-gray-500">
              {isPro ? 'All exports include AS9102 Rev C compliant formatting' : 'Upgrade to Pro to unlock exports'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
