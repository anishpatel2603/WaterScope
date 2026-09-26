import React, { useState, useMemo } from 'react';
import { Link } from 'wouter';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { 
  AlertOctagon, 
  AlertTriangle, 
  ArrowRight, 
  CheckCircle2, 
  ShieldAlert, 
  Wrench, 
  Search, 
  Filter, 
  Calendar,
  Layers,
  Info
} from 'lucide-react';

export const PriorityZonesPage: React.FC = () => {
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');

  const { data, isLoading } = useQuery({
    queryKey: ['priorityZones'],
    queryFn: () => apiClient.getPriorityZones(),
  });

  const rawZones = data?.priority_zones && data.priority_zones.length > 0 
    ? data.priority_zones 
    : [];

  // Extract unique districts
  const districts = useMemo(() => {
    const dSet = new Set<string>();
    rawZones.forEach(z => {
      if (z.district) dSet.add(z.district);
    });
    return Array.from(dSet).sort();
  }, [rawZones]);

  // Dynamic counts across all tiers
  const criticalCount = data?.critical_count ?? rawZones.filter(z => z.priority?.toUpperCase() === 'CRITICAL').length;
  const highCount = data?.high_count ?? rawZones.filter(z => z.priority?.toUpperCase() === 'HIGH').length;
  const mediumCount = data?.medium_count ?? rawZones.filter(z => z.priority?.toUpperCase() === 'MEDIUM').length;
  const lowCount = data?.low_count ?? rawZones.filter(z => z.priority?.toUpperCase() === 'LOW').length;
  const totalCount = rawZones.length;

  // Filtered zones
  const filteredZones = useMemo(() => {
    return rawZones.filter(z => {
      // Priority filter
      if (selectedPriority !== 'ALL' && z.priority?.toUpperCase() !== selectedPriority.toUpperCase()) {
        return false;
      }
      // District filter
      if (selectedDistrict !== 'ALL' && z.district?.toLowerCase() !== selectedDistrict.toLowerCase()) {
        return false;
      }
      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = z.intervention_name?.toLowerCase().includes(q);
        const matchVillage = z.village?.toLowerCase().includes(q);
        const matchDistrict = z.district?.toLowerCase().includes(q);
        const matchAction = z.action_type?.toLowerCase().includes(q);
        const matchRationale = z.rationale?.toLowerCase().includes(q);
        if (!matchName && !matchVillage && !matchDistrict && !matchAction && !matchRationale) {
          return false;
        }
      }
      return true;
    });
  }, [rawZones, selectedPriority, selectedDistrict, searchQuery]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto transition-colors duration-200">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Preventative Infrastructure Surveillance
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Priority Maintenance & Degradation Zones
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Automated alerts flagged by bi-temporal ML models detecting structure drying, siltation, or embankment breaches across all urgency levels.
          </p>
        </div>
      </div>

      {/* Summary Stat Grid - All Priorities */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        {/* Critical */}
        <div 
          onClick={() => setSelectedPriority(selectedPriority === 'CRITICAL' ? 'ALL' : 'CRITICAL')}
          className={`p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
            selectedPriority === 'CRITICAL'
              ? 'bg-rose-50 dark:bg-rose-950/40 border-rose-400 dark:border-rose-700 ring-2 ring-rose-500/20'
              : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-rose-300'
          }`}
        >
          <div className="flex justify-between items-center text-rose-600 dark:text-rose-400 mb-1 font-semibold">
            <span>Critical Action Needed</span>
            <AlertOctagon className="w-4 h-4" />
          </div>
          <div className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {criticalCount} {criticalCount === 1 ? 'Site' : 'Sites'}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Immediate breach repair & re-excavation</p>
        </div>

        {/* High */}
        <div 
          onClick={() => setSelectedPriority(selectedPriority === 'HIGH' ? 'ALL' : 'HIGH')}
          className={`p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
            selectedPriority === 'HIGH'
              ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-400 dark:border-amber-700 ring-2 ring-amber-500/20'
              : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-amber-300'
          }`}
        >
          <div className="flex justify-between items-center text-amber-600 dark:text-amber-400 mb-1 font-semibold">
            <span>High Priority Alerts</span>
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {highCount} {highCount === 1 ? 'Site' : 'Sites'}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Moisture deficit & rapid siltation</p>
        </div>

        {/* Medium */}
        <div 
          onClick={() => setSelectedPriority(selectedPriority === 'MEDIUM' ? 'ALL' : 'MEDIUM')}
          className={`p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
            selectedPriority === 'MEDIUM'
              ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-400 dark:border-blue-700 ring-2 ring-blue-500/20'
              : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-blue-300'
          }`}
        >
          <div className="flex justify-between items-center text-blue-600 dark:text-blue-400 mb-1 font-semibold">
            <span>Medium Priority</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {mediumCount} {mediumCount === 1 ? 'Site' : 'Sites'}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Buffer siltation & slope revetment</p>
        </div>

        {/* Low / Preventative */}
        <div 
          onClick={() => setSelectedPriority(selectedPriority === 'LOW' ? 'ALL' : 'LOW')}
          className={`p-4 rounded-lg border shadow-sm cursor-pointer transition-all ${
            selectedPriority === 'LOW'
              ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-400 dark:border-emerald-700 ring-2 ring-emerald-500/20'
              : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-emerald-300'
          }`}
        >
          <div className="flex justify-between items-center text-emerald-700 dark:text-emerald-400 mb-1 font-semibold">
            <span>Low / Preventative</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {lowCount} {lowCount === 1 ? 'Site' : 'Sites'}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">Bi-annual survey & canopy check</p>
        </div>
      </div>

      {/* Filter & Priority Selector Tabs */}
      <div className="bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Priority Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 mr-1 flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Priority:</span>
          </span>

          <button
            onClick={() => setSelectedPriority('ALL')}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              selectedPriority === 'ALL'
                ? 'bg-slate-800 dark:bg-slate-700 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700/80'
            }`}
          >
            <span>All Priorities</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-black/20 text-white font-mono">
              {totalCount}
            </span>
          </button>

          <button
            onClick={() => setSelectedPriority('CRITICAL')}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              selectedPriority === 'CRITICAL'
                ? 'bg-rose-700 text-white shadow-sm'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50 hover:bg-rose-100'
            }`}
          >
            <span>Critical</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-rose-900/30 text-rose-800 dark:text-rose-200 font-mono">
              {criticalCount}
            </span>
          </button>

          <button
            onClick={() => setSelectedPriority('HIGH')}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              selectedPriority === 'HIGH'
                ? 'bg-amber-700 text-white shadow-sm'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50 hover:bg-amber-100'
            }`}
          >
            <span>High</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-amber-900/30 text-amber-800 dark:text-amber-200 font-mono">
              {highCount}
            </span>
          </button>

          <button
            onClick={() => setSelectedPriority('MEDIUM')}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              selectedPriority === 'MEDIUM'
                ? 'bg-blue-700 text-white shadow-sm'
                : 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900/50 hover:bg-blue-100'
            }`}
          >
            <span>Medium</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-900/30 text-blue-800 dark:text-blue-200 font-mono">
              {mediumCount}
            </span>
          </button>

          <button
            onClick={() => setSelectedPriority('LOW')}
            className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              selectedPriority === 'LOW'
                ? 'bg-emerald-800 text-white shadow-sm'
                : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50 hover:bg-emerald-100'
            }`}
          >
            <span>Low</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-900/30 text-emerald-800 dark:text-emerald-200 font-mono">
              {lowCount}
            </span>
          </button>
        </div>

        {/* Search & District Filters */}
        <div className="flex items-center space-x-2">
          {districts.length > 0 && (
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2.5 py-1.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            >
              <option value="ALL">All Districts</option>
              {districts.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          )}

          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search site, village..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded pl-8 pr-3 py-1.5 text-slate-700 dark:text-slate-300 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-emerald-600 w-44"
            />
          </div>
        </div>
      </div>

      {/* Priority Recommendations List */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-700 dark:text-slate-200">Active Priority Interventions</span>
            <span className="text-[11px] bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded font-mono">
              {filteredZones.length} of {totalCount} Sites
            </span>
          </div>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            {selectedPriority === 'ALL' ? 'Showing all priority tiers' : `Filtered to ${selectedPriority} tier`}
          </span>
        </div>

        {filteredZones.length === 0 ? (
          <div className="p-8 text-center space-y-2">
            <Info className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No priority interventions match your filter
            </p>
            <p className="text-xs text-slate-500">
              Try adjusting your priority tier, district filter, or search query.
            </p>
            <button
              onClick={() => {
                setSelectedPriority('ALL');
                setSelectedDistrict('ALL');
                setSearchQuery('');
              }}
              className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 hover:underline mt-2 inline-block"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {filteredZones.map((zone) => {
              const priority = (zone.priority || 'MEDIUM').toUpperCase();
              const isCritical = priority === 'CRITICAL';
              const isHigh = priority === 'HIGH';
              const isMedium = priority === 'MEDIUM';
              const isLow = priority === 'LOW';

              return (
                <div 
                  key={zone.recommendation_id} 
                  className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Priority Badge */}
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                            isCritical
                              ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                              : isHigh
                              ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800'
                              : isMedium
                              ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-800'
                              : 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800'
                          }`}
                        >
                          {priority}
                        </span>

                        <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                          {zone.intervention_name}
                        </h3>

                        <span className="text-xs text-slate-300 dark:text-slate-600">•</span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {zone.village}, {zone.district}
                        </span>
                      </div>

                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {zone.rationale}
                      </p>

                      <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 dark:text-slate-400 pt-0.5">
                        <span className="flex items-center space-x-1">
                          <Wrench className="w-3.5 h-3.5 text-slate-400" />
                          <span>Prescribed Action: <strong className="text-slate-700 dark:text-slate-300">{zone.action_type.replace(/_/g, ' ')}</strong></span>
                        </span>

                        {zone.created_at && (
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            <span>Flagged: {new Date(zone.created_at).toLocaleDateString()}</span>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <Link href={`/interventions/${zone.intervention_id}`}>
                        <a className="inline-flex items-center space-x-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 border border-emerald-200 dark:border-emerald-800 px-3 py-1.5 rounded transition-colors">
                          <span>Launch Inspection</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </a>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

