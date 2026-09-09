import React, { useState, useRef, useCallback } from 'react';
import { Calendar, Eye, Layers, MoveHorizontal, Maximize2 } from 'lucide-react';

interface BeforeAfterSliderProps {
  t0Image: string;
  t1Image: string;
  t0Date?: string;
  t1Date?: string;
  maskOverlay?: string | null;
  maskOpacity?: number;
  height?: string;
  className?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  t0Image,
  t1Image,
  t0Date = 'Before (T0)',
  t1Date = 'After (T1)',
  maskOverlay = null,
  maskOpacity = 0.5,
  height = '420px',
  className = '',
}) => {
  const [sliderPosition, setSliderPosition] = useState(50); // percentage (0 - 100)
  const [isDragging, setIsDragging] = useState(false);
  const [viewMode, setViewMode] = useState<'slider' | 'side-by-side'>('slider');
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback(
    (clientX: number) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setSliderPosition(percentage);
    },
    []
  );

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isDragging) {
      handleMove(e.touches[0].clientX);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      handleMove(e.clientX);
    }
  };

  return (
    <div className={`relative flex flex-col bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm transition-colors duration-200 ${className}`}>
      {/* Top Header & Mode Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-50 dark:bg-slate-800/90 border-b border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-200">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 font-medium">
            <Calendar className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            <span>T0: <strong className="text-slate-900 dark:text-white">{t0Date}</strong></span>
            <span className="text-slate-400 dark:text-slate-500">vs</span>
            <span>T1: <strong className="text-slate-900 dark:text-white">{t1Date}</strong></span>
          </div>
          <span className="text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 px-1.5 py-0.5 rounded">
            1.0m / px (GE Zoom 18)
          </span>
        </div>

        <div className="flex items-center space-x-1 bg-white dark:bg-slate-900 p-0.5 rounded border border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setViewMode('slider')}
            className={`px-2.5 py-0.5 rounded text-[11px] font-semibold transition-colors ${
              viewMode === 'slider' ? 'bg-emerald-700 text-white' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Swipe Slider
          </button>
          <button
            onClick={() => setViewMode('side-by-side')}
            className={`px-2.5 py-0.5 rounded text-[11px] font-semibold transition-colors ${
              viewMode === 'side-by-side' ? 'bg-emerald-700 text-white' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {/* Main Image Comparison Area */}
      {viewMode === 'slider' ? (
        <div
          ref={containerRef}
          className="relative w-full cursor-ew-resize select-none overflow-hidden bg-slate-900"
          style={{ height }}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onMouseLeave={() => setIsDragging(false)}
          onMouseMove={handleMouseMove}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={() => setIsDragging(false)}
          onTouchMove={handleTouchMove}
        >
          {/* T1 (After) Image - Background Layer */}
          <div className="absolute inset-0 w-full h-full">
            <img
              src={t1Image}
              alt="After Implementation (T1)"
              className="w-full h-full object-cover"
            />
            {/* Optional Change Mask Overlay */}
            {maskOverlay && (
              <img
                src={maskOverlay}
                alt="Change Mask"
                className="absolute inset-0 w-full h-full object-cover pointer-events-none transition-opacity duration-150"
                style={{ opacity: maskOpacity }}
              />
            )}
            <div className="absolute top-3 right-3 bg-black/70 text-white text-xs px-2.5 py-1 rounded font-medium backdrop-blur">
              AFTER ({t1Date})
            </div>
          </div>

          {/* T0 (Before) Image - Clipped Top Layer */}
          <div
            className="absolute inset-0 h-full overflow-hidden"
            style={{ width: `${sliderPosition}%` }}
          >
            <div className="relative w-full h-full" style={{ width: containerRef.current?.clientWidth || '100%' }}>
              <img
                src={t0Image}
                alt="Before Implementation (T0)"
                className="w-full h-full object-cover"
                style={{ width: containerRef.current?.clientWidth || '100%' }}
              />
              <div className="absolute top-3 left-3 bg-black/70 text-white text-xs px-2.5 py-1 rounded font-medium backdrop-blur">
                BEFORE ({t0Date})
              </div>
            </div>
          </div>

          {/* Vertical Divider Line & Handle */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg pointer-events-none"
            style={{ left: `${sliderPosition}%` }}
          >
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 bg-white dark:bg-slate-800 rounded-full shadow-md flex items-center justify-center border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200">
              <MoveHorizontal className="w-4 h-4" />
            </div>
          </div>
        </div>
      ) : (
        /* Side by Side Mode */
        <div className="grid grid-cols-2 gap-1 bg-slate-200 dark:bg-slate-800 p-1" style={{ height }}>
          <div className="relative h-full bg-slate-900 overflow-hidden rounded">
            <img src={t0Image} alt="Before" className="w-full h-full object-cover" />
            <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded font-medium">
              BEFORE: {t0Date}
            </div>
          </div>
          <div className="relative h-full bg-slate-900 overflow-hidden rounded">
            <img src={t1Image} alt="After" className="w-full h-full object-cover" />
            {maskOverlay && (
              <img
                src={maskOverlay}
                alt="Change Mask"
                className="absolute inset-0 w-full h-full object-cover pointer-events-none transition-opacity duration-150"
                style={{ opacity: maskOpacity }}
              />
            )}
            <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded font-medium">
              AFTER: {t1Date}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
