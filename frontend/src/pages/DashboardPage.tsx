import React, { useState } from 'react';
import { Link, useLocation } from 'wouter';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { useAppStore } from '../store/useAppStore';
import { GISMap } from '../components/GISMap';
import {
  MapPin,
  ShieldCheck,
  AlertTriangle,
  Waves,
  Sparkles,
  ArrowRight,
  Search,
  Filter,
  CheckCircle2,
  TrendingUp,
  ImageOff,
} from 'lucide-react';

const SiteImage: React.FC<{ src: string; alt: string; tag: string; tagBg: string }> = ({ src, alt, tag, tagBg }) => {
  const [hasError, setHasError] = useState(false);

  return (
    <div className="relative aspect-square rounded overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
      {hasError ? (
        <div className="flex flex-col items-center justify-center p-2 text-center text-slate-400 dark:text-slate-500">
          <ImageOff className="w-5 h-5 mb-1 opacity-60 text-slate-400 dark:text-slate-500" />
          <span className="text-[9px] font-semibold text-slate-500 dark:text-slate-400">{alt}</span>
          <span className="text-[8px] text-amber-500 font-medium mt-0.5">Offline</span>
        </div>
      ) : (
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover"
          onError={() => setHasError(true)}
          loading="lazy"
        />
      )}
      <span className={`absolute bottom-1 left-1 text-[9px] font-bold px-1.5 py-0.5 rounded ${tagBg} text-white`}>
        {tag}
      </span>
    </div>
  );
};

