/**
 * DimensionSidebar.jsx
 * Sliding sidebar that appears when a balloon is selected
 * Shows zoomed thumbnail and dimension properties
 */

import React, { useState, useEffect } from 'react';
import { cropDimensionImage } from '../utils/imageCropper';

export function DimensionSidebar({ dimension, blueprintImage, onClose, onUpdate }) {
  const [zoomedImage, setZoomedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (dimension && blueprintImage) {
      setIsLoading(true);
      cropDimensionImage(blueprintImage, dimension)
        .then(croppedImg => {
          setZoomedImage(croppedImg);
          setIsLoading(false);
        })
        .catch(error => {
          console.error('Failed to crop dimension image:', error);
          setIsLoading(false);
        });
    }
  }, [dimension, blueprintImage]);

  if (!dimension) return null;

  const getVal = (field, fallback = '') => {
    return dimension.parsed?.[field] ?? fallback;
  };

  return (
    <div className="h-full bg-[#161616] border-l border-[#2a2a2a] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-[#1a1a1a] border-b border-[#2a2a2a] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-[#E63946] flex items-center justify-center text-white font-bold text-sm">
            {dimension.id}
          </div>
          <h3 className="text-white font-medium">Dimension Detail</h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white transition-colors"
          title="Close sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Zoomed Image Section */}
        <div className="p-4 border-b border-[#2a2a2a]">
          <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
            Zoomed View
          </div>
          <div className="bg-[#0a0a0a] rounded-lg p-3 border border-[#2a2a2a]">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-8 h-8 border-2 border-[#E63946] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : zoomedImage ? (
              <img
                src={zoomedImage}
                alt={`Dimension ${dimension.id}`}
                className="w-full h-auto rounded"
                style={{ imageRendering: 'crisp-edges' }}
              />
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-600 text-sm">
                Failed to load image
              </div>
            )}
          </div>
        </div>

        {/* Properties Section */}
        <div className="p-4 space-y-4">
          {/* Basic Info */}
          <div>
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
              Basic Information
            </div>
            <div className="space-y-2">
              <PropertyRow label="Value" value={dimension.value} highlight />
              <PropertyRow label="Zone" value={dimension.zone || '—'} />
              <PropertyRow label="Page" value={dimension.page || 1} />
            </div>
          </div>

          {/* Tolerancing */}
          {dimension.parsed && (
            <div>
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                Tolerancing
              </div>
              <div className="space-y-2">
                <PropertyRow label="Nominal" value={getVal('nominal', 0).toFixed(4)} />
                <PropertyRow label="Units" value={getVal('units', 'in')} />
                <PropertyRow label="Type" value={getVal('tolerance_type', 'bilateral')} />
                <PropertyRow
                  label="Plus Tolerance"
                  value={`+${getVal('upper_tol', 0).toFixed(4)}`}
                  valueClass="text-green-400"
                />
                <PropertyRow
                  label="Minus Tolerance"
                  value={getVal('lower_tol', 0).toFixed(4)}
                  valueClass="text-red-400"
                />
              </div>
            </div>
          )}

          {/* Limits */}
          {dimension.parsed && (
            <div>
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                Specification Limits
              </div>
              <div className="space-y-2">
                <PropertyRow
                  label="Upper Limit (USL)"
                  value={getVal('max_limit', 0).toFixed(4)}
                  valueClass="text-green-400 font-mono"
                />
                <PropertyRow
                  label="Lower Limit (LSL)"
                  value={getVal('min_limit', 0).toFixed(4)}
                  valueClass="text-green-400 font-mono"
                />
              </div>
            </div>
          )}

          {/* ISO Fits */}
          {(getVal('hole_fit_class') || getVal('shaft_fit_class')) && (
            <div>
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                ISO 286 Fits
              </div>
              <div className="space-y-2">
                {getVal('hole_fit_class') && (
                  <PropertyRow label="Hole Fit" value={getVal('hole_fit_class')} valueClass="text-purple-400" />
                )}
                {getVal('shaft_fit_class') && (
                  <PropertyRow label="Shaft Fit" value={getVal('shaft_fit_class')} valueClass="text-purple-400" />
                )}
              </div>
            </div>
          )}

          {/* Inspection */}
          <div>
            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
              Inspection
            </div>
            <div className="space-y-2">
              <PropertyRow label="Method" value={getVal('inspection_method', '—')} valueClass="text-blue-400" />
              <PropertyRow label="Confidence" value={`${(dimension.confidence * 100).toFixed(1)}%`} />
            </div>
          </div>

          {/* Metadata */}
          {(getVal('chart_char_id') || getVal('view_name')) && (
            <div>
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">
                Metadata
              </div>
              <div className="space-y-2">
                {getVal('chart_char_id') && (
                  <PropertyRow label="Chart Char ID" value={getVal('chart_char_id')} />
                )}
                {getVal('view_name') && <PropertyRow label="View" value={getVal('view_name')} />}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="px-4 py-3 bg-[#1a1a1a] border-t border-[#2a2a2a] flex gap-2">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2 bg-[#2a2a2a] hover:bg-[#3a3a3a] text-white rounded-lg transition-colors text-sm font-medium"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function PropertyRow({ label, value, highlight = false, valueClass = '' }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-sm text-gray-400">{label}:</span>
      <span
        className={`text-sm font-medium ${
          highlight ? 'text-white font-mono bg-[#2a2a2a] px-2 py-0.5 rounded' : valueClass || 'text-gray-200'
        }`}
      >
        {value}
      </span>
    </div>
  );
}
