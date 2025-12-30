/**
 * PropertiesPanel.jsx
 * Left sidebar for editing detailed properties of the selected dimension.
 * Matches InspectionXpert's "General Settings" / "Characteristic" panel.
 */
import React from 'react';

export function PropertiesPanel({ selectedDimension, onUpdate }) {
  if (!selectedDimension) {
    return (
      <div className="w-64 bg-[#161616] border-r border-[#2a2a2a] p-6 text-center">
        <div className="text-gray-600 mt-10">
          <svg className="w-12 h-12 mx-auto mb-4 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
          </svg>
          <p className="text-sm font-medium">No Selection</p>
          <p className="text-xs mt-2">Click a balloon to edit properties</p>
        </div>
      </div>
    );
  }

  // Helper to safely get/set nested parsed values
  const getVal = (field, fallback = '') => {
    return selectedDimension.parsed?.[field] ?? fallback;
  };

  const updateParsed = (field, value) => {
    onUpdate(selectedDimension.id, {
      parsed: {
        ...selectedDimension.parsed,
        [field]: value
      }
    });
  };

  const updateRoot = (field, value) => {
    onUpdate(selectedDimension.id, { [field]: value });
  };

  return (
    <div className="w-72 bg-[#161616] border-r border-[#2a2a2a] flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-[#2a2a2a] bg-[#1a1a1a]">
        <h2 className="text-sm font-bold text-white flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-xs">
            {selectedDimension.id}
          </span>
          Characteristic Properties
        </h2>
      </div>

      <div className="p-4 space-y-6">
        
        {/* Section: General */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">General</h3>
          
          <div className="space-y-1">
            <label className="text-xs text-gray-400">Value (Requirement)</label>
            <input 
              type="text" 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white focus:border-blue-500 outline-none"
              value={selectedDimension.value}
              onChange={(e) => updateRoot('value', e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Type</label>
              <select 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-gray-300 outline-none"
                value={getVal('subtype', 'Linear')}
                onChange={(e) => updateParsed('subtype', e.target.value)}
              >
                <option value="Linear">Linear</option>
                <option value="Diameter">Diameter</option>
                <option value="Radius">Radius</option>
                <option value="Angle">Angle</option>
                <option value="Chamfer">Chamfer</option>
                <option value="Note">Note</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-400">Units</label>
              <select 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-gray-300 outline-none"
                value={getVal('units', 'in')}
                onChange={(e) => updateParsed('units', e.target.value)}
              >
                <option value="in">Inch</option>
                <option value="mm">MM</option>
                <option value="deg">Deg</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section: Tolerancing */}
        <div className="space-y-3 pt-4 border-t border-[#2a2a2a]">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Tolerancing</h3>
          
          <div className="space-y-1">
             <label className="text-xs text-gray-400">Tolerance Type</label>
             <select 
                className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-gray-300 outline-none"
                value={getVal('tolerance_type', 'bilateral')}
                onChange={(e) => updateParsed('tolerance_type', e.target.value)}
              >
                <option value="bilateral">Bilateral (±)</option>
                <option value="limit">Limit (+/-)</option>
                <option value="fit">Fit Class (ISO 286)</option>
                <option value="max">Max</option>
                <option value="min">Min</option>
                <option value="basic">Basic</option>
              </select>
          </div>

          {/* Conditional Inputs based on Tolerance Type */}
          {getVal('tolerance_type') === 'fit' ? (
             <div className="space-y-1">
                <label className="text-xs text-purple-400 font-bold">Fit Class (e.g., H7)</label>
                <input 
                  type="text" 
                  className="w-full bg-[#0a0a0a] border border-purple-900/50 rounded px-2 py-1.5 text-sm text-purple-400 focus:border-purple-500 outline-none font-mono"
                  value={getVal('fit_class')}
                  placeholder="H7"
                  onChange={(e) => updateParsed('fit_class', e.target.value)}
                />
             </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Plus / Upper</label>
                <input 
                  type="number" step="0.001"
                  className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white outline-none font-mono"
                  value={getVal('upper_tol')}
                  onChange={(e) => updateParsed('upper_tol', parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Minus / Lower</label>
                <input 
                  type="number" step="0.001"
                  className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white outline-none font-mono"
                  value={getVal('lower_tol')}
                  onChange={(e) => updateParsed('lower_tol', parseFloat(e.target.value))}
                />
              </div>
            </div>
          )}

          <div className="bg-[#222] rounded p-2 mt-2">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500">Calculated Max:</span>
              <span className="text-green-400 font-mono">{getVal('max_limit', 0).toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Calculated Min:</span>
              <span className="text-green-400 font-mono">{getVal('min_limit', 0).toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Section: Inspection */}
        <div className="space-y-3 pt-4 border-t border-[#2a2a2a]">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Inspection</h3>
          
          <div className="space-y-1">
            <label className="text-xs text-gray-400">Method</label>
            <select 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-blue-400 font-medium outline-none"
              value={getVal('inspection_method', '')}
              onChange={(e) => updateParsed('inspection_method', e.target.value)}
            >
              <option value="">Select Method...</option>
              <option value="CMM">CMM</option>
              <option value="Visual">Visual</option>
              <option value="Caliper">Caliper</option>
              <option value="Micrometer">Micrometer</option>
              <option value="Gage Block">Gage Block</option>
              <option value="Pin Gage">Pin Gage</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-gray-400">Operation</label>
            <input 
              type="text" 
              className="w-full bg-[#0a0a0a] border border-[#333] rounded px-2 py-1.5 text-sm text-white outline-none"
              placeholder="e.g. Op 10"
              value={getVal('operation', '')}
              onChange={(e) => updateParsed('operation', e.target.value)}
            />
          </div>
        </div>

      </div>
    </div>
  );
}
