/**
 * TableManager.jsx
 * Excel-like grid view for managing engineering characteristics.
 * Supports inline editing and matches InspectionXpert's bottom panel.
 */
import React from 'react';

export function TableManager({ dimensions, selectedId, onSelect, onUpdate }) {
  // Helper to safely get parsed values
  const getVal = (dim, field, fallback = '') => {
    return dim.parsed?.[field] ?? fallback;
  };

  const handleChange = (id, field, value) => {
    // Determine if we are updating the main value or parsed metadata
    if (field === 'value') {
      onUpdate(id, { value });
    } else {
      // For metadata updates (method, fit_class, etc.), we update the 'parsed' object
      // In a real app, you might want a flatter structure, but this keeps schema consistent
      onUpdate(id, { 
        parsed: { ...dimensions.find(d => d.id === id).parsed, [field]: value } 
      });
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#161616] border-t border-[#2a2a2a] shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.3)]">
      {/* Toolbar / Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#1a1a1a] border-b border-[#2a2a2a]">
        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Characteristic Table</span>
        <div className="text-xs text-gray-500">
          {dimensions.length} items
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full text-xs text-left border-collapse">
          <thead className="sticky top-0 bg-[#252525] text-gray-300 z-10 shadow-sm">
            <tr>
              <th className="p-2 border-r border-b border-[#333] w-12 text-center">#ID</th>
              <th className="p-2 border-r border-b border-[#333] w-16">Sheet</th>
              <th className="p-2 border-r border-b border-[#333] w-24">Type</th>
              <th className="p-2 border-r border-b border-[#333] w-24">Subtype</th>
              <th className="p-2 border-r border-b border-[#333] w-32">Nominal</th>
              <th className="p-2 border-r border-b border-[#333] w-20">Units</th>
              <th className="p-2 border-r border-b border-[#333] w-32">Tolerance</th>
              <th className="p-2 border-r border-b border-[#333] w-24">Lower</th>
              <th className="p-2 border-r border-b border-[#333] w-24">Upper</th>
              <th className="p-2 border-r border-b border-[#333] w-24 text-purple-400">Fit</th>
              <th className="p-2 border-r border-b border-[#333] w-32 text-blue-400">Method</th>
            </tr>
          </thead>
          <tbody className="bg-[#161616] text-gray-300">
            {dimensions.map((dim) => {
              const isSelected = selectedId === dim.id;
              const isPass = dim.actual && (parseFloat(dim.actual) >= getVal(dim, 'min_limit') && parseFloat(dim.actual) <= getVal(dim, 'max_limit'));
              
              return (
                <tr 
                  key={dim.id}
                  onClick={() => onSelect(dim.id)}
                  className={`border-b border-[#2a2a2a] hover:bg-[#2a2a2a] cursor-pointer transition-colors ${
                    isSelected ? 'bg-[#3a3a3a]' : ''
                  }`}
                >
                  {/* ID */}
                  <td className={`p-2 border-r border-[#2a2a2a] text-center font-bold ${isSelected ? 'text-white' : 'text-gray-500'}`}>
                    {dim.id}
                  </td>
                  
                  {/* Sheet */}
                  <td className="p-2 border-r border-[#2a2a2a] text-gray-500">
                    {dim.page || 1}
                  </td>

                  {/* Type */}
                  <td className="p-2 border-r border-[#2a2a2a]">
                    {getVal(dim, 'is_gdt') ? 'GD&T' : 'Dim'}
                  </td>

                  {/* Subtype (Dropdown) */}
                  <td className="p-0 border-r border-[#2a2a2a]">
                    <select 
                      className="w-full h-full p-2 bg-transparent border-none outline-none text-gray-300 focus:bg-[#000]"
                      value={getVal(dim, 'subtype', 'Linear')}
                      onChange={(e) => handleChange(dim.id, 'subtype', e.target.value)}
                    >
                      <option value="Linear">Linear</option>
                      <option value="Diameter">Diameter (Ø)</option>
                      <option value="Radius">Radius (R)</option>
                      <option value="Angle">Angle (∠)</option>
                      <option value="Chamfer">Chamfer</option>
                    </select>
                  </td>

                  {/* Nominal (Editable) */}
                  <td className="p-0 border-r border-[#2a2a2a]">
                    <input 
                      type="text"
                      className="w-full h-full p-2 bg-transparent border-none outline-none focus:bg-[#000] font-mono text-white"
                      value={dim.value} // Shows raw text, or could use dim.parsed.nominal
                      onChange={(e) => handleChange(dim.id, 'value', e.target.value)}
                    />
                  </td>

                  {/* Units */}
                  <td className="p-2 border-r border-[#2a2a2a] text-gray-500 text-xs">
                    {getVal(dim, 'units', 'in')}
                  </td>

                  {/* Tolerance Display */}
                  <td className="p-2 border-r border-[#2a2a2a] text-gray-400 font-mono text-[10px]">
                    {getVal(dim, 'tolerance_type') === 'fit' ? (
                      <span className="text-purple-400 font-bold">{getVal(dim, 'fit_class')}</span>
                    ) : getVal(dim, 'tolerance_type') === 'limit' ? (
                      `+${getVal(dim, 'upper_tol')} / ${getVal(dim, 'lower_tol')}`
                    ) : (
                      `± ${getVal(dim, 'upper_tol')}`
                    )}
                  </td>

                  {/* Calculated Limits (Read Only) */}
                  <td className="p-2 border-r border-[#2a2a2a] font-mono text-green-500/80 bg-green-900/10">
                    {typeof getVal(dim, 'min_limit') === 'number' ? getVal(dim, 'min_limit').toFixed(4) : '-'}
                  </td>
                  <td className="p-2 border-r border-[#2a2a2a] font-mono text-green-500/80 bg-green-900/10">
                    {typeof getVal(dim, 'max_limit') === 'number' ? getVal(dim, 'max_limit').toFixed(4) : '-'}
                  </td>

                  {/* Fit Class (Editable) */}
                  <td className="p-0 border-r border-[#2a2a2a]">
                    <input 
                      className="w-full h-full p-2 bg-transparent border-none outline-none focus:bg-[#000] text-purple-400 font-bold text-center"
                      value={getVal(dim, 'fit_class')}
                      placeholder="-"
                      onChange={(e) => handleChange(dim.id, 'fit_class', e.target.value)}
                    />
                  </td>

                  {/* Method (Editable) */}
                  <td className="p-0 border-r border-[#2a2a2a]">
                    <select 
                      className="w-full h-full p-2 bg-transparent border-none outline-none text-blue-400 focus:bg-[#000]"
                      value={getVal(dim, 'inspection_method', '')}
                      onChange={(e) => handleChange(dim.id, 'inspection_method', e.target.value)}
                    >
                      <option value="">(None)</option>
                      <option value="CMM">CMM</option>
                      <option value="Caliper">Caliper</option>
                      <option value="Micrometer">Micrometer</option>
                      <option value="Visual">Visual</option>
                      <option value="Gage Block">Gage Block</option>
                    </select>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
