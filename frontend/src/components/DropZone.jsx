/**
 * DropZone.jsx - UPDATED with UX Improvements
 * 
 * THREE FIXES IMPLEMENTED:
 * 1. Tooltip stays visible when moving from balloon to tooltip (invisible bridge)
 * 2. Add Balloon mode: click button → draw rectangle → enter value → balloon created
 * 3. Clear Area mode: click button → draw rectangle → balloons inside deleted
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useUsage } from '../hooks/useUsage';
import { API_BASE_URL, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS } from '../constants/config';
import { GlassWallPaywall } from './GlassWallPaywall';
import { PreviewWatermark } from './PreviewWatermark';

// ============ HELPER FUNCTION ============
function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}

// ============ MAIN DROPZONE COMPONENT ============
export function DropZone({ onBeforeProcess, hasPromoAccess = false, userEmail = '' }) {
  const { token, isPro } = useAuth();
  const { visitorId, incrementUsage, usage, refreshUsage } = useUsage();
  const fileInputRef = useRef(null);
  const canDownload = isPro || hasPromoAccess;
  
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [showGlassWall, setShowGlassWall] = useState(false);
  const [showRevisionCompare, setShowRevisionCompare] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => { if (refreshUsage) refreshUsage(); }, []);

  const handleDragEnter = useCallback((e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }, []);
  const handleDragOver = useCallback((e) => { e.preventDefault(); e.stopPropagation(); }, []);

  const validateFile = (file) => {
    if (!file) return 'No file selected';
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) return `Unsupported format. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) return `File too large. Maximum: ${MAX_FILE_SIZE_MB}MB`;
    return null;
  };

  const processFile = async (file) => {
    const validationError = validateFile(file);
    if (validationError) { setError(validationError); return; }
    if (onBeforeProcess && !onBeforeProcess()) return;
    setIsProcessing(true);
    setError(null);
    setResult(null);
    setCurrentPage(1);
    setTotalPages(1);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (!token) formData.append('visitor_id', visitorId);
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const response = await fetch(`${API_BASE_URL}/process`, { method: 'POST', headers, body: formData });
      const data = await response.json();
      if (data.success) {
        if (data.pages && data.pages.length > 0) {
          setTotalPages(data.total_pages || data.pages.length);
          setCurrentPage(1);
        }
        setResult(data);
        await incrementUsage();
        if (refreshUsage) await refreshUsage();
      } else {
        setError(data.error?.message || 'Processing failed');
      }
    } catch (err) {
      setError('Network error. Please check your connection.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false);
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) processFile(files[0]);
  }, [token, visitorId, onBeforeProcess, usage]);

  const handleFileChange = (e) => { if (e.target.files?.[0]) processFile(e.target.files[0]); };
  const handleClick = () => { fileInputRef.current?.click(); };
  const handleReset = () => { setResult(null); setError(null); setCurrentPage(1); setTotalPages(1); };

  const handleRevisionCompareResult = async (comparisonData) => {
    await incrementUsage();
    if (refreshUsage) await refreshUsage();
    setResult(comparisonData);
    setShowRevisionCompare(false);
  };

  const getTotalDimensionCount = () => {
    if (!result) return 0;
    if (result.pages && result.pages.length > 0) {
      return result.pages.reduce((sum, p) => sum + (p.dimensions?.length || 0), 0);
    }
    return result.dimensions?.length || 0;
  };

  if (showRevisionCompare) {
    return (
      <RevisionCompare 
        onClose={() => setShowRevisionCompare(false)} 
        onComplete={handleRevisionCompareResult} 
        visitorId={visitorId} 
        incrementUsage={incrementUsage} 
        isPro={canDownload} 
        onShowGlassWall={() => setShowGlassWall(true)} 
      />
    );
  }
  
  if (result) {
    return (
      <>
        <GlassWallPaywall 
          isOpen={showGlassWall}
          onClose={() => setShowGlassWall(false)}
          dimensionCount={getTotalDimensionCount()}
          estimatedHours={(getTotalDimensionCount() * 1 + 10) / 60}
        />
        <BlueprintViewer 
          result={result} 
          onReset={handleReset} 
          token={token}
          isPro={canDownload}
          onShowGlassWall={() => setShowGlassWall(true)}
          currentPage={currentPage} 
          setCurrentPage={setCurrentPage} 
          totalPages={totalPages} 
        />
      </>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <button onClick={() => setShowRevisionCompare(true)} className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl transition-all text-sm flex items-center gap-2 font-medium shadow-lg">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          Compare Revisions (Delta FAI)
        </button>
      </div>
      <div
        className={`relative border-2 border-dashed rounded-xl p-12 transition-all duration-200 cursor-pointer ${isDragging ? 'border-[#E63946] bg-[#E63946]/10' : 'border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#1a1a1a]'} ${isProcessing ? 'pointer-events-none' : ''}`}
        onDragEnter={handleDragEnter} onDragLeave={handleDragLeave} onDragOver={handleDragOver} onDrop={handleDrop} onClick={handleClick}
      >
        <input ref={fileInputRef} type="file" accept={ALLOWED_EXTENSIONS.join(',')} onChange={handleFileChange} className="hidden" />
        {isProcessing ? (
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-[#E63946] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-xl font-medium text-white mb-2">Processing...</p>
            <p className="text-gray-400 text-sm">Detecting dimensions, this may take a moment for multi-page PDFs</p>
          </div>
        ) : (
          <div className="text-center">
            <div className={`w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center ${isDragging ? 'bg-[#E63946]/20' : 'bg-[#1a1a1a]'}`}>
              <svg className={`w-10 h-10 ${isDragging ? 'text-[#E63946]' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-xl font-medium text-white mb-2">{isDragging ? 'Drop your file here' : 'Drag & drop your blueprint'}</p>
            <p className="text-gray-400 mb-4">or <span className="text-[#E63946]">click to browse</span></p>
            <p className="text-gray-500 text-sm">PDF (multi-page supported), PNG, JPEG, TIFF - Max {MAX_FILE_SIZE_MB}MB</p>
          </div>
        )}
        {error && <div className="absolute inset-x-0 bottom-4 text-center"><p className="text-red-500 text-sm">{error}</p></div>}
      </div>
    </div>
  );
}

// ============ BLUEPRINT VIEWER - MAIN COMPONENT WITH UX IMPROVEMENTS ============
function BlueprintViewer({ result, onReset, token, isPro, onShowGlassWall, currentPage, setCurrentPage, totalPages: initialTotalPages }) {
  const [isDownloading, setIsDownloading] = useState(false);
  
  // Multi-page support
  const hasMultiplePages = result.pages && result.pages.length > 1;
  const totalPages = hasMultiplePages ? result.pages.length : (initialTotalPages || 1);
  
  const getCurrentPageData = () => {
    if (hasMultiplePages) {
      return result.pages.find(p => p.page_number === currentPage) || result.pages[0];
    }
    return { image: result.image, dimensions: result.dimensions || [], grid_detected: result.grid?.detected };
  };
  
  const currentPageData = getCurrentPageData();
  const currentImage = hasMultiplePages 
    ? `data:image/png;base64,${currentPageData.image}` 
    : (currentPageData.image?.startsWith('data:') ? currentPageData.image : `data:image/png;base64,${currentPageData.image}`);
  
  const getPageDimensions = () => {
    if (hasMultiplePages) return currentPageData.dimensions || [];
    return result.dimensions || [];
  };
  
  const [dimensions, setDimensions] = useState(() => 
    getPageDimensions().map(d => ({
      ...d,
      anchorX: (d.bounding_box.xmin + d.bounding_box.xmax) / 2 / 10,
      anchorY: (d.bounding_box.ymin + d.bounding_box.ymax) / 2 / 10,
      balloonX: (d.bounding_box.xmin + d.bounding_box.xmax) / 2 / 10 + 4,
      balloonY: (d.bounding_box.ymin + d.bounding_box.ymax) / 2 / 10 - 4,
    }))
  );
  
  useEffect(() => {
    const pageDims = getPageDimensions();
    setDimensions(pageDims.map(d => ({
      ...d,
      anchorX: (d.bounding_box.xmin + d.bounding_box.xmax) / 2 / 10,
      anchorY: (d.bounding_box.ymin + d.bounding_box.ymax) / 2 / 10,
      balloonX: (d.bounding_box.xmin + d.bounding_box.xmax) / 2 / 10 + 4,
      balloonY: (d.bounding_box.ymin + d.bounding_box.ymax) / 2 / 10 - 4,
    })));
  }, [currentPage, result]);
  
  // ===== UX IMPROVEMENT: Drawing mode state =====
  const [drawMode, setDrawMode] = useState(null); // null | 'addBalloon' | 'clearArea'
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState(null);
  const [drawEnd, setDrawEnd] = useState(null);
  const [showValueInput, setShowValueInput] = useState(false);
  const [newBalloonRect, setNewBalloonRect] = useState(null);
  const [newBalloonValue, setNewBalloonValue] = useState('');
  
  const [showCMMImport, setShowCMMImport] = useState(false);
  const [cmmResults, setCmmResults] = useState({});
  const containerRef = useRef(null);
  const imageRef = useRef(null);
  
  const getTotalDimensions = () => {
    if (hasMultiplePages) return result.pages.reduce((sum, p) => sum + (p.dimensions?.length || 0), 0);
    return result.dimensions?.length || 0;
  };
  
  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (showValueInput) {
          setShowValueInput(false);
          setNewBalloonRect(null);
          setNewBalloonValue('');
        } else if (drawMode) {
          setDrawMode(null);
          setIsDrawing(false);
          setDrawStart(null);
          setDrawEnd(null);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [drawMode, showValueInput]);
  
  // ===== Rectangle Drawing Handlers =====
  const handleMouseDown = (e) => {
    if (!drawMode || !containerRef.current) return;
    e.preventDefault();
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setIsDrawing(true);
    setDrawStart({ x, y });
    setDrawEnd({ x, y });
  };
  
  const handleMouseMove = (e) => {
    if (!isDrawing || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));
    setDrawEnd({ x, y });
  };
  
  const handleMouseUp = () => {
    if (!isDrawing || !drawStart || !drawEnd) {
      setIsDrawing(false);
      return;
    }
    setIsDrawing(false);
    
    const minX = Math.min(drawStart.x, drawEnd.x);
    const maxX = Math.max(drawStart.x, drawEnd.x);
    const minY = Math.min(drawStart.y, drawEnd.y);
    const maxY = Math.max(drawStart.y, drawEnd.y);
    
    // Minimum size check
    if (maxX - minX < 1 || maxY - minY < 1) {
      setDrawStart(null);
      setDrawEnd(null);
      return;
    }
    
    if (drawMode === 'addBalloon') {
      setNewBalloonRect({ minX, maxX, minY, maxY });
      setShowValueInput(true);
      setDrawMode(null);
    } else if (drawMode === 'clearArea') {
      setDimensions(prev => prev.filter(d => {
        const isInside = d.balloonX >= minX && d.balloonX <= maxX && d.balloonY >= minY && d.balloonY <= maxY;
        return !isInside;
      }));
      setDrawMode(null);
    }
    
    setDrawStart(null);
    setDrawEnd(null);
  };
  
  const handleAddBalloonConfirm = () => {
    if (!newBalloonRect || !newBalloonValue.trim()) {
      setShowValueInput(false);
      setNewBalloonRect(null);
      setNewBalloonValue('');
      return;
    }
    
    const { minX, maxX, minY, maxY } = newBalloonRect;
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    
    // Calculate zone (8x4 grid)
    const x = centerX * 10;
    const y = centerY * 10;
    const colIndex = Math.floor(x / 125);
    const rowIndex = Math.floor(y / 250);
    const columns = ["H", "G", "F", "E", "D", "C", "B", "A"];
    const rows = ["4", "3", "2", "1"];
    const zone = `${columns[Math.min(colIndex, 7)]}${rows[Math.min(rowIndex, 3)]}`;
    
    const newId = dimensions.length > 0 ? Math.max(...dimensions.map(d => d.id)) + 1 : 1;
    
    setDimensions(prev => [...prev, {
      id: newId,
      value: newBalloonValue.trim(),
      zone,
      page: currentPage,
      bounding_box: { xmin: x - 20, xmax: x + 20, ymin: y - 10, ymax: y + 10 },
      anchorX: centerX,
      anchorY: centerY,
      balloonX: centerX + 4,
      balloonY: centerY - 4,
    }]);
    
    setShowValueInput(false);
    setNewBalloonRect(null);
    setNewBalloonValue('');
  };
  
  // Download handlers
  const handleDownloadPDF = async () => {
    if (!isPro) { onShowGlassWall(); return; }
    setIsDownloading(true);
    try {
      const payload = {
        pages: hasMultiplePages 
          ? result.pages.map(p => ({ page_number: p.page_number, image: p.image, width: p.width || 1700, height: p.height || 2200, dimensions: p.dimensions || [] }))
          : [{ page_number: 1, image: result.image?.replace(/^data:image\/\w+;base64,/, '') || '', width: result.metadata?.width || 1700, height: result.metadata?.height || 2200, dimensions: result.dimensions || [] }],
        part_number: result.metadata?.part_number || '',
        revision: result.metadata?.revision || '',
      };
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/download/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { 'Authorization': `Bearer ${token}` }) },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        const blob = await response.blob();
        const filename = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'ballooned_drawing.pdf';
        downloadBlob(blob, filename);
      }
    } catch (err) { console.error('PDF download failed:', err); }
    finally { setIsDownloading(false); }
  };

  const handleDownloadZIP = async () => {
    if (!isPro) { onShowGlassWall(); return; }
    setIsDownloading(true);
    try {
      const payload = {
        pages: hasMultiplePages 
          ? result.pages.map(p => ({ page_number: p.page_number, image: p.image, width: p.width || 1700, height: p.height || 2200, dimensions: p.dimensions || [] }))
          : [{ page_number: 1, image: result.image?.replace(/^data:image\/\w+;base64,/, '') || '', width: result.metadata?.width || 1700, height: result.metadata?.height || 2200, dimensions: result.dimensions || [] }],
        part_number: result.metadata?.part_number || '',
        revision: result.metadata?.revision || '',
      };
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/download/zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { 'Authorization': `Bearer ${token}` }) },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        const blob = await response.blob();
        downloadBlob(blob, 'FAI_package.zip');
      }
    } catch (err) { console.error('ZIP download failed:', err); }
    finally { setIsDownloading(false); }
  };

  const handleDownloadExcel = async () => {
    if (!isPro) { onShowGlassWall(); return; }
    setIsDownloading(true);
    try {
      const payload = {
        pages: hasMultiplePages 
          ? result.pages.map(p => ({ page_number: p.page_number, dimensions: p.dimensions || [] }))
          : [{ page_number: 1, dimensions: result.dimensions || [] }],
        part_number: result.metadata?.part_number || '',
      };
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/download/excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { 'Authorization': `Bearer ${token}` }) },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        const blob = await response.blob();
        downloadBlob(blob, 'AS9102_Form3.xlsx');
      }
    } catch (err) { console.error('Excel download failed:', err); }
    finally { setIsDownloading(false); }
  };

  const handleDeleteDimension = (id) => { setDimensions(prev => prev.filter(d => d.id !== id)); };

  const handleBalloonDrag = (id, deltaX, deltaY) => {
    setDimensions(prev => prev.map(d => {
      if (d.id !== id) return d;
      return { ...d, anchorX: d.anchorX + deltaX, anchorY: d.anchorY + deltaY, balloonX: d.balloonX + deltaX, balloonY: d.balloonY + deltaY };
    }));
  };

  const getSelectionRect = () => {
    if (!isDrawing || !drawStart || !drawEnd) return null;
    return {
      left: `${Math.min(drawStart.x, drawEnd.x)}%`,
      top: `${Math.min(drawStart.y, drawEnd.y)}%`,
      width: `${Math.abs(drawEnd.x - drawStart.x)}%`,
      height: `${Math.abs(drawEnd.y - drawStart.y)}%`,
    };
  };

  const selectionRect = getSelectionRect();

  return (
    <div className="space-y-6">
      {showCMMImport && <CMMImportModal dimensions={dimensions} onClose={() => setShowCMMImport(false)} onImport={(r) => { setCmmResults(r); setShowCMMImport(false); }} />}
      
      {/* Value Input Popup */}
      {showValueInput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6 w-80">
            <h3 className="text-white font-medium mb-4">Enter Dimension Value</h3>
            <input
              type="text"
              value={newBalloonValue}
              onChange={(e) => setNewBalloonValue(e.target.value)}
              placeholder="e.g., 1.250in, Ø5mm..."
              className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg text-white text-sm mb-4"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddBalloonConfirm();
                if (e.key === 'Escape') { setShowValueInput(false); setNewBalloonRect(null); setNewBalloonValue(''); }
              }}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setShowValueInput(false); setNewBalloonRect(null); setNewBalloonValue(''); }} className="px-4 py-2 text-gray-400 hover:text-white text-sm">Cancel</button>
              <button onClick={handleAddBalloonConfirm} className="px-4 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white rounded-lg text-sm">Add Balloon</button>
            </div>
          </div>
        </div>
      )}
      
      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <button onClick={onReset} className="text-gray-400 hover:text-white transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            New Upload
          </button>
          <div className="h-6 w-px bg-[#2a2a2a]" />
          
          <span className="text-sm">
            <span className="text-gray-400">This page: </span>
            <span className="text-white font-medium">{dimensions.length} dimensions</span>
            {totalPages > 1 && <span className="text-gray-500 ml-2">({getTotalDimensions()} total)</span>}
          </span>
          
          <div className="h-6 w-px bg-[#2a2a2a]" />
          
          {/* ===== UX FIX #2: Add Balloon Button ===== */}
          <button
            onClick={() => setDrawMode(drawMode === 'addBalloon' ? null : 'addBalloon')}
            className={`px-3 py-1.5 rounded-lg transition-colors text-sm flex items-center gap-2 ${drawMode === 'addBalloon' ? 'bg-[#E63946] text-white' : 'bg-[#1a1a1a] hover:bg-[#252525] text-gray-300'}`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            {drawMode === 'addBalloon' ? 'Cancel' : 'Add Balloon'}
          </button>
          
          {/* ===== UX FIX #3: Clear Area Button ===== */}
          <button
            onClick={() => setDrawMode(drawMode === 'clearArea' ? null : 'clearArea')}
            className={`px-3 py-1.5 rounded-lg transition-colors text-sm flex items-center gap-2 ${drawMode === 'clearArea' ? 'bg-red-600 text-white' : 'bg-[#1a1a1a] hover:bg-[#252525] text-gray-300'}`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            {drawMode === 'clearArea' ? 'Cancel' : 'Clear Area'}
          </button>
        </div>
        
        <div className="flex items-center gap-3">
          <button onClick={() => setShowCMMImport(true)} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            Import CMM
          </button>
          <DownloadMenu onDownloadPDF={handleDownloadPDF} onDownloadZIP={handleDownloadZIP} onDownloadExcel={handleDownloadExcel} isDownloading={isDownloading} totalPages={totalPages} totalDimensions={getTotalDimensions()} isPro={isPro} />
        </div>
      </div>

      {/* Mode indicator */}
      <div className="bg-[#1a1a1a] rounded-lg px-3 py-2 text-sm text-gray-400 flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        {drawMode === 'addBalloon' ? (
          <span className="text-[#E63946]">Draw a rectangle over the area you want to balloon. Press Escape to cancel.</span>
        ) : drawMode === 'clearArea' ? (
          <span className="text-red-400">Draw a rectangle over the balloons you want to delete. Press Escape to cancel.</span>
        ) : (
          <span>Hover over balloons to see details. Drag to reposition.</span>
        )}
      </div>

      {/* Canvas Area */}
      <div
        ref={containerRef}
        className={`relative bg-[#0a0a0a] rounded-xl overflow-hidden select-none ${drawMode ? 'cursor-crosshair' : ''}`}
        style={{ minHeight: '500px' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => { if (isDrawing) { setIsDrawing(false); setDrawStart(null); setDrawEnd(null); } }}
      >
        {currentImage && <img ref={imageRef} src={currentImage} alt={`Blueprint Page ${currentPage}`} className="w-full h-auto pointer-events-none" crossOrigin="anonymous" />}
        
        {/* Leader lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {dimensions.map((dim) => (
            <g key={`leader-${dim.id}`}>
              <line x1={`${dim.anchorX}%`} y1={`${dim.anchorY - 0.8}%`} x2={`${dim.balloonX}%`} y2={`${dim.balloonY}%`} stroke="#E63946" strokeWidth="2" />
              <circle cx={`${dim.anchorX}%`} cy={`${dim.anchorY - 0.8}%`} r="2.5" fill="#E63946" />
            </g>
          ))}
        </svg>
        
        {/* Balloons with UX FIX #1: Tooltip bridge */}
        {dimensions.map((dim) => (
          <DraggableBalloon
            key={dim.id}
            dimension={dim}
            left={dim.balloonX}
            top={dim.balloonY}
            onDelete={() => handleDeleteDimension(dim.id)}
            onDrag={handleBalloonDrag}
            cmmResult={cmmResults[dim.id]}
            containerRef={containerRef}
            disabled={drawMode !== null}
          />
        ))}
        
        {/* Selection rectangle */}
        {selectionRect && (
          <div
            className={`absolute border-2 border-dashed pointer-events-none ${drawMode === 'addBalloon' ? 'border-[#E63946] bg-[#E63946]/10' : 'border-red-500 bg-red-500/10'}`}
            style={selectionRect}
          />
        )}
        
        {!isPro && <PreviewWatermark isVisible={true} />}
      </div>

      {/* Dimensions Table */}
      <div className="bg-[#0a0a0a] rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-[#1a1a1a] border-b border-[#2a2a2a] flex items-center justify-between">
          <h3 className="font-medium text-white">Dimensions {totalPages > 1 ? `(Page ${currentPage})` : ''}</h3>
        </div>
        <div className="max-h-64 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#161616] sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">#</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Zone</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Nominal</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Actual</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Status</th>
                <th className="px-4 py-2 text-right text-gray-400 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {dimensions.map((dim) => (
                <tr key={dim.id} className="border-b border-[#1a1a1a] hover:bg-[#161616]">
                  <td className="px-4 py-2 text-white">{dim.id}</td>
                  <td className="px-4 py-2 text-gray-300">{dim.zone || '-'}</td>
                  <td className="px-4 py-2 text-white font-mono">{dim.value}</td>
                  <td className="px-4 py-2 text-white font-mono">{cmmResults[dim.id]?.actual || '-'}</td>
                  <td className="px-4 py-2">
                    {cmmResults[dim.id]?.status && (
                      <span className={`px-2 py-1 rounded text-xs ${cmmResults[dim.id].status === 'PASS' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                        {cmmResults[dim.id].status}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button onClick={() => handleDeleteDimension(dim.id)} className="text-gray-500 hover:text-red-500">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {dimensions.length === 0 && <div className="px-4 py-8 text-center text-gray-500">No dimensions on this page.</div>}
        </div>
      </div>
    </div>
  );
}

// ============ DRAGGABLE BALLOON - UX FIX #1: Tooltip stays visible ============
function DraggableBalloon({ dimension, left, top, onDelete, onDrag, cmmResult, containerRef, disabled = false }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const startPos = useRef({ x: 0, y: 0 });
  const hasResult = cmmResult?.actual;
  const isPassing = cmmResult?.status === 'PASS';

  const handleMouseDown = (e) => {
    if (disabled) return;
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
    startPos.current = { x: e.clientX, y: e.clientY };
    
    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const deltaX = ((e.clientX - startPos.current.x) / rect.width) * 100;
      const deltaY = ((e.clientY - startPos.current.y) / rect.height) * 100;
      startPos.current = { x: e.clientX, y: e.clientY };
      onDrag(dimension.id, deltaX, deltaY);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  /**
   * UX FIX #1: Tooltip stays visible when moving from balloon to tooltip
   * 
   * The container tracks hover state for both balloon AND tooltip.
   * CSS padding creates an invisible "bridge" between them.
   */
  return (
    <div
      className={`absolute transform -translate-x-1/2 -translate-y-1/2 ${isDragging ? 'cursor-grabbing z-50' : disabled ? '' : 'cursor-grab'}`}
      style={{ left: `${left}%`, top: `${top}%`, zIndex: isHovered || isDragging ? 100 : 10 }}
      onMouseEnter={() => !disabled && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Balloon circle */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-lg ${
          hasResult 
            ? (isPassing ? 'bg-green-500 text-white border-2 border-green-400' : 'bg-red-500 text-white border-2 border-red-400') 
            : (isHovered || isDragging ? 'bg-[#E63946] text-white scale-110' : 'bg-white text-[#E63946] border-2 border-[#E63946]')
        }`}
        onMouseDown={handleMouseDown}
      >
        {dimension.id}
      </div>
      
      {/* Tooltip with invisible bridge (padding) */}
      {isHovered && !isDragging && !disabled && (
        <div className="absolute left-full top-1/2 -translate-y-1/2 flex items-center" style={{ paddingLeft: '8px' }}>
          <div className="bg-[#161616] border border-[#2a2a2a] rounded-lg px-3 py-2 whitespace-nowrap shadow-xl min-w-[120px]">
            <div className="text-white font-mono text-sm mb-1">{dimension.value}</div>
            {dimension.zone && <div className="text-gray-400 text-xs">Zone: {dimension.zone}</div>}
            {cmmResult?.actual && <div className="text-blue-400 text-xs mt-1">Actual: {cmmResult.actual}</div>}
            {cmmResult?.status && <div className={`text-xs ${cmmResult.status === 'PASS' ? 'text-green-400' : 'text-red-400'}`}>{cmmResult.status}</div>}
            <button onClick={(e) => { e.stopPropagation(); onDelete(); }} className="text-red-500 text-xs hover:text-red-400 hover:underline mt-2 block">Delete</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============ DOWNLOAD MENU ============
function DownloadMenu({ onDownloadPDF, onDownloadZIP, onDownloadExcel, isDownloading, totalPages, totalDimensions, isPro }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setIsOpen(false); };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = (action) => { action(); setIsOpen(false); };

  return (
    <div className="relative" ref={menuRef}>
      <button onClick={() => setIsOpen(!isOpen)} disabled={isDownloading} className="flex items-center gap-2 px-4 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg transition-colors disabled:opacity-50">
        {isDownloading ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
        ) : !isPro ? (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
        )}
        <span>{isDownloading ? 'Preparing...' : (isPro ? 'Download' : 'Export (Pro)')}</span>
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>

      {isOpen && !isDownloading && (
        <div className="absolute right-0 mt-2 w-72 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl shadow-2xl overflow-hidden z-50">
          <div className="px-4 py-3 border-b border-[#2a2a2a] bg-[#161616]">
            <p className="text-sm font-medium text-white">Export Options</p>
            <p className="text-xs text-gray-400 mt-0.5">{totalPages} page{totalPages !== 1 ? 's' : ''} • {totalDimensions} dimensions</p>
          </div>
          <div className="p-2">
            <button onClick={() => handleDownload(onDownloadPDF)} className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] text-left group">
              <div className="p-2 rounded-lg bg-[#E63946]/10 text-[#E63946]"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
              <div className="flex-1"><p className="text-sm font-medium text-white">Ballooned PDF</p><p className="text-xs text-gray-400">All pages with balloon markers</p></div>
            </button>
            <button onClick={() => handleDownload(onDownloadZIP)} className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] text-left group">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg></div>
              <div className="flex-1"><p className="text-sm font-medium text-white">FAI Package (ZIP)</p><p className="text-xs text-gray-400">Images + AS9102 Excel + README</p></div>
              {isPro && <span className="text-[10px] font-medium text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full self-center">RECOMMENDED</span>}
            </button>
            <button onClick={() => handleDownload(onDownloadExcel)} className="w-full flex items-start gap-3 p-3 rounded-lg hover:bg-[#252525] text-left group">
              <div className="p-2 rounded-lg bg-green-500/10 text-green-400"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></div>
              <div className="flex-1"><p className="text-sm font-medium text-white">AS9102 Excel Only</p><p className="text-xs text-gray-400">Form 3 spreadsheet</p></div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============ CMM IMPORT MODAL ============
function CMMImportModal({ dimensions, onClose, onImport }) {
  const [csvData, setCsvData] = useState(null);
  const [mappings, setMappings] = useState([]);
  const fileInputRef = useRef(null);

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    return lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const row = {};
      headers.forEach((h, i) => row[h] = values[i] || '');
      return row;
    });
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const data = parseCSV(event.target.result);
      setCsvData(data);
      const autoMappings = data.map((row, idx) => {
        const featureNum = row.feature || row.id || row['feature #'] || (idx + 1).toString();
        const match = dimensions.find(d => d.id.toString() === featureNum.toString());
        return { cmmIndex: idx, cmmData: row, matchedBalloon: match?.id || null, actualValue: row.actual || row.measured || '', status: row.status || '' };
      });
      setMappings(autoMappings);
    };
    reader.readAsText(file);
  };

  const matchedCount = mappings.filter(m => m.matchedBalloon).length;

  const handleImport = () => {
    const results = {};
    mappings.forEach(m => { if (m.matchedBalloon) results[m.matchedBalloon] = { actual: m.actualValue, status: m.status }; });
    onImport(results);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center">
          <div><h2 className="text-xl font-bold text-white">Import CMM Results</h2><p className="text-gray-400 text-sm">Upload your CMM CSV to auto-fill measurements</p></div>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
        </div>
        <div className="flex-1 overflow-auto p-6">
          {!csvData ? (
            <div className="border-2 border-dashed border-[#2a2a2a] rounded-xl p-12 text-center cursor-pointer hover:border-[#3a3a3a]" onClick={() => fileInputRef.current?.click()}>
              <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileUpload} className="hidden" />
              <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
              <p className="text-white font-medium mb-2">Upload CMM CSV File</p>
              <p className="text-gray-500 text-sm">Supports standard CMM export formats</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-green-500 font-medium">{matchedCount} of {mappings.length} matched</span>
                <button onClick={() => { setCsvData(null); setMappings([]); }} className="text-gray-400 hover:text-white text-sm">Upload different file</button>
              </div>
              <div className="bg-[#0a0a0a] rounded-xl overflow-hidden max-h-64">
                <table className="w-full text-sm">
                  <thead className="bg-[#1a1a1a] sticky top-0"><tr><th className="px-4 py-3 text-left text-gray-400">CMM Feature</th><th className="px-4 py-3 text-left text-gray-400">Actual</th><th className="px-4 py-3 text-left text-gray-400">Match to Balloon</th><th className="px-4 py-3 text-left text-gray-400">Status</th></tr></thead>
                  <tbody>
                    {mappings.map((m, idx) => (
                      <tr key={idx} className="border-t border-[#1a1a1a]">
                        <td className="px-4 py-3 text-white">{m.cmmData.feature || m.cmmData.id || `Row ${idx + 1}`}</td>
                        <td className="px-4 py-3 text-white font-mono">{m.actualValue || '-'}</td>
                        <td className="px-4 py-3">
                          <select value={m.matchedBalloon || ''} onChange={(e) => setMappings(prev => prev.map((p, i) => i === idx ? { ...p, matchedBalloon: e.target.value ? parseInt(e.target.value) : null } : p))} className="bg-[#1a1a1a] border border-[#2a2a2a] rounded px-2 py-1 text-white text-sm">
                            <option value="">No match</option>
                            {dimensions.map(d => <option key={d.id} value={d.id}>#{d.id} - {d.value}</option>)}
                          </select>
                        </td>
                        <td className="px-4 py-3">{m.status && <span className={`px-2 py-1 rounded text-xs ${m.status === 'PASS' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{m.status}</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
        {csvData && (
          <div className="px-6 py-4 border-t border-[#2a2a2a] flex justify-end gap-3">
            <button onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white">Cancel</button>
            <button onClick={handleImport} disabled={matchedCount === 0} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50">Import {matchedCount} Results</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ============ REVISION COMPARE ============
function RevisionCompare({ onClose, onComplete, visitorId, incrementUsage, isPro, onShowGlassWall }) {
  const [revA, setRevA] = useState(null);
  const [revB, setRevB] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);
  const fileInputARef = useRef(null);
  const fileInputBRef = useRef(null);

  const handleFileSelect = (file, setRev) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => setRev({ file, name: file.name, preview: e.target.result });
    reader.readAsDataURL(file);
  };

  const handleCompare = async () => {
    if (!revA || !revB) return;
    setIsComparing(true);
    try {
      const [formDataA, formDataB] = [new FormData(), new FormData()];
      formDataA.append('file', revA.file);
      formDataB.append('file', revB.file);
      const [responseA, responseB] = await Promise.all([
        fetch(`${API_BASE_URL}/process`, { method: 'POST', body: formDataA }),
        fetch(`${API_BASE_URL}/process`, { method: 'POST', body: formDataB })
      ]);
      const [dataA, dataB] = await Promise.all([responseA.json(), responseB.json()]);
      if (dataA.success && dataB.success) {
        const dimsA = dataA.dimensions || [];
        const dimsB = dataB.dimensions || [];
        const changes = { added: [], removed: [], modified: [], unchanged: [] };
        const TOLERANCE = 20;
        
        dimsB.forEach(dimB => {
          const centerBX = (dimB.bounding_box.xmin + dimB.bounding_box.xmax) / 2;
          const centerBY = (dimB.bounding_box.ymin + dimB.bounding_box.ymax) / 2;
          const matchA = dimsA.find(dimA => {
            const centerAX = (dimA.bounding_box.xmin + dimA.bounding_box.xmax) / 2;
            const centerAY = (dimA.bounding_box.ymin + dimA.bounding_box.ymax) / 2;
            return Math.abs(centerAX - centerBX) < TOLERANCE && Math.abs(centerAY - centerBY) < TOLERANCE;
          });
          if (!matchA) changes.added.push({ ...dimB, changeType: 'added' });
          else if (matchA.value !== dimB.value) changes.modified.push({ ...dimB, changeType: 'modified', oldValue: matchA.value, newValue: dimB.value });
          else changes.unchanged.push({ ...dimB, changeType: 'unchanged' });
        });
        
        dimsA.forEach(dimA => {
          const centerAX = (dimA.bounding_box.xmin + dimA.bounding_box.xmax) / 2;
          const centerAY = (dimA.bounding_box.ymin + dimA.bounding_box.ymax) / 2;
          const matchB = dimsB.find(dimB => {
            const centerBX = (dimB.bounding_box.xmin + dimB.bounding_box.xmax) / 2;
            const centerBY = (dimB.bounding_box.ymin + dimB.bounding_box.ymax) / 2;
            return Math.abs(centerAX - centerBX) < TOLERANCE && Math.abs(centerAY - centerBY) < TOLERANCE;
          });
          if (!matchB) changes.removed.push({ ...dimA, changeType: 'removed' });
        });
        
        setComparisonResult({ revA: dataA, revB: dataB, changes, summary: { added: changes.added.length, removed: changes.removed.length, modified: changes.modified.length, unchanged: changes.unchanged.length } });
      }
    } catch (err) { console.error('Comparison failed:', err); }
    finally { setIsComparing(false); }
  };

  const handleUseChanges = () => {
    if (!isPro) { onShowGlassWall(); return; }
    if (comparisonResult && onComplete) {
      const changedDimensions = [...comparisonResult.changes.added, ...comparisonResult.changes.modified].map((dim, idx) => ({ ...dim, id: idx + 1 }));
      onComplete({ dimensions: changedDimensions, image: comparisonResult.revB.image, metadata: comparisonResult.revB.metadata, comparison: comparisonResult });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-[#161616] rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-[#2a2a2a] flex justify-between items-center">
          <div><h2 className="text-xl font-bold text-white"><span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">Delta FAI</span> - Revision Compare</h2><p className="text-gray-400 text-sm">Upload two revisions to find what changed</p></div>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
        </div>
        <div className="flex-1 overflow-auto p-6">
          {!comparisonResult ? (
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2"><span className="w-6 h-6 rounded bg-gray-600 flex items-center justify-center text-xs">A</span>Old Revision</h3>
                <div className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${revA ? 'border-green-500/50 bg-green-500/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a]'}`} onClick={() => fileInputARef.current?.click()}>
                  <input ref={fileInputARef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => handleFileSelect(e.target.files[0], setRevA)} className="hidden" />
                  {revA ? (<div><img src={revA.preview} alt="Rev A" className="max-h-48 mx-auto rounded mb-2" /><p className="text-green-400 text-sm">{revA.name}</p></div>) : (<div><svg className="w-10 h-10 text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg><p className="text-gray-400">Upload Rev A</p></div>)}
                </div>
              </div>
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2"><span className="w-6 h-6 rounded bg-[#E63946] flex items-center justify-center text-xs text-white">B</span>New Revision</h3>
                <div className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${revB ? 'border-[#E63946]/50 bg-[#E63946]/5' : 'border-[#2a2a2a] hover:border-[#3a3a3a]'}`} onClick={() => fileInputBRef.current?.click()}>
                  <input ref={fileInputBRef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={(e) => handleFileSelect(e.target.files[0], setRevB)} className="hidden" />
                  {revB ? (<div><img src={revB.preview} alt="Rev B" className="max-h-48 mx-auto rounded mb-2" /><p className="text-[#E63946] text-sm">{revB.name}</p></div>) : (<div><svg className="w-10 h-10 text-gray-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg><p className="text-gray-400">Upload Rev B</p></div>)}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-green-400">{comparisonResult.summary.added}</div><div className="text-green-400/70 text-sm">Added</div></div>
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-yellow-400">{comparisonResult.summary.modified}</div><div className="text-yellow-400/70 text-sm">Modified</div></div>
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-red-400">{comparisonResult.summary.removed}</div><div className="text-red-400/70 text-sm">Removed</div></div>
                <div className="bg-gray-500/10 border border-gray-500/30 rounded-xl p-4 text-center"><div className="text-3xl font-bold text-gray-400">{comparisonResult.summary.unchanged}</div><div className="text-gray-400/70 text-sm">Unchanged</div></div>
              </div>
            </div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-[#2a2a2a] flex justify-between">
          {!comparisonResult ? (
            <><div className="text-gray-500 text-sm">{revA && revB ? 'Ready to compare' : 'Upload both revisions'}</div>
            <button onClick={handleCompare} disabled={!revA || !revB || isComparing} className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg disabled:opacity-50 flex items-center gap-2">
              {isComparing ? <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Comparing...</> : 'Compare Revisions'}
            </button></>
          ) : (
            <><button onClick={() => setComparisonResult(null)} className="text-gray-400 hover:text-white">Compare Different Files</button>
            <button onClick={handleUseChanges} className="px-6 py-2 bg-[#E63946] hover:bg-[#c62d39] text-white font-medium rounded-lg">Balloon Only Changes ({comparisonResult.summary.added + comparisonResult.summary.modified})</button></>
          )}
        </div>
      </div>
    </div>
  );
}

export default DropZone;
