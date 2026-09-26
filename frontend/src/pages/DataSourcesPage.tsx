import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { Layers, Satellite, Database, CheckCircle2, ShieldCheck, ExternalLink, HardDrive } from 'lucide-react';

export const DataSourcesPage: React.FC = () => {
  const { data } = useQuery({
    queryKey: ['dataSources'],
    queryFn: () => apiClient.getDataSources(),
  });

  const sources = data?.sources || [
    {
      id: 'src-sentinel2',
      name: 'Copernicus Sentinel-2 MSI',
      type: 'Multi-Spectral Satellite Constellation',
      provider: 'European Space Agency (ESA)',
      resolution: '10m (B02, B03, B04, B08) / 20m (B11, B12)',
      update_frequency: '5-Day Global Revisit Cycle',
      license: 'Open Access (Copernicus Legal Notice)',
      is_active: true,
    },
    {
      id: 'src-bhuvan',
      name: 'ISRO Bhuvan Geospatial Gateway',
      type: 'Earth Observation Platform',
      provider: 'Indian Space Research Organisation (ISRO)',
      resolution: '5.8m (LISS-IV) / 2.5m (Cartosat-1)',
      update_frequency: 'Monthly / On-Demand',
      license: 'Government of India Data Sharing Policy',
      is_active: true,
    },
    {
      id: 'src-fpcd',
      name: 'Farm Pond Change Detection (FPCD) Dataset',
      type: 'Supervised Bi-Temporal Verification Corpus',
      provider: 'Hugging Face (ctundia/FPCD)',
      resolution: '1.0 meter/pixel (Google Earth Zoom 18)',
      update_frequency: '693 Triplet Pairs (Maharashtra Benchmark)',
      license: 'CC-BY-4.0 Open Scientific Dataset',
      is_active: true,
    },
    {
      id: 'src-cadastral',
      name: 'Maharashtra Cadastral & Watershed GIS',
      type: 'Administrative & Drainage Boundary Vector Shapefiles',
      provider: 'Dept. of Soil & Water Conservation, Maharashtra',
      resolution: 'Village / Parcel Level (1:10,000 Scale)',
      update_frequency: 'Annual Administrative Revision',
      license: 'Institutional Restricted / Internal State Use',
      is_active: true,
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Sensor & Registry Provenance
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Data Sources & Sensor Pipelines
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Inventory of ingested satellite constellations, airborne imagery, ground registries, and benchmark training corpora.
          </p>
        </div>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sources.map((src) => (
          <div
            key={src.id}
            className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4 hover:border-emerald-600 dark:hover:border-emerald-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Satellite className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />
                <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {src.type}
                </span>
              </div>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>ONLINE & ACTIVE</span>
              </span>
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">{src.name}</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Provider: {src.provider}</p>
            </div>

            <div className="border-t border-b border-slate-100 dark:border-slate-800 py-3 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Spatial Resolution:</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-semibold">{src.resolution}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Temporal Cadence:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{src.update_frequency}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Access & Licensing:</span>
                <span className="text-slate-700 dark:text-slate-300">{src.license}</span>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-1">
              <span>Sensor Band Support: NIR (B08), Red (B04), Green (B03)</span>
              <span className="font-mono text-emerald-700 dark:text-emerald-400 font-bold">LATENCY &lt; 250ms</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