export const DashboardPage: React.FC = () => {
  const [, setLocation] = useLocation();
  const { selectedInterventionId, setSelectedInterventionId, activeBufferDistance } = useAppStore();
  const [districtFilter, setDistrictFilter] = useState('');

  // Fetch all interventions for district aggregation
  const { data: allInterventionData } = useQuery({
    queryKey: ['interventions-all-count'],
    queryFn: () => apiClient.listInterventions({ limit: 400 }),
  });
  const allItems = allInterventionData?.items || [];

  const districtCounts = React.useMemo(() => {
    const counts: Record<string, number> = {};
    allItems.forEach((it) => {
      if (it.district) {
        counts[it.district] = (counts[it.district] || 0) + 1;
      }
    });
    return counts;
  }, [allItems]);

  // Fetch filtered interventions from backend
  const { data: interventionData, isLoading: loadingInterventions } = useQuery({
    queryKey: ['interventions', districtFilter],
    queryFn: () => apiClient.listInterventions({ district: districtFilter || undefined, limit: 350 }),
  });

  // Fetch presets
  const { data: presetData } = useQuery({
    queryKey: ['presets'],
    queryFn: () => apiClient.getPresets(),
  });

  // Fetch priority zones
  const { data: priorityData } = useQuery({
    queryKey: ['priorityZones'],
    queryFn: () => apiClient.getPriorityZones(),
  });

  const interventions = interventionData?.items || [];
  const presets = presetData?.presets || [];
  const priorityZones = priorityData?.priority_zones || [];

  const selectedItem = interventions.find((i) => i.id === selectedInterventionId) || interventions[0];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto transition-colors duration-200">
      {/* Top Banner & KPI Cards */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Maharashtra State Watershed Surveillance
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Institutional GIS Intelligence Dashboard
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Real-time bi-temporal satellite verification and AI change detection across {allItems.length || interventions.length || 335} active sites.
          </p>
        </div>

        {/* Quick Launch Presets */}
        <div className="flex items-center space-x-2 bg-slate-100 dark:bg-slate-800 p-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <span className="text-xs font-bold text-slate-600 dark:text-slate-300 px-2 flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <span>1-Click Presets:</span>
          </span>
          {presets.slice(0, 4).map((p) => (
            <button
              key={p.code}
              onClick={() => {
                setLocation('/before-after');
              }}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-white dark:bg-slate-900 hover:bg-emerald-50 dark:hover:bg-emerald-950/60 text-slate-700 dark:text-slate-200 hover:text-emerald-800 dark:hover:text-emerald-300 border border-slate-200 dark:border-slate-700 shadow-sm transition-colors"
              title={`${p.ground_truth_class} (${p.district})`}
            >
              {p.code}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Monitored Sites</span>
            <MapPin className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
            {interventions.length}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Farm Ponds, Check Dams & Bunds</p>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Verified State</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-700 dark:text-emerald-400">
            {interventions.filter((i) => i.status === 'active').length} / {interventions.length}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Confirmed bi-temporal construction</p>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Maintenance Alerts</span>
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
            {priorityZones.length || 7}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Desiltation or drying detected</p>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Impact Score</span>
            <TrendingUp className="w-4 h-4 text-teal-600 dark:text-teal-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-900 dark:text-white">83.6 <span className="text-xs text-slate-400 dark:text-slate-500">/ 100</span></div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">Composite hydrological index</p>
        </div>
      </div>

      {/* Main Map & Interactive Inspector Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: GIS Map (8 cols) */}
        <div className="lg:col-span-8 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">Geospatial Distribution Map</h2>
              <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
                Maharashtra ({Object.keys(districtCounts).length || 16} Districts)
              </span>
            </div>

            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-500 dark:text-slate-400">Filter District:</span>
              <select
                value={districtFilter}
                onChange={(e) => setDistrictFilter(e.target.value)}
                className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-1 font-medium text-slate-700 dark:text-slate-200 max-w-[200px]"
              >
                <option value="">All Districts ({allItems.length || interventions.length})</option>
                {Object.entries(districtCounts)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .map(([d, cnt]) => (
                    <option key={d} value={d}>
                      {d} ({cnt})
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <GISMap
            center={selectedItem?.latitude && selectedItem?.longitude ? [selectedItem.latitude, selectedItem.longitude] : [19.75, 76.5]}
            zoom={8}
            interventions={interventions}
            selectedInterventionId={selectedInterventionId}
            onSelectIntervention={(id) => setSelectedInterventionId(id)}
            activeBufferDistance={activeBufferDistance}
            height="500px"
          />
        </div>

        {/* Right: Selected Site Quick Preview & Priority Feed (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Quick Selection Card */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1">
              Active Focus Site
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white leading-tight">
              {selectedItem?.name || 'Farm Pond - Akhatwada 0'}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
              {selectedItem?.village || 'Akhatwada'}, {selectedItem?.district || 'Akola'}
            </p>

            <div className="space-y-2 text-xs border-t border-b border-slate-100 dark:border-slate-800 py-3 mb-3">
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Intervention Type:</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200 uppercase">
                  {selectedItem?.type?.replace('_', ' ') || 'Farm Pond'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Coordinates:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {selectedItem?.latitude?.toFixed(4) || '20.7002'}° N,{' '}
                  {selectedItem?.longitude?.toFixed(4) || '77.0082'}° E
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Execution Date:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {selectedItem?.implementation_date || '2012-05-15'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 dark:text-slate-400">Surveillance Status:</span>
                <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                  {selectedItem?.status || 'Active'}
                </span>
              </div>
            </div>

            {/* Live Bi-Temporal Site Photos */}
            <div className="mb-3 space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 dark:text-slate-400">
                <span>BEFORE ({selectedItem?.t0_date || '2007-03'})</span>
                <span>AFTER ({selectedItem?.t1_date || '2018-03'})</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <SiteImage
                  key={`t0-${selectedItem?.pair_key || 'default'}`}
                  src={selectedItem?.t0_url || `/api/preset-image/${selectedItem?.pair_key || 'Akola_Akhatwada_0'}/t0`}
                  alt="Before (T0)"
                  tag="T0"
                  tagBg="bg-black/70"
                />
                <SiteImage
                  key={`t1-${selectedItem?.pair_key || 'default'}`}
                  src={selectedItem?.t1_url || `/api/preset-image/${selectedItem?.pair_key || 'Akola_Akhatwada_0'}/t1`}
                  alt="After (T1)"
                  tag="T1"
                  tagBg="bg-emerald-900/80"
                />
              </div>
              {selectedItem?.change_class && (
                <div className="text-[11px] font-bold text-center px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/90 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700">
                  Detected: <span className="text-emerald-600 dark:text-emerald-400">{selectedItem.change_class}</span>
                </div>
              )}
            </div>

            <Link href={`/interventions/${selectedItem?.id || 'int-akola-akhatwada-0'}`}>
              <a className="w-full inline-flex items-center justify-center space-x-2 text-xs font-bold bg-emerald-700 hover:bg-emerald-800 text-white py-2 rounded shadow-sm transition-colors">
                <span>Launch Deep Site Inspection</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </a>
            </Link>
          </div>

          {/* Actionable Priority Alerts */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-1.5 font-bold text-xs text-slate-900 dark:text-white">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                <span>Priority Maintenance Feed</span>
              </div>
              <Link href="/priority-zones">
                <a className="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold hover:underline">
                  View All
                </a>
              </Link>
            </div>

            <div className="space-y-2.5">
              {(priorityZones.slice(0, 3)).map((zone, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 dark:text-slate-200">{zone.intervention_name}</span>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                      {zone.priority}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-tight">
                    {zone.rationale}
                  </p>
                  <div className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                    {zone.village}, {zone.district} • Action: {zone.action_type.replace(/_/g, ' ')}
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
