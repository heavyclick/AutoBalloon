/**
 * TemplateUploadModal.jsx
 * Modal for uploading and managing custom Excel templates
 * Shows available tokens for template creation
 */

import React, { useState, useRef } from 'react';

// Available tokens that can be used in templates
const TOKEN_REFERENCE = {
  metadata: [
    { token: '{{part_number}}', description: 'Part number from export metadata' },
    { token: '{{part_name}}', description: 'Part name from export metadata' },
    { token: '{{revision}}', description: 'Revision level' },
    { token: '{{serial_number}}', description: 'Serial number' },
    { token: '{{fai_report_number}}', description: 'FAI report number' },
    { token: '{{date}}', description: 'Current date (YYYY-MM-DD)' },
  ],
  dimensions: [
    { token: '{{dim.id}}', description: 'Dimension/characteristic number' },
    { token: '{{dim.zone}}', description: 'Zone reference (e.g., A1, B2)' },
    { token: '{{dim.value}}', description: 'Dimension value/requirement' },
    { token: '{{dim.actual}}', description: 'Actual measured value' },
    { token: '{{dim.min}}', description: 'Minimum limit' },
    { token: '{{dim.max}}', description: 'Maximum limit' },
    { token: '{{dim.method}}', description: 'Inspection method' },
    { token: '{{dim.class}}', description: 'Classification (Critical, Major, Minor)' },
  ],
  bom: [
    { token: '{{bom.part_number}}', description: 'BOM item part number' },
    { token: '{{bom.part_name}}', description: 'BOM item part name' },
    { token: '{{bom.qty}}', description: 'BOM item quantity' },
  ],
  specifications: [
    { token: '{{spec.process}}', description: 'Process/material name' },
    { token: '{{spec.spec_number}}', description: 'Specification number' },
  ],
};

export function TemplateUploadModal({ onClose, onUpload, visitorId, userEmail, existingTemplates, onDeleteTemplate }) {
  const [templateName, setTemplateName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'manage' or 'tokens'
  const [deletingId, setDeletingId] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.xlsx')) {
        setError('Only .xlsx files are allowed');
        return;
      }
      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB');
        return;
      }
      setSelectedFile(file);
      setError(null);
      // Auto-fill template name from filename
      if (!templateName) {
        setTemplateName(file.name.replace('.xlsx', ''));
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !templateName.trim()) {
      setError('Please provide a template name and select a file');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('name', templateName.trim());

      const response = await fetch(`${API_BASE_URL}/templates/upload`, {
        method: 'POST',
        headers: {
          'X-Visitor-ID': visitorId || '',
          'X-User-Email': userEmail || ''
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok && data.success) {
        onUpload(data.template);
        setSelectedFile(null);
        setTemplateName('');
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        setError(data.detail || data.message || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Network error. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (templateId) => {
    setDeletingId(templateId);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
        method: 'DELETE',
        headers: {
          'X-Visitor-ID': visitorId || '',
          'X-User-Email': userEmail || ''
        }
      });

      if (response.ok) {
        onDeleteTemplate(templateId);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete template');
      }
    } catch (err) {
      console.error('Delete error:', err);
      setError('Network error. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownload = async (templateId, templateName) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const response = await fetch(`${API_BASE_URL}/templates/${templateId}/download`, {
        headers: {
          'X-Visitor-ID': visitorId || '',
          'X-User-Email': userEmail || ''
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${templateName}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      }
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Custom Templates</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-4 flex gap-1 border-b border-[#2a2a2a]">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'upload'
                ? 'bg-[#252525] text-white border-b-2 border-[#E63946]'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Upload New
          </button>
          <button
            onClick={() => setActiveTab('manage')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'manage'
                ? 'bg-[#252525] text-white border-b-2 border-[#E63946]'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            My Templates ({existingTemplates.length})
          </button>
          <button
            onClick={() => setActiveTab('tokens')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'tokens'
                ? 'bg-[#252525] text-white border-b-2 border-[#E63946]'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Token Reference
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Template Name</label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="e.g., My Company FAI Report"
                  className="w-full px-4 py-3 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg text-white focus:outline-none focus:border-[#E63946]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Template File (.xlsx)</label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    selectedFile
                      ? 'border-green-500/50 bg-green-500/5'
                      : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div className="flex items-center justify-center gap-3">
                      <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <div className="text-left">
                        <p className="text-white font-medium">{selectedFile.name}</p>
                        <p className="text-gray-400 text-sm">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                  ) : (
                    <>
                      <svg className="w-10 h-10 text-gray-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="text-gray-400">Click to select or drag & drop</p>
                      <p className="text-gray-500 text-sm mt-1">Excel (.xlsx) only, max 5MB</p>
                    </>
                  )}
                </div>
              </div>

              <div className="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg p-4">
                <h4 className="text-sm font-medium text-white mb-2">How to create a template:</h4>
                <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
                  <li>Create an Excel file with your desired layout</li>
                  <li>Add placeholders like {"{{part_number}}"} where you want data</li>
                  <li>For repeating data, use {"{{dim.id}}"}, {"{{dim.value}}"} etc. in a row</li>
                  <li>Upload the file here</li>
                </ol>
              </div>

              <button
                onClick={handleUpload}
                disabled={!selectedFile || !templateName.trim() || isUploading}
                className="w-full py-3 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Upload Template
                  </>
                )}
              </button>
            </div>
          )}

          {/* Manage Tab */}
          {activeTab === 'manage' && (
            <div className="space-y-3">
              {existingTemplates.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="w-12 h-12 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-gray-400">No custom templates yet</p>
                  <p className="text-gray-500 text-sm mt-1">Upload your first template to get started</p>
                </div>
              ) : (
                existingTemplates.map(template => (
                  <div
                    key={template.id}
                    className="flex items-center justify-between p-4 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="text-white font-medium">{template.name}</p>
                      <p className="text-gray-500 text-sm">
                        {template.file_size ? `${(template.file_size / 1024).toFixed(1)} KB` : 'Unknown size'}
                        {template.created_at && ` - Created ${new Date(template.created_at).toLocaleDateString()}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDownload(template.id, template.name)}
                        className="p-2 text-gray-400 hover:text-white transition-colors"
                        title="Download"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(template.id)}
                        disabled={deletingId === template.id}
                        className="p-2 text-gray-400 hover:text-red-400 transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        {deletingId === template.id ? (
                          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Token Reference Tab */}
          {activeTab === 'tokens' && (
            <div className="space-y-6">
              <p className="text-gray-400 text-sm">
                Use these placeholders in your Excel template. They will be automatically replaced with data during export.
              </p>

              {Object.entries(TOKEN_REFERENCE).map(([category, tokens]) => (
                <div key={category}>
                  <h4 className="text-white font-medium capitalize mb-3">{category}</h4>
                  <div className="bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[#2a2a2a]">
                          <th className="text-left px-4 py-2 text-gray-400 font-medium">Token</th>
                          <th className="text-left px-4 py-2 text-gray-400 font-medium">Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tokens.map((t, i) => (
                          <tr key={i} className="border-b border-[#2a2a2a] last:border-0">
                            <td className="px-4 py-2">
                              <code className="text-[#E63946] bg-[#E63946]/10 px-2 py-0.5 rounded text-xs">
                                {t.token}
                              </code>
                            </td>
                            <td className="px-4 py-2 text-gray-300">{t.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {category === 'dimensions' && (
                    <p className="text-gray-500 text-xs mt-2">
                      * Place dimension tokens in a single row. The row will be duplicated for each dimension.
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#2a2a2a] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default TemplateUploadModal;
