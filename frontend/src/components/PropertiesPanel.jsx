import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../constants/config';

/**
 * PropertiesPanel.jsx
 * Side panel for editing dimension attributes, ISO Fits, and Sampling.
 * FIXED: Data flow now matches the Parent DropZone's state engine.
 */
export function PropertiesPanel({ dimension, onUpdate, cmmResult }) {
  // Local state for Sampling inputs (UI only)
  const [localSampling, setLocalSampling] = useState({
    lot_size: 0,
    aql: 2.5,
    level: 'II'
  });

  // Sync local state when dimension changes
  useEffect(() => {
    if (dimension?.parsed) {
        setLocalSampling({
            lot_size: dimension.parsed.lot_size || 0,
            aql: dimension.parsed.aql || 2.5,
            level: dimension.parsed.inspection_level || 'II'
        });
    }
  }, [dimension?.id]);

  if (!dimension) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500 bg-[#161616]">
        <svg className="w-12 h-12 mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
           <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
        </svg>
        <p className="text-sm font-medium">No Selection</p>
        <p className="text-xs mt-1">Click a balloon to edit</p>
      </div>
    );
  }

  // --- HELPERS ---
  const getVal = (field, fallback = '') => dimension.parsed?.[field] ?? fallback;
  const getRoot = (field, fallback = '') => dimension[field] ?? fallback;

  // --- UPDATE HANDLERS ---
  // Fix: Send the ENTIRE object back to DropZone
  const updateParsed = (field, value) => {
    onUpdate({
      ...dimension,
      parsed: {
        ...dimension.parsed,
        [field]: value
      }
    });
  };

  const updateRoot = (field, value) => {
    onUpdate({
      ...dimension,
      [field]: value
    });
  };

  // --- SAMPLING LOGIC ---
  // Hits the backend when inputs change
  useEffect(() => {
    const calculateSampling = async () => {
        const { lot_size, aql, level } = localSampling;
        if (lot_size <= 0) return;

        try {
            const res = await fetch(`${API_BASE_URL}/sampling/calculate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lot_size, aql, level })
            });
            const data = await res.json();
            
            // Only update parent if value changed to avoid loops
            if (data.sample_size !== dimension.parsed?.sample_size) {
                onUpdate({
                    ...dimension,
                    parsed: {
                        ...dimension.parsed,
                        lot_size,
                        aql,
                        inspection_level: level,
                        sample_size: data.sample_size
                    }
                });
            }
        } catch (e) {
            console.error("Sampling calc failed", e);
        }
    };

    const timer = setTimeout(calculateSampling, 600); // Debounce
    return () => clearTimeout(timer);
  }, [localSampling.lot_size, localSampling.aql, localSampling.level]);


  return (
    <div className="w-full bg-[#161616] flex flex-col h-full overflow-y-auto text-gray-300 font-sans border-r border-[#2a2a2a]">
      
      {/* Header */}
      <div className="p-4 border-b border-[#2a2a2a] bg-[#1a1a1a]">
        <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-[#E63946] flex items-center justify-center text-xs text-white shadow-lg">
                    {dimension.id}
                </span>
                Properties
            </h2>
            <span className={`text-[10px] px-2 py-0.5 rounded border ${dimension.confidence > 0.9 ? 'border-green-500/30 text-green-400' : 'border-yellow-500/30 text-yellow-400'}`}>
                {Math.round((dimension.confidence || 0) * 100)}% Conf.
            </span>
        </div>
      </div>

      <div className="p-4 space-y-6">
        
        {/* 1. Identification (Schema Requirement #5) */}
        <div className="space-y-3">
          <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Identification</h3>
          
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Chart ID</label>
              <input 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-white focus:border-[#E63946] outline-none transition-colors"
                value={getVal('chart_char_id')}
                onChange={(e) => updateParsed('chart_char_id', e.target.value)}
                placeholder="1.1"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Operation</label>
              <input 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-white focus:border-[#E63946] outline-none"
                value={getVal('operation')}
                onChange={(e) => updateParsed('operation', e.target.value)}
                placeholder="Op 10"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Sheet</label>
              <input 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-white focus:border-[#E63946] outline-none"
                value={dimension.page || getVal('sheet')}
                onChange={(e) => updateRoot('page', parseInt(e.target.value) || 1)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">View</label>
              <input 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-white focus:border-[#E63946] outline-none"
                value={getVal('view_name')}
                onChange={(e) => updateParsed('view_name', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* 2. Definition */}
        <div className="space-y-3 pt-4 border-t border-[#2a2a2a]">
          <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Definition</h3>
          
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Full Specification</label>
            <textarea 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white focus:border-[#E63946] outline-none resize-none h-16 font-mono"
              value={getVal('full_specification', dimension.value)}
              onChange={(e) => updateParsed('full_specification', e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Nominal</label>
              <input 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white focus:border-[#E63946] outline-none font-mono"
                value={dimension.value}
                onChange={(e) => updateRoot('value', e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Units</label>
              <select 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-gray-300 outline-none"
                value={getVal('units', 'in')}
                onChange={(e) => updateParsed('units', e.target.value)}
              >
                <option value="in">Inch</option>
                <option value="mm">MM</option>
                <option value="deg">Deg</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Feature Type</label>
            <select 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-gray-300 outline-none"
              value={getVal('subtype', 'Linear')}
              onChange={(e) => updateParsed('subtype', e.target.value)}
            >
              <option value="Linear">Linear</option>
              <option value="Diameter">Diameter (Ø)</option>
              <option value="Radius">Radius (R)</option>
              <option value="Chamfer">Chamfer</option>
              <option value="Weld">Weld</option>
              <option value="Note">Note</option>
              <option value="GD&T">GD&T</option>
            </select>
          </div>
        </div>

        {/* 3. Tolerancing (Requirement #2) */}
        <div className="space-y-3 pt-4 border-t border-[#2a2a2a]">
          <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Tolerancing</h3>
          
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Mode</label>
            <select 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-blue-400 outline-none font-medium"
              value={getVal('tolerance_type', 'bilateral')}
              onChange={(e) => updateParsed('tolerance_type', e.target.value)}
            >
              <option value="bilateral">Bilateral (±)</option>
              <option value="limit">Limit (High/Low)</option>
              <option value="fit">ISO 286 Fit</option>
              <option value="basic">Basic (Boxed)</option>
            </select>
          </div>

          {getVal('tolerance_type') === 'fit' ? (
            <div className="grid grid-cols-2 gap-2 animate-fadeIn">
              <div className="space-y-1">
                <label className="text-[10px] text-purple-400 font-bold">Hole Fit</label>
                <input 
                  className="w-full bg-[#0a0a0a] border border-purple-900/50 rounded px-2 py-1.5 text-sm text-purple-400 focus:border-purple-500 outline-none font-mono uppercase placeholder-purple-900/50"
                  value={getVal('hole_fit_class')}
                  placeholder="H7"
                  onChange={(e) => updateParsed('hole_fit_class', e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-purple-400 font-bold">Shaft Fit</label>
                <input 
                  className="w-full bg-[#0a0a0a] border border-purple-900/50 rounded px-2 py-1.5 text-sm text-purple-400 focus:border-purple-500 outline-none font-mono uppercase placeholder-purple-900/50"
                  value={getVal('shaft_fit_class')}
                  placeholder="g6"
                  onChange={(e) => updateParsed('shaft_fit_class', e.target.value)}
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[10px] text-gray-400">Plus (+)</label>
                <input 
                  type="number" step="0.001"
                  className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white focus:border-[#E63946] outline-none font-mono"
                  value={getVal('upper_tol')}
                  onChange={(e) => updateParsed('upper_tol', parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-gray-400">Minus (-)</label>
                <input 
                  type="number" step="0.001"
                  className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white focus:border-[#E63946] outline-none font-mono"
                  value={getVal('lower_tol')}
                  onChange={(e) => updateParsed('lower_tol', parseFloat(e.target.value))}
                />
              </div>
            </div>
          )}

          <div className="bg-[#222] rounded p-2 mt-2 border border-[#333]">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500">Upper Limit:</span>
              <span className="text-green-400 font-mono">{getVal('upper_limit', 0).toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Lower Limit:</span>
              <span className="text-green-400 font-mono">{getVal('lower_limit', 0).toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* 4. Sampling (Requirement #9) */}
        <div className="space-y-3 pt-4 border-t border-[#2a2a2a]">
          <h3 className="text-[10px] font-bold text-yellow-600 uppercase tracking-wider">Sampling (ANSI Z1.4)</h3>
          
          <div className="grid grid-cols-3 gap-2">
             <div className="space-y-1">
               <label className="text-[10px] text-gray-400">Lot Size</label>
               <input 
                 type="number" 
                 className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-xs text-white focus:border-yellow-600 outline-none"
                 value={localSampling.lot_size}
                 onChange={(e) => setLocalSampling(s => ({...s, lot_size: parseInt(e.target.value) || 0}))}
               />
             </div>
             <div className="space-y-1">
               <label className="text-[10px] text-gray-400">AQL</label>
               <select 
                 className="w-full bg-[#0a0a0a] border border-[#333] rounded px-1 py-1.5 text-xs text-gray-300 outline-none"
                 value={localSampling.aql}
                 onChange={(e) => setLocalSampling(s => ({...s, aql: parseFloat(e.target.value)}))}
               >
                 <option value="0.65">0.65</option>
                 <option value="1.0">1.0</option>
                 <option value="2.5">2.5</option>
                 <option value="4.0">4.0</option>
               </select>
             </div>
             <div className="space-y-1">
               <label className="text-[10px] text-yellow-600 font-bold">Inspect</label>
               <div className="w-full bg-yellow-900/20 border border-yellow-900/50 rounded px-1 py-1.5 text-xs text-yellow-500 font-bold text-center">
                 {getVal('sample_size', '-')}
               </div>
             </div>
          </div>
        </div>

        {/* 5. CMM Result */}
        {cmmResult && (
            <div className="mt-4 p-3 bg-blue-900/10 border border-blue-900/30 rounded-lg">
                <div className="text-[10px] text-blue-400 uppercase tracking-wide mb-1">CMM Measured</div>
                <div className="flex justify-between items-end">
                    <span className="text-xl font-mono text-white">{cmmResult.actual}</span>
                    <span className={`text-xs px-2 py-0.5 rounded font-bold ${cmmResult.status === 'PASS' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {cmmResult.status}
                    </span>
                </div>
            </div>
        )}

      </div>
    </div>
  );
}
