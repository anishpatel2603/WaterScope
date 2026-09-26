import React from 'react';
import { useRoute, Link } from 'wouter';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { GISMap } from '../components/GISMap';
import { Waves, ArrowLeft, MapPin, Layers, ShieldCheck, ArrowRight } from 'lucide-react';

export const WatershedDetailPage: React.FC = () => {
  const [, params] = useRoute<{ id: string }>('/watersheds/:id');
  const wsId = (params as any)?.id || 'ws-purna-upper';

  const { data: watershed } = useQuery({
    queryKey: ['watershed', wsId],
    queryFn: () => apiClient.getWatershed(wsId),
  });

  const { data: interventionsData } = useQuery({
    queryKey: ['interventions', watershed?.district],
    queryFn: () => apiClient.listInterventions({ district: watershed?.district || 'Akola' }),
  });

  const ws = watershed || {
    id: wsId,
    code: 'MH-PURNA-01',
    name: 'Upper Purna River Watershed',
    river_basin: 'Tapi River Basin',
    district: 'Akola',
    state: 'Maharashtra',
    area_hectares: 24500,
    sub_watersheds: [
      { id: 'sub-1', code: 'SW-01', name: 'Akhatwada Micro-Drainage', drainage_density: 2.34 },
      { id: 'sub-2', code: 'SW-02', name: 'Ghusar Stream Network', drainage_density: 2.12 },
      { id: 'sub-3', code: 'SW-03', name: 'Murtizapur Tributary', drainage_density: 1.98 },
      { id: 'sub-4', code: 'SW-04', name: 'Balapur Confluence', drainage_density: 2.45 },
    ],
  };

  const interventions = interventionsData?.items || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-3">
        <Link href="/watersheds">
          <a className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-900 px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-800 shadow-sm transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>All Watersheds</span>
          </a>
        </Link>
        <span className="text-slate-300 dark:text-slate-700">/</span>
        <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">{ws.code}</span>
      </div>

      {/* Header Info */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm transition-colors">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-800 uppercase">
                {ws.river_basin}
              </span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                {ws.area_hectares.toLocaleString()} Hectares
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">{ws.name}</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center space-x-2 mt-1">
              <MapPin className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
              <span>{ws.district}, {ws.state || 'Maharashtra'}</span>
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4 border-t lg:border-t-0 lg:border-l border-slate-200 dark:border-slate-800 pt-3 lg:pt-0 lg:pl-6 text-left">
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                Total Sites
              </span>
              <span className="text-lg font-bold font-mono text-slate-900 dark:text-white">
                {interventions.length || 42}
              </span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                Drainage Density
              </span>
              <span className="text-lg font-bold font-mono text-emerald-700 dark:text-emerald-400">2.22 km/km²</span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                Aggregated Water
              </span>
              <span className="text-lg font-bold font-mono text-blue-700 dark:text-blue-400">+48,200 m³</span>
            </div>
          </div>
        </div>
      </div>

      {/* Map & Sub-watershed Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 transition-colors">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <Waves className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
            <span>Watershed Spatial Map & Interventions Distribution</span>
          </h2>
          <GISMap
            center={[20.7002, 77.0082]}
            zoom={12}
            interventions={interventions}
            height="450px"
          />
        </div>

        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm text-xs space-y-3 transition-colors">
            <h3 className="font-bold text-slate-900 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800">
              Constituent Sub-Watersheds
            </h3>
            <div className="space-y-2">
              {ws.sub_watersheds?.map((sub) => (
                <div key={sub.id} className="p-2.5 rounded bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-800 dark:text-slate-200">{sub.name}</span>
                    <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                      {sub.code}
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 dark:text-slate-400">
                    <span>Drainage Density:</span>
                    <strong className="font-mono text-slate-800 dark:text-slate-200">{sub.drainage_density} km/km²</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
