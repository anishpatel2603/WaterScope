import React from 'react';
import { Link } from 'wouter';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { Waves, MapPin, ArrowRight, Layers, ShieldCheck } from 'lucide-react';

export const WatershedsPage: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['watersheds'],
    queryFn: () => apiClient.listWatersheds(),
  });

  const watersheds = data?.items || [
    {
      id: 'ws-purna-upper',
      code: 'MH-PURNA-01',
      name: 'Upper Purna River Watershed',
      river_basin: 'Tapi River Basin',
      district: 'Akola',
      state: 'Maharashtra',
      area_hectares: 24500,
    },
    {
      id: 'ws-godavari-jalna',
      code: 'MH-GODA-04',
      name: 'Kundalika Sub-Basin',
      river_basin: 'Godavari Basin',
      district: 'Jalna',
      state: 'Maharashtra',
      area_hectares: 18200,
    },
    {
      id: 'ws-amravati-wardha',
      code: 'MH-WARDHA-02',
      name: 'Pedhi Catchment',
      river_basin: 'Wardha Basin',
      district: 'Amravati',
      state: 'Maharashtra',
      area_hectares: 31000,
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Hydrological Planning Units
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Watersheds & Drainage Basins
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Delineated micro-watersheds and river drainage zones for multi-structure aggregation across Maharashtra.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {watersheds.map((ws) => (
          <div
            key={ws.id}
            className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4 hover:border-emerald-500 dark:hover:border-emerald-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                {ws.code}
              </span>
              <Waves className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            </div>

            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">{ws.name}</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center space-x-1.5 mt-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                <span>{ws.district}, {ws.state || 'Maharashtra'}</span>
              </p>
            </div>

            <div className="border-t border-b border-slate-100 dark:border-slate-800 py-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">River Basin:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{ws.river_basin}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Delineated Area:</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">{ws.area_hectares.toLocaleString()} Hectares</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Sub-Watersheds:</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">4 Micro-units</span>
              </div>
            </div>

            <Link href={`/watersheds/${ws.id}`}>
              <a className="w-full inline-flex items-center justify-center space-x-2 text-xs font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 py-2 rounded transition-colors border border-transparent dark:border-emerald-800/60">
                <span>Inspect Drainage & Interventions</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};
