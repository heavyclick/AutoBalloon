import React, { useState, useRef } from 'react';
import { API_BASE_URL } from '../constants/config';
import { useAuth } from '../context/AuthContext';

export function CMMImportModal({ dimensions, onClose, onImport }) {
  const { token } = useAuth();
  const [step, setStep] = useState('upload'); // 'upload' | 'review'
  const [isUploading, setIsUploading] = useState(false);
  const [cmmFilename, setCmmFilename] = useState(null);
  const [mappings, setMappings] = useState([]); // { uuid, cmmData, matchedBalloonId, matchScore }
  const fileInputRef = useRef(null);

  // ===========================================================================
  // 1. INTELLIGENT MATCHING ENGINE (Your Logic)
  // ===========================================================================
  const calculateMatchScore = (cmmRow, dimension) => {
    let score = 0;
    const EPSILON = 0.002;

    // 1. Nominal Match (50 pts)
    const dimVal = parseFloat(dimension.value.replace(/[^\d.-]/g, ''));
    if (!isNaN(dimVal) && Math.abs(cmmRow.nominal - dimVal) <= EPSILON) {
      score += 50;
    }

    // 2. ID Match (30 pts)
    const cmmId = String(cmmRow.feature_id).replace(/[^0-9]/g, '');
    const dimId = String(dimension.id);
    if (cmmId && cmmId === dimId) score += 30;

    // 3. Tolerance Match (20 pts)
    if (dimension.parsed && cmmRow.plus_tol !== undefined) {
      const dimPlus = dimension.parsed.plus_tolerance || 0;
      const dimMinus = dimension.parsed.minus_tolerance || 0;
      if (Math.abs(cmmRow.plus_tol - dimPlus) < EPSILON && 
          Math.abs(Math.abs(cmmRow.minus_tol) - Math.abs(dimMinus)) < EPSILON) {
        score += 20;
      }
    }
    return score;
  };

  const performAutoMatch = (cmmRows, availableDimensions) => {
    return cmmRows.map((row, idx) => {
      let bestMatch = null;
      let maxScore = -1;

      availableDimensions.forEach(dim => {
        const score = calculateMatchScore(row, dim);
        if (score > maxScore) {
          maxScore = score;
          bestMatch = dim;
        }
      });

      // Threshold > 40 to auto-assign
      const finalMatch = (maxScore >= 40) ? bestMatch : null;

      return {
        uuid: `cmm-${idx}`,
        cmmData: row,
        matchedBalloonId: finalMatch ? finalMatch.id : '',
        matchScore: maxScore,
        manualOverride: false
      };
    });
  };

  // ===========================================================================
  // 2. HANDLERS
  // ===========================================================================
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/cmm/parse`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      });
      const data = await response.json();

      if (data.success && data.results) {
        setCmmFilename(file.name);
        const autoMapped = performAutoMatch(data.results, dimensions);
        setMappings(autoMapped);
        setStep('review');
      } else {
        alert(data.message || 'Failed to parse CMM file.');
      }
    } catch (err) {
      console.error(err);
      alert('Network error uploading file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleMatchChange = (uuid, balloonId) => {
    setMappings(prev => prev.map(m => {
      if (m.uuid !== uuid) return m;
      return { ...m, matchedBalloonId: balloonId ? parseInt(balloonId) : '', manualOverride: true };
    }));
  };

  const handleCommit = () => {
    // Transform array back to dictionary for DropZone
    const resultsMap = {};
    mappings.forEach(m => {
      if (m.matchedBalloonId) {
        resultsMap[m.matchedBalloonId] = {
          actual: m.cmmData.actual,
          status: m.cmmData.status,
          deviation: m.cmmData.deviation
        };
      }
    });
    onImport(resultsMap); // Update Parent State
    onClose();
  };

  // ===========================================================================
  // 3. RENDER
  // ===========================================================================
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col border border-[#2a2a2a] shadow-2xl">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center bg-[#111]">
            <div>
                <h2 className="text-white font-bold text-lg">Import CMM Results</h2>
                <p className="text-gray-500 text-xs">Intelligent Matching Engine Active</p>
            </div>
            <button onClick={onClose} className="text-gray-500 hover:text-white">✕</button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 bg-[#0a0a0a]">
            {step === 'upload' ? (
                <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="h-full border-2 border-dashed border-[#333] hover:border-[#E63946] rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors"
                >
                    <input ref={fileInputRef} type="file" className="hidden" accept=".csv,.txt,.rpt" onChange={handleFileUpload} />
                    {isUploading ? (
                        <div className="text-center">
                            <div className="w-8 h-8 border-2 border-[#E63946] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-gray-400">Parsing & Scoring Matches...</p>
                        </div>
                    ) : (
                        <>
                            <span className="text-4xl mb-4">📥</span>
                            <p className="text-white font-medium">Click to Upload CMM Report</p>
                            <p className="text-gray-500 text-sm mt-2">PC-DMIS, Calypso, or CSV</p>
                        </>
                    )}
                </div>
            ) : (
                <div className="space-y-4">
                    {/* Stats Bar */}
                    <div className="flex items-center justify-between bg-[#1a1a1a] p-3 rounded border border-[#333]">
                        <span className="text-sm text-gray-400">File: <span className="text-white">{cmmFilename}</span></span>
                        <div className="flex gap-4 text-sm">
                            <span className="text-green-400">{mappings.filter(m => m.matchedBalloonId).length} Matched</span>
                            <span className="text-gray-500">{mappings.length} Total Rows</span>
                        </div>
                    </div>

                    {/* Table */}
                    <table className="w-full text-left text-sm border-collapse">
                        <thead className="bg-[#111] text-gray-400 sticky top-0 z-10">
                            <tr>
                                <th className="p-3 border-b border-[#333]">CMM Feature</th>
                                <th className="p-3 border-b border-[#333]">Actual</th>
                                <th className="p-3 border-b border-[#333]">Deviation</th>
                                <th className="p-3 border-b border-[#333] w-1/3">Mapped Balloon</th>
                                <th className="p-3 border-b border-[#333]">Score</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2a2a2a]">
                            {mappings.map(row => (
                                <tr key={row.uuid} className="hover:bg-[#111]">
                                    <td className="p-3 text-white">
                                        {row.cmmData.feature_id}
                                        <div className="text-[10px] text-gray-500">Nom: {row.cmmData.nominal}</div>
                                    </td>
                                    <td className="p-3 font-mono text-blue-400">{row.cmmData.actual}</td>
                                    <td className={`p-3 font-mono ${Math.abs(row.cmmData.deviation) > 0 ? 'text-yellow-500' : 'text-gray-500'}`}>
                                        {row.cmmData.deviation}
                                    </td>
                                    <td className="p-3">
                                        <select 
                                            value={row.matchedBalloonId}
                                            onChange={(e) => handleMatchChange(row.uuid, e.target.value)}
                                            className={`w-full bg-[#0a0a0a] border rounded px-2 py-1 outline-none text-xs ${row.matchedBalloonId ? 'border-blue-900 text-white' : 'border-[#333] text-gray-500'}`}
                                        >
                                            <option value="">-- Unmapped --</option>
                                            {dimensions.map(d => (
                                                <option key={d.id} value={d.id}>#{d.id} - {d.value}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="p-3">
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 h-1.5 bg-[#333] rounded-full w-12 overflow-hidden">
                                                <div className={`h-full ${row.matchScore > 80 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${row.matchScore}%` }} />
                                            </div>
                                            <span className="text-[10px] text-gray-500">{Math.round(row.matchScore)}</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>

        {/* Footer */}
        {step === 'review' && (
            <div className="px-6 py-4 border-t border-[#2a2a2a] bg-[#111] flex justify-end gap-3">
                <button onClick={() => setStep('upload')} className="px-4 py-2 text-gray-400 hover:text-white text-sm">Back</button>
                <button 
                    onClick={handleCommit}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium shadow-lg"
                >
                    Import Data
                </button>
            </div>
        )}
      </div>
    </div>
  );
}
