import React from 'react';
import { ObservedImpact } from '../types/api';
import { ShieldCheck, AlertCircle, Info, AlertTriangle, Activity, Database, CheckCircle2 } from 'lucide-react';

interface ObservedImpactCardProps {
  impact?: ObservedImpact | null;
  isLoading?: boolean;
  className?: string;
}

export const ObservedImpactCard: React.FC<ObservedImpactCardProps> = ({
  impact,
  isLoading = false,
  className = '',
}) => {
  // If loading or no data yet, render clean placeholder
  if (isLoading || !impact) {
    return (
      <div className={`bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm text-slate-800 dark:text-slate-200 transition-colors duration-200 ${className}`}>
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
              Observed Bi-Temporal Verification
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Observed Impact Evidence</h3>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full border text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            <Activity className="w-3.5 h-3.5 animate-spin" />
            <span>Resolving Site Telemetry...</span>
          </div>
        </div>
        <div className="py-6 text-center text-xs text-slate-500 dark:text-slate-400 animate-pulse">
          Computing site-specific bi-temporal index from satellite & field observations...
        </div>
      </div>
    );
  }

  const data = impact;
  const compositeScore = (typeof data.composite_index === 'number')
    ? data.composite_index
    : (typeof data.composite_score === 'number' ? data.composite_score : 50.0);

  const mlScore = data.ml_change_score ?? data.components?.ml_change?.score ?? 50.0;
  const waterScore = data.water_retention_score ?? data.components?.water_extent?.score ?? 50.0;
  const vegScore = data.vegetation_score ?? data.components?.vegetation_response?.score ?? 50.0;
  const qualityScore = data.data_quality_score ?? data.components?.data_quality?.score ?? data.components?.model_confidence?.score ?? 80.0;

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'OBSERVED IMPROVEMENT':
        return {
          bg: 'bg-emerald-100 dark:bg-emerald-950/80 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200',
          icon: ShieldCheck,
          label: 'OBSERVED IMPROVEMENT',
        };
      case 'OBSERVED DEGRADATION':
        return {
          bg: 'bg-rose-100 dark:bg-rose-950/80 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200',
          icon: AlertTriangle,
          label: 'OBSERVED DEGRADATION',
        };
      case 'MODERATE OBSERVED CHANGE':
        return {
          bg: 'bg-blue-100 dark:bg-blue-950/80 border-blue-300 dark:border-blue-800 text-blue-900 dark:text-blue-200',
          icon: Activity,
          label: 'MODERATE OBSERVED CHANGE',
        };
      case 'NO SIGNIFICANT OBSERVED CHANGE':
        return {
          bg: 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-300',
          icon: Info,
          label: 'NO SIGNIFICANT CHANGE',
        };
      default:
        return {
          bg: 'bg-amber-100 dark:bg-amber-950/80 border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-200',
          icon: AlertCircle,
          label: 'INSUFFICIENT EVIDENCE',
        };
    }
  };

  const badge = getVerdictBadge(data.verdict);
  const VerdictIcon = badge.icon;

  return (
    <div className={`bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm text-slate-800 dark:text-slate-200 transition-colors duration-200 ${className}`}>
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
            Observed Bi-Temporal Verification
          </span>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <span>Observed Impact Evidence</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
              {data.scoring_version || 'v2.0'}
            </span>
          </h3>
        </div>

        <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full border text-xs font-bold ${badge.bg}`}>
          <VerdictIcon className="w-4 h-4" />
          <span>{badge.label}</span>
        </div>
      </div>

      {/* Main Score & Narrative */}
      <div className="py-3 flex items-start space-x-4">
        {/* Big Composite Score Ring / Box */}
        <div className="shrink-0 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-center min-w-[105px]">
          <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            Composite Index
          </span>
          <span className={`text-3xl font-extrabold font-mono ${
            compositeScore >= 75 ? 'text-emerald-700 dark:text-emerald-400' :
            compositeScore >= 50 ? 'text-blue-700 dark:text-blue-400' :
            compositeScore >= 40 ? 'text-slate-700 dark:text-slate-300' : 'text-rose-700 dark:text-rose-400'
          }`}>
            {compositeScore.toFixed(1)}
          </span>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 block font-semibold">/ 100 max</span>
        </div>

        {/* Narrative Description */}
        <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed flex-1">
          <p className="font-medium text-slate-800 dark:text-slate-100 mb-1.5">{data.narrative}</p>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 dark:text-slate-400">
            <span><strong>Model:</strong> {data.model_version || 'waterscope_change_model_v3'}</span>
            <span>•</span>
            <span><strong>Framework:</strong> 4-Part Multi-Sensor Telemetry</span>
            {data.site_id && (
              <>
                <span>•</span>
                <span className="font-mono text-[10px] text-slate-600 dark:text-slate-400">ID: {data.site_id}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 4 Component Weight Breakdown */}
      <div className="mt-2 pt-3 border-t border-slate-200 dark:border-slate-800">
        <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-2">
          Index Weight Contribution Breakdown
        </span>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {/* ML Change */}
          <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center text-[10px] text-slate-500 dark:text-slate-400 font-semibold mb-1">
                <span>ML Change (35%)</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-bold">{mlScore.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mb-1.5">
                <div
                  className="bg-emerald-600 dark:bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, mlScore))}%` }}
                ></div>
              </div>
            </div>
            {data.explanation?.ml_change && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-tight">
                {data.explanation.ml_change}
              </p>
            )}
          </div>

          {/* Water Extent */}
          <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center text-[10px] text-slate-500 dark:text-slate-400 font-semibold mb-1">
                <span>Water Retention (30%)</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-bold">{waterScore.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mb-1.5">
                <div
                  className="bg-blue-600 dark:bg-blue-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, waterScore))}%` }}
                ></div>
              </div>
            </div>
            {data.explanation?.water_retention && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-tight">
                {data.explanation.water_retention}
              </p>
            )}
          </div>

          {/* Vegetation */}
          <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center text-[10px] text-slate-500 dark:text-slate-400 font-semibold mb-1">
                <span>Vegetation (20%)</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-bold">{vegScore.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mb-1.5">
                <div
                  className="bg-teal-600 dark:bg-teal-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, vegScore))}%` }}
                ></div>
              </div>
            </div>
            {data.explanation?.vegetation && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-tight">
                {data.explanation.vegetation}
              </p>
            )}
          </div>

          {/* Data Quality */}
          <div className="bg-slate-50 dark:bg-slate-800 p-2.5 rounded border border-slate-200 dark:border-slate-700 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center text-[10px] text-slate-500 dark:text-slate-400 font-semibold mb-1">
                <span>Data Quality (15%)</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 font-bold">{qualityScore.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden mb-1.5">
                <div
                  className="bg-indigo-600 dark:bg-indigo-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, qualityScore))}%` }}
                ></div>
              </div>
            </div>
            {data.explanation?.data_quality && (
              <p className="text-[10px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-tight">
                {data.explanation.data_quality}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Mandatory Scientific Non-Causal Alert */}
      <div className="mt-3 p-2.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded text-[11px] text-amber-900 dark:text-amber-300 flex items-start space-x-2">
        <AlertCircle className="w-4 h-4 text-amber-700 dark:text-amber-400 shrink-0 mt-0.5" />
        <p className="leading-tight">
          <strong>Mandatory Scientific Caveat:</strong> {data.scientific_disclaimer || 'Observed bi-temporal surface change derived from satellite and field imagery. Demonstrates physical surface alteration; requires field validation.'}
        </p>
      </div>
    </div>
  );
};
