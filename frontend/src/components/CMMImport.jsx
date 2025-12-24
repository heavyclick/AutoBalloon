/**
 * CMM Import Component
 * Allows users to upload CMM measurement CSV and auto-match to balloons
 */

import React, { useState, useRef } from 'react';

export function CMMImport({ dimensions, onResultsImported }) {
  const [isOpen, setIsOpen] = useState(false);
  const [csvData, setCsvData] = useState(null);
  const [mappings, setMappings] = useState([]);
  const [importedResults, setImportedResults] = useState({});
  const fileInputRef = useRef(null);

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    const data = [];
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row = {};
      headers.forEach((header, idx) => {
        row[header] = values[idx] || '';
      });
      data.push(row);
    }
    return { headers, data };
  };

  const findBestMatch = (cmmFeature, dimensions) => {
    // Try to match by feature number, name, or nominal value
    const featureNum = cmmFeature.feature || cmmFeature.id || cmmFeature['feature #'] || cmmFeature['feature number'];
    const nominal = cmmFeature.nominal || cmmFeature['nominal value'] || cmmFeature.nom;
    
    // First try exact feature number match
    if (featureNum) {
      const numMatch = dimensions.find(d => d.id.toString() === featureNum.toString());
      if (numMatch) return numMatch;
    }
    
    // Then try nominal value match
    if (nominal) {
      const nominalNum = parseFloat(nominal);
      const nomMatch = dimensions.find(d => {
        const dimValue = parseFloat(d.value.replace(/[^\d.-]/g, ''));
        return Math.abs(dimValue - nominalNum) < 0.001;
      });
      if (nomMatch) return nomMatch;
    }
    
    return null;
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      const parsed = parseCSV(text);
      setCsvData(parsed);
      
      // Auto-map CMM features to balloons
      const autoMappings = parsed.data.map((row, idx) => {
        const match = findBestMatch(row, dimensions);
        return {
          cmmIndex: idx,
          cmmData: row,
          matchedBalloon: match ? match.id : null,
          actualValue: row.actual || row.measured || row['actual value'] || row.result || '',
          deviation: row.deviation || row.dev || '',
          status: row.status || (row.pass === 'true' || row.pass === '1' ? 'PASS' : row.pass === 'false' || row.pass === '0' ? 'FAIL' : ''),
        };
      });
      
      setMappings(autoMappings);
    };
    reader.readAsText(file);
  };

  const handleMappingChange = (cmmIndex, balloonId) => {
    setMappings(prev => prev.map((m, idx) => 
      idx === cmmIndex ? { ...m, matchedBalloon: balloonId ? parseInt(balloonId) : null } : m
    ));
  };

  const handleImport = () => {
    const results = {};
    mappings.forEach(m => {
      if (m.matchedBalloon) {
        results[m.matchedBalloon] = {
          actual: m.actualValue,
          deviation: m.deviation,
          status: m.status,
        };
      }
    });
    
    setImportedResults(results);
    onResultsImported(results);
    setIsOpen(false);
  };

  const matchedCount = mappings.filter(m => m.matchedBalloon).length;

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-[#1a1a1a] hover:bg-[#252525] text-gray-300 rounded-lg transition-colors text-sm flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Import CMM
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Import CMM Results</h2>
            <p className="text-gray-400 text-sm">Upload your CMM measurement CSV to auto-fill results</p>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-white">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {!csvData ? (
            <div 
              className="border-2 border-dashed border-[#2a2a2a] rounded-xl p-12 text-center cursor-pointer hover:border-[#3a3a3a]"
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
              />
              <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-white font-medium mb-2">Upload CMM CSV File</p>
              <p className="text-gray-500 text-sm">Supports standard CMM export formats</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <span className="text-green-500 font-medium">{matchedCount} of {mappings.length} matched</span>
                  <button 
                    onClick={() => { setCsvData(null); setMappings([]); }}
                    className="text-gray-400 hover:text-white text-sm"
                  >
                    Upload different file
                  </button>
                </div>
              </div>

              <div className="bg-[#0a0a0a] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[#1a1a1a]">
                    <tr>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">CMM Feature</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Actual Value</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Match to Balloon</th>
                      <th className="px-4 py-3 text-left text-gray-400 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mappings.map((mapping, idx) => (
                      <tr key={idx} className="border-t border-[#1a1a1a]">
                        <td className="px-4 py-3 text-white">
                          {mapping.cmmData.feature || mapping.cmmData.id || mapping.cmmData['feature #'] || `Row ${idx + 1}`}
                        </td>
                        <td className="px-4 py-3 text-white font-mono">
                          {mapping.actualValue || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={mapping.matchedBalloon || ''}
                            onChange={(e) => handleMappingChange(idx, e.target.value)}
                            className="bg-[#1a1a1a] border border-[#2a2a2a] rounded px-2 py-1 text-white text-sm"
                          >
                            <option value="">No match</option>
                            {dimensions.map(d => (
                              <option key={d.id} value={d.id}>
                                #{d.id} - {d.value}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          {mapping.status && (
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              mapping.status === 'PASS' ? 'bg-green-500/20 text-green-400' : 
                              mapping.status === 'FAIL' ? 'bg-red-500/20 text-red-400' : 
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {mapping.status}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {csvData && (
          <div className="px-6 py-4 border-t border-[#2a2a2a] flex justify-end gap-3">
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={matchedCount === 0}
              className="px-6 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg disabled:opacity-50"
            >
              Import {matchedCount} Results
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
