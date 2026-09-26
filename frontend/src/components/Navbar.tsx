import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { Database, Satellite, Sparkles, Sun, Moon } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';

export const Navbar: React.FC = () => {
  const { isDemoMode, toggleDemoMode, theme, toggleTheme } = useAppStore();

  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => apiClient.getSystemStatus(),
    refetchInterval: 30000,
  });

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50 h-16 flex items-center justify-between px-6 select-none transition-colors duration-200">
      {/* Brand & Tagline */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-700 text-white flex items-center justify-center font-bold text-xl shadow-sm border border-emerald-800">
            W
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">WATERSCOPE</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                GOV-GIS v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium tracking-wide">
              AI-Powered Before & After Watershed Intervention Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Middle Status Indicators */}
      <div className="hidden lg:flex items-center space-x-6 text-xs text-slate-600 dark:text-slate-300">
        <div className="flex items-center space-x-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
          </span>
          <span className="font-semibold text-slate-700 dark:text-slate-300">System:</span>
          <span className="text-emerald-700 dark:text-emerald-400 font-medium">{status?.status || 'OPERATIONAL'}</span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400 border-l border-slate-200 dark:border-slate-800 pl-4">
          <Database className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
          <span>Sites:</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200">{status?.active_interventions_count ?? 62}</span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400 border-l border-slate-200 dark:border-slate-800 pl-4">
          <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          <span>Model:</span>
          <span className="font-mono font-medium text-slate-800 dark:text-slate-200">SiameseNet-v1 (FPCD)</span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-500 dark:text-slate-400 border-l border-slate-200 dark:border-slate-800 pl-4">
          <Satellite className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>Provider:</span>
          <span className="font-medium text-slate-800 dark:text-slate-200 uppercase text-[11px]">
            {status?.satellite_provider === 'demo' ? 'Sentinel-2 Synthetic + Google Earth' : 'Copernicus API'}
          </span>
        </div>
      </div>

      {/* Right Controls, Dark Mode & Demo Toggle */}
      <div className="flex items-center space-x-4">
        {/* Dark / Light Mode Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors border border-slate-200 dark:border-slate-700 flex items-center space-x-1.5 text-xs font-semibold"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? (
            <>
              <Sun className="w-4 h-4 text-amber-400 fill-amber-400" />
              <span className="hidden sm:inline">Light</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 text-slate-700" />
              <span className="hidden sm:inline">Dark</span>
            </>
          )}
        </button>

        {/* Demo Mode Pill */}
        <div className="flex items-center space-x-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
          <span className="text-xs font-semibold px-2 text-slate-600 dark:text-slate-300">
            DEMO
          </span>
          <button
            onClick={toggleDemoMode}
            className={`text-xs px-3 py-1 font-semibold rounded transition-colors ${
              isDemoMode
                ? 'bg-amber-600 text-white shadow-sm'
                : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700'
            }`}
          >
            {isDemoMode ? 'ACTIVE (PRESETS)' : 'LIVE STREAM'}
          </button>
        </div>

        {/* User / Department Pill */}
        <div className="hidden sm:flex items-center space-x-2 pl-2 border-l border-slate-200 dark:border-slate-800 text-xs">
          <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-600">
            GS
          </div>
          <div className="text-left leading-tight">
            <p className="font-semibold text-slate-800 dark:text-slate-200">State Watershed Cell</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Dept. of Soil & Water</p>
          </div>
        </div>
      </div>
    </header>
  );
};
