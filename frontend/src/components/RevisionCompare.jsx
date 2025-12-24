/**
 * Revision Compare Component
 * Compare two drawing revisions and highlight only the changes
 */

import React, { useState, useRef } from 'react';
import { API_BASE_URL } from '../constants/config';

export function RevisionCompare({ onCompareComplete }) {
  const [isOpen, setIsOpen] = useState(false);
  const [revA, setRevA] = useState(null);
  const [revB, setRevB] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const fileInputARef = useRef(null);
  const fileInputBRef = useRef(null);

  const handleFileSelect = (file, setRev) => {
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setRev({
        file,
        name: file.name,
        preview: e.target.result
      });
    };
    reader.readAsDataURL(file);
  };

  const handleCompare = async () => {
    if (!revA || !revB) return;
    
    setIsComparing(true);
    
    try {
      // First, process both revisions
      const formDataA = new FormData();
      formDataA.append('file', revA.file);
      
      const formDataB = new FormData();
      formDataB.append('file', revB.file);
      
      const [responseA, responseB] = await Promise.all([
        fetch(`${API_BASE_URL}/process`, { method: 'POST', body: formDataA }),
        fetch(`${API_BASE_URL}/process`, { method: 'POST', body: formDataB })
      ]);
      
      const [dataA, dataB] = await Promise.all([
        responseA.json(),
        responseB.json()
      ]);
      
      if (dataA.success && dataB.success) {
        // Compare dimensions
        const dimsA = dataA.dimensions || [];
        const dimsB = dataB.dimensions || [];
        
        const changes = {
          added: [],      // In B but not in A
          removed: [],    // In A but not in B
          modified: [],   // In both but different values
          unchanged: []   // Same in both
        };
        
        // Find dimensions in B
        dimsB.forEach(dimB => {
          const matchA = dimsA.find(dimA => {
            // Match by similar position (within 5% tolerance)
            const posMatch = 
              Math.abs(dimA.bounding_box.xmin - dimB.bounding_box.xmin) < 50 &&
              Math.abs(dimA.bounding_box.ymin - dimB.bounding_box.ymin) < 50;
            return posMatch;
          });
          
          if (!matchA) {
            changes.added.push({ ...dimB, changeType: 'added' });
          } else if (matchA.value !== dimB.value) {
            changes.modified.push({ 
              ...dimB, 
              changeType: 'modified',
              oldValue: matchA.value,
              newValue: dimB.value 
            });
          } else {
            changes.unchanged.push({ ...dimB, changeType: 'unchanged' });
          }
        });
        
        // Find removed dimensions (in A but not in B)
        dimsA.forEach(dimA => {
          const matchB = dimsB.find(dimB => {
            const posMatch = 
              Math.abs(dimA.bounding_box.xmin - dimB.bounding_box.xmin) < 50 &&
              Math.abs(dimA.bounding_box.ymin - dimB.bounding_box.ymin) < 50;
            return posMatch;
          });
          
          if (!matchB) {
            changes.removed.push({ ...dimA, changeType: 'removed' });
          }
        });
        
        setComparisonResult({
          revA: dataA,
          revB: dataB,
          changes,
          summary: {
            added: changes.added.length,
            removed: changes.removed.length,
            modified: changes.modified.length,
            unchanged: changes.unchanged.length
          }
        });
      }
    } catch (err) {
      console.error('Comparison failed:', err);
    } finally {
      setIsComparing(false);
    }
  };

  const handleUseChanges = () => {
    if (comparisonResult && onCompareComplete) {
      // Return only the changed dimensions (added + modified) for ballooning
      const changedDimensions = [
        ...comparisonResult.changes.added,
        ...comparisonResult.changes.modified
      ].map((dim, idx) => ({
        ...dim,
        id: idx + 1 // Re-number
      }));
      
      onCompareComplete({
        dimensions: changedDimensions,
        image: comparisonResult.revB.image,
        metadata: comparisonResult.revB.metadata,
        comparison: comparisonResult
      });
      setIsOpen(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2 font-medium"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        Compare Revisions
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
                Delta FAI
              </span>
              <span className="text-gray-400">- Revision Compare</span>
            </h2>
            <p className="text-gray-400 text-sm">Upload two revisions to find only what changed</p>
          </div>
          <button onClick={() => { setIsOpen(false); setComparisonResult(null); }} className="text-gray-500 hover:text-white">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {!comparisonResult ? (
            <div className="grid grid-cols-2 gap-6">
              {/* Rev A */}
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-gray-600 flex items-center justify-center text-xs">A</span>
                  Old Revision
                </h3>
                <div 
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                    revA ? 'border-green-500/50 bg-green-500/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                  }`}
                  onClick={() => fileInputARef.current?.click()}
                >
                  <input
                    ref={fileInputARef}
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => handleFileSelect(e.target.files[0], setRevA)}
                    className="hidden"
                  />
                  {revA ? (
                    <div>
                      <img src={revA.preview} alt="Rev A" className="max-h-48 mx-auto rounded mb-2" />
                      <p className="text-green-400 text-sm">{revA.name}</p>
                    </div>
                  ) : (
                    <div>
                      <svg className="w-10 h-10 text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="text-gray-400">Upload Rev A (Old)</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Rev B */}
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-[#E63946] flex items-center justify-center text-xs text-white">B</span>
                  New Revision
                </h3>
                <div 
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                    revB ? 'border-[#E63946]/50 bg-[#E63946]/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a]'
                  }`}
                  onClick={() => fileInputBRef.current?.click()}
                >
                  <input
                    ref={fileInputBRef}
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => handleFileSelect(e.target.files[0], setRevB)}
                    className="hidden"
                  />
                  {revB ? (
                    <div>
                      <img src={revB.preview} alt="Rev B" className="max-h-48 mx-auto rounded mb-2" />
                      <p className="text-[#E63946] text-sm">{revB.name}</p>
                    </div>
                  ) : (
                    <div>
                      <svg className="w-10 h-10 text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <p className="text-gray-400">Upload Rev B (New)</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-green-400">{comparisonResult.summary.added}</div>
                  <div className="text-green-400/70 text-sm">Added</div>
                </div>
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-yellow-400">{comparisonResult.summary.modified}</div>
                  <div className="text-yellow-400/70 text-sm">Modified</div>
                </div>
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-red-400">{comparisonResult.summary.removed}</div>
                  <div className="text-red-400/70 text-sm">Removed</div>
                </div>
                <div className="bg-gray-500/10 border border-gray-500/30 rounded-xl p-4 text-center">
                  <div className="text-3xl font-bold text-gray-400">{comparisonResult.summary.unchanged}</div>
                  <div className="text-gray-400/70 text-sm">Unchanged</div>
                </div>
              </div>

              {/* Changes List */}
              <div className="bg-[#0a0a0a] rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-[#1a1a1a] border-b border-[#2a2a2a]">
                  <h3 className="font-medium text-white">Changes Detected</h3>
                </div>
                <div className="max-h-64 overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-[#161616] sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left text-gray-400">Status</th>
                        <th className="px-4 py-2 text-left text-gray-400">Zone</th>
                        <th className="px-4 py-2 text-left text-gray-400">Old Value</th>
                        <th className="px-4 py-2 text-left text-gray-400">New Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisonResult.changes.added.map((dim, idx) => (
                        <tr key={`added-${idx}`} className="border-t border-[#1a1a1a]">
                          <td className="px-4 py-2"><span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">ADDED</span></td>
                          <td className="px-4 py-2 text-gray-300">{dim.zone || '—'}</td>
                          <td className="px-4 py-2 text-gray-500">—</td>
                          <td className="px-4 py-2 text-white font-mono">{dim.value}</td>
                        </tr>
                      ))}
                      {comparisonResult.changes.modified.map((dim, idx) => (
                        <tr key={`modified-${idx}`} className="border-t border-[#1a1a1a]">
                          <td className="px-4 py-2"><span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">MODIFIED</span></td>
                          <td className="px-4 py-2 text-gray-300">{dim.zone || '—'}</td>
                          <td className="px-4 py-2 text-gray-500 font-mono line-through">{dim.oldValue}</td>
                          <td className="px-4 py-2 text-white font-mono">{dim.newValue}</td>
                        </tr>
                      ))}
                      {comparisonResult.changes.removed.map((dim, idx) => (
                        <tr key={`removed-${idx}`} className="border-t border-[#1a1a1a]">
                          <td className="px-4 py-2"><span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">REMOVED</span></td>
                          <td className="px-4 py-2 text-gray-300">{dim.zone || '—'}</td>
                          <td className="px-4 py-2 text-red-400 font-mono">{dim.value}</td>
                          <td className="px-4 py-2 text-gray-500">—</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {comparisonResult.summary.added + comparisonResult.summary.modified + comparisonResult.summary.removed === 0 && (
                    <div className="px-4 py-8 text-center text-gray-500">
                      No changes detected between revisions
                    </div>
                  )}
                </div>
              </div>

              {/* Preview */}
              <div className="relative bg-[#0a0a0a] rounded-xl overflow-hidden">
                <img src={comparisonResult.revB.image} alt="Rev B" className="w-full" />
                {/* Overlay changed dimensions */}
                {[...comparisonResult.changes.added, ...comparisonResult.changes.modified].map((dim, idx) => {
                  const left = (dim.bounding_box.xmin + dim.bounding_box.xmax) / 2 / 10;
                  const top = (dim.bounding_box.ymin + dim.bounding_box.ymax) / 2 / 10;
                  return (
                    <div
                      key={idx}
                      className="absolute transform -translate-x-1/2 -translate-y-1/2"
                      style={{ left: `${left}%`, top: `${top}%` }}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 ${
                        dim.changeType === 'added' ? 'bg-green-500 border-green-400 text-white' : 'bg-yellow-500 border-yellow-400 text-black'
                      }`}>
                        {dim.changeType === 'added' ? '+' : '~'}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#2a2a2a] flex justify-between items-center">
          {!comparisonResult ? (
            <>
              <div className="text-gray-500 text-sm">
                {revA && revB ? 'Ready to compare' : 'Upload both revisions to compare'}
              </div>
              <button
                onClick={handleCompare}
                disabled={!revA || !revB || isComparing}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-medium rounded-lg disabled:opacity-50 flex items-center gap-2"
              >
                {isComparing ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Comparing...
                  </>
                ) : (
                  <>Compare Revisions</>
                )}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setComparisonResult(null)}
                className="text-gray-400 hover:text-white"
              >
                ← Compare Different Files
              </button>
              <button
                onClick={handleUseChanges}
                className="px-6 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg flex items-center gap-2"
              >
                Balloon Only Changes ({comparisonResult.summary.added + comparisonResult.summary.modified})
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
