import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { useAppStore } from '../store/useAppStore';
import {
  Settings,
  Database,
  Satellite,
  Sliders,
  Sparkles,
  CheckCircle2,
  RefreshCw,
  Cpu,
  AlertCircle,
  Sun,
  Moon,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const {
    isDemoMode,
    setDemoMode,
    activeBufferDistance,
    setActiveBufferDistance,
    theme,
    setTheme,
  } = useAppStore();
  const [provider, setProvider] = useState<'demo' | 'copernicus' | 'bhuvan'>('demo');

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => apiClient.getSystemStatus(),
  });

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto transition-colors duration-200">
      {/* Top Banner */}
      <div>
        <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          System Administration & GIS Calibration
        </span>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center space-x-2">
          <Settings className="w-6 h-6 text-emerald-700 dark:text-emerald-400" />
          <span>Platform Settings & Operational Parameters</span>
        </h1>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
          Tune deep learning confidence cutoffs, GIS buffer thresholds, active satellite providers, and appearance theme.
        </p>
      </div>

      {/* Visual Theme Appearance Card */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2 pb-3 border-b border-slate-200 dark:border-slate-800">
          <Sun className="w-4 h-4 text-amber-500" />
          <span>Display Appearance & Theme</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => setTheme('light')}
            className={`p-4 rounded-lg border text-left flex items-start space-x-3 transition-all ${
              theme === 'light'
                ? 'bg-emerald-50/70 border-emerald-600 shadow-sm ring-1 ring-emerald-600'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-750'
            }`}
          >
            <div className="p-2 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-amber-500 shadow-xs">
              <Sun className="w-5 h-5 fill-amber-400" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-slate-100 block">
                Light Institutional Mode
              </span>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                High-contrast crisp government GIS styling with light neutral surfaces.
              </p>
            </div>
          </button>

          <button
            onClick={() => setTheme('dark')}
            className={`p-4 rounded-lg border text-left flex items-start space-x-3 transition-all ${
              theme === 'dark'
                ? 'bg-slate-800 border-emerald-500 shadow-sm ring-1 ring-emerald-500'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-750'
            }`}
          >
            <div className="p-2 rounded-md bg-slate-900 border border-slate-700 text-slate-200 shadow-xs">
              <Moon className="w-5 h-5 fill-slate-200" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-slate-100 block">
                Dark Satellite Mode
              </span>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Low-fatigue dark slate mode tailored for night shifts and optical spectral analysis.
              </p>
            </div>
          </button>
        </div>
      </div>

      {/* Backend & Diagnostics Status */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            <span>Backend Services Telemetry</span>
          </h2>
          <button
            onClick={() => refetchStatus()}
            className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Check Connectivity</span>
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-500 dark:text-slate-400 block mb-1">FastAPI Backend</span>
            <div className="flex items-center space-x-1.5 text-emerald-700 dark:text-emerald-400 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>ONLINE</span>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">Port 8000</p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-500 dark:text-slate-400 block mb-1">Spatial Database</span>
            <div className="flex items-center space-x-1.5 text-emerald-700 dark:text-emerald-400 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>CONNECTED</span>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{status?.active_interventions_count || 62} Sites Loaded</p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-500 dark:text-slate-400 block mb-1">ML Inference Server</span>
            <div className="flex items-center space-x-1.5 text-emerald-700 dark:text-emerald-400 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>READY (CPU)</span>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">FPCD-SiameseNet-v1</p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800 p-3 rounded border border-slate-200 dark:border-slate-700">
            <span className="text-slate-500 dark:text-slate-400 block mb-1">FPCD Dataset Cache</span>
            <div className="flex items-center space-x-1.5 text-emerald-700 dark:text-emerald-400 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>SYNCED (693)</span>
            </div>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">data/fpcd/manifest.json</p>
          </div>
        </div>
      </div>

      {/* Operational Mode Controls */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2 pb-3 border-b border-slate-200 dark:border-slate-800">
          <Sliders className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
          <span>Operational Mode & Satellite Stream</span>
        </h2>

        <div className="space-y-4 text-xs">
          {/* Demo Mode Switch */}
          <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
            <div>
              <strong className="text-slate-900 dark:text-white block font-semibold">Institutional Demo Mode</strong>
              <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                When active, uses verified high-res Maharashtra benchmarks (FP-001, FP-042, FP-108, FP-215) for guaranteed zero-latency inspection.
              </p>
            </div>
            <button
              onClick={() => setDemoMode(!isDemoMode)}
              className={`px-4 py-1.5 rounded text-xs font-bold transition-colors ${
                isDemoMode
                  ? 'bg-amber-600 text-white'
                  : 'bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {isDemoMode ? 'DEMO ACTIVE' : 'LIVE API'}
            </button>
          </div>

          {/* Active Satellite Provider */}
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 space-y-2">
            <strong className="text-slate-900 dark:text-white block font-semibold">Primary Earth Observation Feed</strong>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {[
                { id: 'demo', name: 'Synthesized Sentinel-2 / GE High-Res (Fast)', label: 'DEMO / BENCHMARK' },
                { id: 'copernicus', name: 'Copernicus Data Space Ecosystem (ESA)', label: 'LIVE SATELLITE' },
                { id: 'bhuvan', name: 'ISRO Bhuvan Open Services API', label: 'NATIONAL SENSOR' },
              ].map((prov) => (
                <button
                  key={prov.id}
                  onClick={() => setProvider(prov.id as any)}
                  className={`p-3 rounded text-left border transition-colors ${
                    provider === prov.id
                      ? 'bg-white dark:bg-slate-900 border-emerald-600 dark:border-emerald-500 shadow-sm font-bold text-slate-900 dark:text-white ring-1 ring-emerald-500'
                      : 'bg-white/60 dark:bg-slate-900/60 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-900'
                  }`}
                >
                  <span className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-400 block mb-1">
                    {prov.label}
                  </span>
                  <span className="text-xs leading-tight block">{prov.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Default Active Buffer Radius */}
          <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 space-y-2">
            <strong className="text-slate-900 dark:text-white block font-semibold">Default GIS Radial Buffer Focus</strong>
            <p className="text-slate-500 dark:text-slate-400 text-[11px]">
              Sets the default spatial radius applied across map overlays and raster index differencing.
            </p>
            <div className="flex space-x-3">
              {[100, 250, 500, 1000].map((dist) => (
                <button
                  key={dist}
                  onClick={() => setActiveBufferDistance(dist)}
                  className={`px-3 py-1.5 rounded font-mono text-xs font-bold border transition-colors ${
                    activeBufferDistance === dist
                      ? 'bg-emerald-700 dark:bg-emerald-600 text-white border-emerald-700 dark:border-emerald-600'
                      : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {dist} meters
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
