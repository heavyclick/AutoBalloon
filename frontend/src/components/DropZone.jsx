import React, { useState, useCallback, useRef, useEffect } from 'react';
import JSZip from 'jszip';
import { useAuth } from '../context/AuthContext';
import { useUsage } from '../hooks/useUsage';
import { API_BASE_URL, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS } from '../constants/config';

// Imported Components (The "Separation")
import { BlueprintViewer } from './BlueprintViewer';
import { TableManager } from './TableManager';
import { PropertiesPanel } from './PropertiesPanel';
import { RevisionCompare } from './RevisionCompare'; // You will create this file next
import { CMMImportModal } from './CMMImport';       // You will create this file next
import { GlassWallPaywall } from './GlassWallPaywall';

export function DropZone({ onBeforeProcess, hasPromoAccess = false }) {
  const { token, isPro } = useAuth();
  const { visitorId, incrementUsage, refreshUsage } = useUsage();
  
  // ============ STATE MANAGEMENT ============
  const [projectData, setProjectData] = useState({
    metadata: null,
    pages: [],           // Multi-page support
    dimensions: [],      // Form 3
    bom: [],            // Form 1 (New)
    specifications: [],  // Form 2 (New)
    cmmResults: {}       // CMM Data
  });

  const [uiState, setUiState] = useState({
    currentPage: 1,
    totalPages: 1,
    selectedDimId: null,
    isProcessing: false,
    isDragging: false,
    error: null,
    showGlassWall: false,
    showRevisionCompare: false,
    showCMMImport: false
  });

  const fileInputRef = useRef(null);
  const canDownload = isPro || hasPromoAccess;

  // ============ HANDLERS ============

  // 1. File Processing (Backend Call)
  const processFile = async (file) => {
    if (onBeforeProcess && !onBeforeProcess()) return;
    setUiState(prev => ({ ...prev, isProcessing: true, error: null }));

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (!token) formData.append('visitor_id', visitorId);

      // Sending to backend for Vector/OCR hybrid detection
      const response = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });
      
      const data = await response.json();
      
      if (data.success) {
        setProjectData(prev => ({
          ...prev,
          metadata: data.metadata,
          pages: data.pages || [],
          // Initialize dimensions with default "Visual" method if not set
          dimensions: (data.dimensions || []).map(d => ({...d, method: d.method || 'Visual'})), 
          bom: [], 
          specifications: []
        }));
        setUiState(prev => ({ 
          ...prev, 
          totalPages: data.total_pages || 1, 
          currentPage: 1 
        }));
        await incrementUsage();
      } else {
        setUiState(prev => ({ ...prev, error: data.error?.message || 'Processing failed' }));
      }
    } catch (err) {
      setUiState(prev => ({ ...prev, error: 'Network error.' }));
    } finally {
      setUiState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  // 2. State Updates (Passed to Children)
  const handleDimensionUpdate = (updatedDim) => {
    setProjectData(prev => ({
      ...prev,
      dimensions: prev.dimensions.map(d => d.id === updatedDim.id ? updatedDim : d)
    }));
  };

  const handleDimensionDelete = (id) => {
    setProjectData(prev => ({
      ...prev,
      dimensions: prev.dimensions.filter(d => d.id !== id)
    }));
    if (uiState.selectedDimId === id) setUiState(prev => ({ ...prev, selectedDimId: null }));
  };

  // 3. Project Saving (JSZip)
  const handleSaveProject = async () => {
    const zip = new JSZip();
    zip.file("state.json", JSON.stringify({ version: "2.0", ...projectData }));
    const blob = await zip.generateAsync({ type: "blob" });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${projectData.metadata?.filename || 'project'}.ab`;
    a.click();
  };

  // ============ RENDER ============

  if (uiState.showRevisionCompare) return (
    <RevisionCompare 
      onClose={() => setUiState(s => ({...s, showRevisionCompare: false}))}
      onPort={(portedData) => {
          // Handle the "Ported" data from the new RevisionCompare component
          setProjectData(prev => ({ ...prev, ...portedData }));
          setUiState(s => ({...s, showRevisionCompare: false}));
      }}
    />
  );

  // If no file loaded, show Drop Area
  if (!projectData.metadata && !projectData.dimensions.length) {
    return (
        /* ... (Keep your existing DropZone UI logic here for the drag-drop box) ... */
        <div 
          className="border-2 border-dashed border-[#333] rounded-xl p-12 text-center cursor-pointer hover:bg-[#1a1a1a]"
          onClick={() => fileInputRef.current.click()}
        >
            <input ref={fileInputRef} type="file" className="hidden" onChange={e => processFile(e.target.files[0])} />
            <p className="text-white">Click or Drag Blueprint to Begin</p>
            {uiState.isProcessing && <p className="text-blue-400 mt-2">Processing...</p>}
        </div>
    );
  }

  // Main Workspace Layout
  const currentPageData = projectData.pages.find(p => p.page_number === uiState.currentPage) || projectData;
  const currentDimensions = projectData.dimensions.filter(d => d.page === uiState.currentPage || !d.page);

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0a] overflow-hidden">
      
      {/* 1. Header / Toolbar */}
      <div className="h-14 border-b border-[#2a2a2a] flex items-center justify-between px-4 bg-[#161616]">
         <div className="flex items-center gap-4">
             <span className="font-bold text-white">AutoBalloon <span className="text-[#E63946]">Pro</span></span>
             <div className="h-4 w-px bg-[#333]" />
             <button onClick={handleSaveProject} className="text-xs text-gray-400 hover:text-white">Save Project</button>
         </div>
         <div className="flex gap-2">
             <button onClick={() => setUiState(s => ({...s, showCMMImport: true}))} className="px-3 py-1 bg-blue-600 text-white text-xs rounded">Import CMM</button>
             <button onClick={() => setUiState(s => ({...s, showRevisionCompare: true}))} className="px-3 py-1 bg-[#E63946] text-white text-xs rounded">Compare Revs</button>
         </div>
      </div>

      {/* 2. Main Content Grid */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT: Canvas / Blueprint Viewer */}
        <div className="flex-1 relative bg-[#050505] p-4 overflow-auto">
            <BlueprintViewer 
                imageSrc={`data:image/png;base64,${currentPageData.image}`}
                dimensions={currentDimensions}
                selectedDimId={uiState.selectedDimId}
                onSelect={(id) => setUiState(s => ({...s, selectedDimId: id}))}
                onUpdate={handleDimensionUpdate}
                onDelete={handleDimensionDelete}
                isPro={canDownload}
                onShowPaywall={() => setUiState(s => ({...s, showGlassWall: true}))}
            />
            
            {/* Page Navigation Overlay */}
            {uiState.totalPages > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-[#1a1a1a] rounded-full px-4 py-2 flex gap-4 shadow-xl">
                    <button onClick={() => setUiState(s => ({...s, currentPage: Math.max(1, s.currentPage - 1)}))}>←</button>
                    <span className="text-sm text-white">Page {uiState.currentPage} of {uiState.totalPages}</span>
                    <button onClick={() => setUiState(s => ({...s, currentPage: Math.min(s.totalPages, s.currentPage + 1)}))}>→</button>
                </div>
            )}
        </div>

        {/* RIGHT: Properties & Table (Tabbed) */}
        <div className="w-[450px] border-l border-[#2a2a2a] bg-[#111] flex flex-col">
            
            {/* Top Half: Properties Panel (Fits, Tolerances) */}
            <div className="h-1/2 border-b border-[#2a2a2a] overflow-y-auto">
                <PropertiesPanel 
                    dimension={projectData.dimensions.find(d => d.id === uiState.selectedDimId)}
                    onUpdate={handleDimensionUpdate}
                    cmmResult={projectData.cmmResults[uiState.selectedDimId]}
                />
            </div>

            {/* Bottom Half: Table Manager (BOM, Specs, Dims) */}
            <div className="h-1/2 flex flex-col">
                <TableManager 
                    dimensions={projectData.dimensions}
                    bom={projectData.bom}
                    specs={projectData.specifications}
                    activeTab={uiState.activeTab}
                    onTabChange={(tab) => setUiState(s => ({...s, activeTab: tab}))}
                    onUpdateData={(type, data) => setProjectData(prev => ({...prev, [type]: data}))}
                    onSelectRow={(id) => setUiState(s => ({...s, selectedDimId: id}))}
                />
            </div>
        </div>
      </div>

      {/* Modals */}
      <GlassWallPaywall isOpen={uiState.showGlassWall} onClose={() => setUiState(s => ({...s, showGlassWall: false}))} />
      {uiState.showCMMImport && <CMMImportModal onClose={() => setUiState(s => ({...s, showCMMImport: false}))} />}
    </div>
  );
}
