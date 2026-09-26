import React from 'react';
import { useRoute, Link } from 'wouter';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { ArrowLeft, CheckCircle2, AlertTriangle, Layers, ShieldCheck, Compass, FileCheck } from 'lucide-react';
import { ObservedImpactCard } from '../components/ObservedImpactCard';
import { BufferMetricsTable } from '../components/BufferMetricsTable';

export const AnalysisDetailPage: React.FC = () => {
  const [, params] = useRoute<{ id: string }>('/analysis/:id');
  const analysisId = (params as any)?.id || 'job-akola-001';

  const { data: job, isLoading } = useQuery({
    queryKey: ['analysisJob', analysisId],
    queryFn: () => apiClient.getAnalysis(analysisId),
  });

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-3">
        <Link href="/change-detection">
          <a className="inline-flex items-center space-x-1 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-900 px-2.5 py-1.5 rounded border border-slate-200 dark:border-slate-800 shadow-sm transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Change Detection</span>
          </a>
        </Link>
        <span className="text-slate-300 dark:text-slate-700">/</span>
        <span className="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 uppercase">{analysisId}</span>
      </div>

      {/* Header Info */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 uppercase">
                {job?.status || 'COMPLETED'}
              </span>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                Mode: {job?.mode || 'satellite'}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
              Bi-Temporal Analysis Dossier: {analysisId}
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Location Offset: {job?.location_difference_meters ?? 0}m • Temporal Distance: {job?.temporal_difference_days ?? 4018} days
            </p>
          </div>

          <Link href="/reports">
            <a className="inline-flex items-center space-x-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 px-3.5 py-2 rounded shadow-sm">
              <FileCheck className="w-4 h-4" />
              <span>View Audit Certificate</span>
            </a>
          </Link>
        </div>
      </div>

      {/* Observed Impact Card */}
      <ObservedImpactCard impact={job?.observed_impact} />

      {/* Buffer Metrics */}
      <BufferMetricsTable
        metrics={job?.spatial_metrics}
        activeBufferDistance={250}
        onSelectBuffer={() => {}}
      />
    </div>
  );
};
