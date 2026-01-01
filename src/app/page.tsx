'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamically import all views with SSR disabled
const LandingView = dynamic(() => import('@/components/LandingView').then(mod => ({ default: mod.LandingView })), {
  ssr: false,
  loading: () => <div className="min-h-screen w-full bg-brand-dark flex items-center justify-center"><div className="text-brand-gray-500">Loading...</div></div>
});

const ProcessingView = dynamic(() => import('@/components/ProcessingView').then(mod => ({ default: mod.ProcessingView })), {
  ssr: false,
});

const WorkbenchView = dynamic(() => import('@/components/WorkbenchView').then(mod => ({ default: mod.WorkbenchView })), {
  ssr: false,
});

/**
 * The Unified Surface
 *
 * This single page morphs between three states:
 * 1. Landing: Marketing + DropZone
 * 2. Processing: Extraction progress
 * 3. Workbench: Full canvas editor
 *
 * NO NAVIGATION. ONLY TRANSFORMATION.
 */
export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [mode, setMode] = useState<'landing' | 'processing' | 'workbench'>('landing');

  // Only access Zustand after mount
  useEffect(() => {
    setMounted(true);

    // Dynamically import and use the store only on client
    import('@/store/useAppStore').then(({ useAppStore }) => {
      const currentMode = useAppStore.getState().mode;
      setMode(currentMode);

      // Subscribe to mode changes
      const unsubscribe = useAppStore.subscribe(
        (state) => state.mode,
        (newMode) => setMode(newMode)
      );

      return () => unsubscribe();
    });
  }, []);

  if (!mounted) {
    return (
      <main className="min-h-screen w-full overflow-hidden bg-brand-dark">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-brand-gray-500">Loading...</div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen w-full overflow-hidden">
      {mode === 'landing' && <LandingView />}
      {mode === 'processing' && <ProcessingView />}
      {mode === 'workbench' && <WorkbenchView />}
    </main>
  );
}
