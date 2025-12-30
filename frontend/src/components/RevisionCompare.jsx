import React, { useState, useRef } from 'react';
import { API_BASE_URL } from '../constants/config';
import { useAuth } from '../context/AuthContext';

export function RevisionCompare({ onClose, onPort, onShowGlassWall }) {
  const { isPro } = useAuth();
  const [revA, setRevA] = useState(null);
  const [revB, setRevB] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [includeGhosts, setIncludeGhosts] = useState(true);
  
  const fileInputARef = useRef(null);
  const fileInputBRef = useRef(null);

  // Helper: Read file preview
  const handleFileSelect = (file, setRev) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => setRev({ 
        file, 
        name: file.name, 
        preview: e.target.result 
    });
    reader.readAsDataURL(file);
  };

  // 1. Comparison Logic (Backend Call)
  const handleCompare = async () => {
    if (!revA || !revB) return;
    setIsComparing(true);
    
    try {
      const formData = new FormData();
      formData.append('file_a', revA.file);
      formData.append('file_b', revB.file);
      
      // Call the REAL Computer Vision endpoint
      const response = await fetch(`${API_BASE_URL}/compare`, { 
        method: 'POST', 
        body: formData 
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Backend returns aligned dimensions with status: 'added', 'modified', 'unchanged'
        const added = data.dimensions.filter(d => d.status === 'added');
        const modified = data.dimensions.filter(d => d.status === 'modified');
        const unchanged = data.dimensions.filter(d => d.status === 'unchanged');
        const removed = data.removed_dimensions || [];
        
        setComparisonResult({
          revB: {
            image: data.image, // Aligned image
            metadata: data.metadata,
            dimensions: data.dimensions
          },
          changes: { added, modified, removed, unchanged },
          summary: {
            added: added.length,
            removed: removed.length,
            modified: modified.length,
            unchanged: unchanged.length
          }
        });
      } else {
        alert("Comparison failed: " + (data.detail || "Unknown error"));
      }
    } catch (err) {
      console.error('Comparison failed:', err);
      alert("Network error during comparison");
    } finally {
      setIsComparing(false);
    }
  };

  // 2. Porting Logic (Applying Changes)
  const handlePortBalloons = () => {
    if (!isPro) { 
        onShowGlassWall(); 
        return; 
    }
    
    if (comparisonResult) {
      let finalDimensions = [...comparisonResult.revB.dimensions];

      // Add "Ghost" balloons for removed items if requested
      if (includeGhosts && comparisonResult.changes.removed) {
        const ghosts = comparisonResult.changes.removed.map(d => ({
            ...d,
            status: 'removed',
            isGhost: true,
            // Visual styling for ghosts
            confidence: 0.5,
            method: 'Ghost'
        }));
        finalDimensions = [...finalDimensions, ...ghosts];
      }
      
      // Pass aligned data back to parent (DropZone)
      onPort({
        dimensions: finalDimensions,
        image: comparisonResult.revB.image,
        metadata: comparisonResult.revB.metadata
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-[#2a2a2a]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center bg-[#111]">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">Delta FAI</span>
              <span className="text-gray-400 text-sm font-normal">- Revision Control</span>
            </h2>
            <p className="text-gray-500 text-xs mt-1">Computer Vision Alignment & Porting</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">✕</button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto p-6 bg-[#0a0a0a]">
          {!comparisonResult ? (
            <div className="grid grid-cols-2 gap-8 h-full items-center">
                {/* Upload Zone A */}
                <div className="space-y-4">
                    <h3 className="text-white font-medium flex items-center gap-2">
                        <span className="w-6 h-6 rounded bg-gray-600 flex items-center justify-center text-xs">A</span> Old Revision
                    </h3>
                    <div 
                        onClick={() => fileInputARef.current?.click()}
                        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all h-64 flex flex-col items-center justify-center ${revA ? 'border-green-500/30 bg-green-500/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#111]'}`}
                    >
                        <input ref={fileInputARef} type="file" onChange={(e) => handleFileSelect(e.target.files[0], setRevA)} className="hidden" />
                        {revA ? (
                            <>
                                <img src={revA.preview} className="max-h-40 rounded shadow-lg mb-4" alt="Rev A" />
                                <p className="text-green-400 text-sm truncate max-w-xs">{revA.name}</p>
                            </>
                        ) : (
                            <>
                                <span className="text-4xl mb-4">📄</span>
                                <p className="text-gray-400">Click to upload Old PDF</p>
                            </>
                        )}
                    </div>
                </div>

                {/* Upload Zone B */}
                <div className="space-y-4">
                    <h3 className="text-white font-medium flex items-center gap-2">
                        <span className="w-6 h-6 rounded bg-[#E63946] flex items-center justify-center text-xs">B</span> New Revision
                    </h3>
                    <div 
                        onClick={() => fileInputBRef.current?.click()}
                        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all h-64 flex flex-col items-center justify-center ${revB ? 'border-[#E63946]/30 bg-[#E63946]/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#111]'}`}
                    >
                        <input ref={fileInputBRef} type="file" onChange={(e) => handleFileSelect(e.target.files[0], setRevB)} className="hidden" />
                        {revB ? (
                            <>
                                <img src={revB.preview} className="max-h-40 rounded shadow-lg mb-4" alt="Rev B" />
                                <p className="text-[#E63946] text-sm truncate max-w-xs">{revB.name}</p>
                            </>
                        ) : (
                            <>
                                <span className="text-4xl mb-4">📑</span>
                                <p className="text-gray-400">Click to upload New PDF</p>
                            </>
                        )}
                    </div>
                </div>
            </div>
          ) : (
            <div className="space-y-6">
                {/* Stats */}
                <div className="grid grid-cols-4 gap-4">
                    <StatBox count={comparisonResult.summary.added} label="Added" color="green" />
                    <StatBox count={comparisonResult.summary.modified} label="Modified" color="yellow" />
                    <StatBox count={comparisonResult.summary.removed} label="Removed" color="red" />
                    <StatBox count={comparisonResult.summary.unchanged} label="Unchanged" color="gray" />
                </div>

                {/* Diff Table */}
                <div className="bg-[#111] rounded-xl border border-[#2a2a2a] overflow-hidden max-h-96 overflow-y-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-[#1a1a1a] text-gray-400 sticky top-0">
                            <tr>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3">ID</th>
                                <th className="px-4 py-3">Old Value</th>
                                <th className="px-4 py-3">New Value</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2a2a2a]">
                            {comparisonResult.changes.added.map(d => <DiffRow key={d.id} d={d} status="added" />)}
                            {comparisonResult.changes.modified.map(d => <DiffRow key={d.id} d={d} status="modified" />)}
                            {comparisonResult.changes.removed.map(d => <DiffRow key={d.id} d={d} status="removed" />)}
                        </tbody>
                    </table>
                </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#2a2a2a] bg-[#111] flex justify-between items-center">
            {!comparisonResult ? (
                <button 
                    onClick={handleCompare} 
                    disabled={!revA || !revB || isComparing}
                    className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all"
                >
                    {isComparing ? 'Aligning Vectors & Comparing...' : 'Run Comparison'}
                </button>
            ) : (
                <>
                    <button onClick={() => setComparisonResult(null)} className="text-gray-400 hover:text-white text-sm">Reset</button>
                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
                            <input type="checkbox" checked={includeGhosts} onChange={e => setIncludeGhosts(e.target.checked)} className="rounded bg-[#2a2a2a] border-none text-[#E63946] focus:ring-0" />
                            Show Removed Items (Ghosts)
                        </label>
                        <button 
                            onClick={handlePortBalloons}
                            className={`px-6 py-2 rounded-lg font-medium text-white shadow-lg ${isPro ? 'bg-[#E63946] hover:bg-[#d62839]' : 'bg-gray-600 cursor-not-allowed opacity-50'}`}
                        >
                            {isPro ? 'Port Balloons & Replace Drawing' : 'Unlock Pro to Port'}
                        </button>
                    </div>
                </>
            )}
        </div>

      </div>
    </div>
  );
}

// Sub-components for cleaner code
function StatBox({ count, label, color }) {
    const colors = {
        green: 'text-green-400 bg-green-500/10 border-green-500/20',
        yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
        red: 'text-red-400 bg-red-500/10 border-red-500/20',
        gray: 'text-gray-400 bg-gray-500/10 border-gray-500/20'
    };
    return (
        <div className={`p-4 rounded-xl border text-center ${colors[color]}`}>
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-xs uppercase tracking-wide opacity-70">{label}</div>
        </div>
    );
}

function DiffRow({ d, status }) {
    const badges = {
        added: <span className="bg-green-500/20 text-green-400 px-2 py-0.5 rounded text-xs">ADDED</span>,
        modified: <span className="bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded text-xs">MODIFIED</span>,
        removed: <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-xs">REMOVED</span>
    };

    return (
        <tr className="hover:bg-[#1a1a1a]">
            <td className="px-4 py-2">{badges[status]}</td>
            <td className="px-4 py-2 text-white">#{d.id}</td>
            <td className="px-4 py-2 text-gray-400 font-mono line-through decoration-red-500/50">{d.oldValue || d.old_value || '-'}</td>
            <td className="px-4 py-2 text-white font-mono">{d.value || '-'}</td>
        </tr>
    );
}
