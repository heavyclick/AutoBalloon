/**
 * DownloadMenu.jsx
 * Export dropdown menu for PDF, ZIP, and Excel formats
 * Supports multiple export templates: AS9102, PPAP, ISO 13485, Custom
 */

import React, { useState, useEffect, useRef } from 'react';
import { TemplateUploadModal } from './TemplateUploadModal';

// Built-in template options
const TEMPLATE_OPTIONS = [
  { id: 'AS9102', name: 'AS9102 Rev C', description: 'Aerospace FAI 3-Form Workbook' },
  { id: 'PPAP', name: 'PPAP', description: 'Production Part Approval Process' },
  { id: 'ISO13485', name: 'ISO 13485', description: 'Medical Devices QMS' },
  { id: 'CUSTOM', name: 'Custom Template', description: 'Use your own template' },
];

export function DownloadMenu({ onDownloadPDF, onDownloadZIP, onDownloadExcel, isDownloading, totalPages, totalDimensions, isPro, visitorId, userEmail }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('AS9102');
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [customTemplates, setCustomTemplates] = useState([]);
  const [selectedCustomTemplate, setSelectedCustomTemplate] = useState(null);
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

  // Fetch user's custom templates when menu opens
  useEffect(() => {
    if (isOpen && (visitorId || userEmail)) {
      fetchCustomTemplates();
    }
  }, [isOpen, visitorId, userEmail]);

  const fetchCustomTemplates = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const response = await fetch(`${API_BASE_URL}/templates/list`, {
        headers: {
          'X-Visitor-ID': visitorId || '',
          'X-User-Email': userEmail || ''
        }
      });
      if (response.ok) {
        const data = await response.json();
        setCustomTemplates(data.templates || []);
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    }
  };

  const handleDownload = (action, templateName = null) => {
    const templateToUse = templateName || (selectedTemplate === 'CUSTOM' ? selectedCustomTemplate : selectedTemplate);
    action(templateToUse);
    setIsOpen(false);
  };

  const handleTemplateUploaded = (template) => {
    setCustomTemplates(prev => [...prev, template]);
    setSelectedCustomTemplate(template.id);
    setSelectedTemplate('CUSTOM');
    setShowTemplateModal(false);
  };

  return (
    <>
      {/* Template Upload Modal */}
      {showTemplateModal && (
        <TemplateUploadModal
          onClose={() => setShowTemplateModal(false)}
          onUpload={handleTemplateUploaded}
          visitorId={visitorId}
          userEmail={userEmail}
          existingTemplates={customTemplates}
          onDeleteTemplate={(id) => setCustomTemplates(prev => prev.filter(t => t.id !== id))}
        />
      )}

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
          <div className="absolute right-0 mt-2 w-80 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl shadow-2xl overflow-hidden z-50">
            <div className="px-4 py-3 border-b border-[#2a2a2a] bg-[#161616]">
              <p className="text-sm font-medium text-white">Export Options</p>
              <p className="text-xs text-gray-400 mt-0.5">
                {totalPages} page{totalPages !== 1 ? 's' : ''} - {totalDimensions} dimension{totalDimensions !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Template Selector */}
            <div className="px-4 py-3 border-b border-[#2a2a2a]">
              <label className="block text-xs font-medium text-gray-400 mb-2">Excel Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => {
                  setSelectedTemplate(e.target.value);
                  if (e.target.value !== 'CUSTOM') {
                    setSelectedCustomTemplate(null);
                  }
                }}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg text-white text-sm focus:outline-none focus:border-[#E63946]"
              >
                {TEMPLATE_OPTIONS.map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.name} - {opt.description}</option>
                ))}
              </select>

              {/* Custom Template Sub-Options */}
              {selectedTemplate === 'CUSTOM' && (
                <div className="mt-3 space-y-2">
                  {customTemplates.length > 0 && (
                    <select
                      value={selectedCustomTemplate || ''}
                      onChange={(e) => setSelectedCustomTemplate(e.target.value)}
                      className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg text-white text-sm focus:outline-none focus:border-[#E63946]"
                    >
                      <option value="">Select a saved template...</option>
                      {customTemplates.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  )}
                  <button
                    onClick={() => setShowTemplateModal(true)}
                    className="w-full px-3 py-2 bg-[#252525] hover:bg-[#333] border border-[#2a2a2a] rounded-lg text-gray-300 text-sm flex items-center justify-center gap-2 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {customTemplates.length > 0 ? 'Manage Templates' : 'Upload Template'}
                  </button>
                </div>
              )}
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
                  <p className="text-xs text-gray-400 mt-0.5">Images + {selectedTemplate !== 'CUSTOM' ? TEMPLATE_OPTIONS.find(t => t.id === selectedTemplate)?.name : 'Custom'} Excel</p>
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
                disabled={selectedTemplate === 'CUSTOM' && !selectedCustomTemplate}
                className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] transition-colors text-left group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="p-2 rounded-lg bg-green-500/10 text-green-400 group-hover:bg-green-500/20">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">
                    {selectedTemplate !== 'CUSTOM'
                      ? TEMPLATE_OPTIONS.find(t => t.id === selectedTemplate)?.name
                      : selectedCustomTemplate
                        ? customTemplates.find(t => t.id === selectedCustomTemplate)?.name || 'Custom Template'
                        : 'Select Template Above'
                    } Excel
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {selectedTemplate !== 'CUSTOM'
                      ? TEMPLATE_OPTIONS.find(t => t.id === selectedTemplate)?.description
                      : 'Your custom template'
                    }
                  </p>
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
                {isPro ? `Using ${TEMPLATE_OPTIONS.find(t => t.id === selectedTemplate)?.name || 'Custom'} template` : 'Upgrade to Pro to unlock exports'}
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
