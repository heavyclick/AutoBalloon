/**
 * PageNavigator.jsx
 * Multi-page navigation controls for blueprints
 */

import React from 'react';

export function PageNavigator({ currentPage, totalPages, onPageChange, gridDetected }) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 bg-[#1a1a1a] rounded-lg px-3 py-2">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span className="text-sm text-gray-300">
          Page{' '}
          <select
            value={currentPage}
            onChange={(e) => onPageChange(Number(e.target.value))}
            className="bg-transparent text-white font-medium appearance-none cursor-pointer hover:text-[#E63946] transition-colors"
          >
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <option key={page} value={page} className="bg-[#1a1a1a]">{page}</option>
            ))}
          </select>
          <span className="text-gray-500"> of {totalPages}</span>
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage <= 1}
          className="p-2 rounded-lg bg-[#1a1a1a] text-gray-300 hover:bg-[#252525] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage >= totalPages}
          className="p-2 rounded-lg bg-[#1a1a1a] text-gray-300 hover:bg-[#252525] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {gridDetected === false && (
        <div className="flex items-center gap-1.5 text-xs text-amber-400/80 bg-amber-400/10 px-3 py-1.5 rounded-lg">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>Standard grid</span>
        </div>
      )}
    </div>
  );
}
