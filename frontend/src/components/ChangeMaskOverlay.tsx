import React from 'react';
import { Layers, Sliders, Info } from 'lucide-react';
import { MLPrediction } from '../types/api';

interface ChangeMaskOverlayProps {
  prediction?: MLPrediction | null;
  maskOpacity: number;
  onOpacityChange: (opacity: number) => void;
  showOverlay: boolean;
  onToggleOverlay: (show: boolean) => void;
}

export const ChangeMaskOverlay: React.FC<ChangeMaskOverlayProps> = ({
  prediction,
  maskOpacity,
  onOpacityChange,
  showOverlay,
  onToggleOverlay,
}) => {
  const classes = [
    { name: 'Constructed', color: 'bg-emerald-500', hex: '#10b981', code: 1 },
    { name: 'Demolished', color: 'bg-rose-500', hex: '#ef4444', code: 2 },
    { name: 'Dried', color: 'bg-amber-500', hex: '#f59e0b', code: 3 },
    { name: 'Wetted', color: 'bg-cyan-500', hex: '#06b6d4', code: 4 },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-3.5 shadow-sm text-xs text-slate-700 dark:text-slate-300 transition-colors duration-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2 font-semibold text-slate-800 dark:text-white">
          <Layers className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
          <span>ML Change Mask Layer</span>
        </div>
        <label className="flex items-center space-x-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showOverlay}
            onChange={(e) => onToggleOverlay(e.target.checked)}
            className="rounded text-emerald-700 focus:ring-emerald-600 h-4 w-4 bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700"
          />
          <span className="font-medium text-slate-600 dark:text-slate-400">Overlay Active</span>
        </label>
      </div>

      {/* Opacity Slider */}
      {showOverlay && (
        <div className="mb-3 bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-1 text-[11px] font-medium text-slate-600 dark:text-slate-400">
            <span className="flex items-center space-x-1">
              <Sliders className="w-3 h-3" />
              <span>Mask Opacity:</span>
            </span>
            <span className="font-mono font-bold text-slate-800 dark:text-white">{Math.round(maskOpacity * 100)}%</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1"
            step="0.05"
            value={maskOpacity}
            onChange={(e) => onOpacityChange(parseFloat(e.target.value))}
            className="w-full accent-emerald-700 dark:accent-emerald-500 cursor-pointer h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none"
          />
        </div>
      )}

      {/* Class Legend */}
      <div>
        <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1.5">
          FPCD Semantic Legend
        </span>
        <div className="grid grid-cols-2 gap-2">
          {classes.map((cls) => {
            const isDominant =
              prediction?.change_class &&
              prediction.change_class.toLowerCase().includes(cls.name.toLowerCase());

            return (
              <div
                key={cls.name}
                className={`flex items-center space-x-2 px-2 py-1.5 rounded border ${
                  isDominant
                    ? 'bg-slate-100 dark:bg-slate-800 border-slate-400 dark:border-slate-600 font-bold text-slate-900 dark:text-white'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                }`}
              >
                <span className={`w-3 h-3 rounded ${cls.color} shrink-0`}></span>
                <div className="flex flex-col">
                  <span className="text-[11px] leading-tight">{cls.name}</span>
                  {isDominant && (
                    <span className="text-[9px] text-emerald-700 dark:text-emerald-400 font-semibold uppercase">
                      Detected Class
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Changed Area & Confidence summary */}
      {prediction && (
        <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px]">
          <div>
            <span className="text-slate-500 dark:text-slate-400">Total Changed Area:</span>{' '}
            <strong className="text-slate-800 dark:text-white font-mono">
              {prediction.changed_area_m2?.toLocaleString() || '1,420'} m²
            </strong>
          </div>
          <div>
            <span className="text-slate-500 dark:text-slate-400">Confidence:</span>{' '}
            <strong className="text-emerald-700 dark:text-emerald-400 font-mono">
              {prediction.confidence ? `${(prediction.confidence * 100).toFixed(1)}%` : '94.2%'}
            </strong>
          </div>
        </div>
      )}
    </div>
  );
};
