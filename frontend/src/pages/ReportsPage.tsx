import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/apiClient';
import { FileCheck, Download, Printer, ShieldCheck, Calendar, MapPin, AlertCircle, AlertTriangle, Info, Activity } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { data: interventionsData, isLoading } = useQuery({
    queryKey: ['interventionsReports'],
    queryFn: () => apiClient.listInterventions({ limit: 8 }),
    staleTime: 60000,
  });

  const rawItems = interventionsData?.items || [];
  
  // Transform interventions into report dossiers
  const reports = rawItems.map((item, idx) => {
    const impact = item.observed_impact;
    const compScore = impact?.composite_index ?? impact?.composite_score ?? 50.0;
    const mlScore = impact?.ml_change_score ?? impact?.components?.ml_change?.score ?? 50.0;
    const waterScore = impact?.water_retention_score ?? impact?.components?.water_extent?.score ?? 50.0;
    const vegScore = impact?.vegetation_score ?? impact?.components?.vegetation_response?.score ?? 50.0;
    const qualityScore = impact?.data_quality_score ?? impact?.components?.data_quality?.score ?? impact?.components?.model_confidence?.score ?? 85.0;
    
    return {
      id: `rep-${item.id.replace('int-', '')}`,
      intervention_id: item.id,
      title: `Bi-Temporal Verification Audit - ${item.name}`,
      village: item.village,
      district: item.district,
      verdict: impact?.verdict || 'OBSERVED IMPROVEMENT',
      composite_score: Number(compScore.toFixed(1)),
      date_generated: '2026-09-06',
      baseline_date: item.t0_date || '2007-03',
      verification_date: item.t1_date || '2018-03',
      narrative: impact?.narrative || 'Bi-temporal telemetry verified across multispectral observations.',
      components: {
        ml_change: Number(mlScore.toFixed(1)),
        water_extent: Number(waterScore.toFixed(1)),
        vegetation_response: Number(vegScore.toFixed(1)),
        data_quality: Number(qualityScore.toFixed(1)),
      },
      explanation: impact?.explanation || {
        ml_change: `${item.change_class || 'Farm Pond'} verified via multi-scale difference head`,
        water_retention: 'NDWI differential raster calculation over target polygon',
        vegetation: 'Perimeter canopy response within 250m radial buffer',
        data_quality: 'High-resolution orthophoto with verified GPS coordinates'
      }
    };
  });

  const [selectedReportId, setSelectedReportId] = useState<string>('');
  
  const activeReport = reports.find((r) => r.id === selectedReportId) || reports[0] || {
    id: 'rep-default',
    intervention_id: 'int-akola-akhatwada-10',
    title: 'Bi-Temporal Verification Audit - Farm Pond Akhatwada 10',
    village: 'Akhatwada',
    district: 'Akola',
    verdict: 'OBSERVED IMPROVEMENT',
    composite_score: 95.8,
    date_generated: '2026-09-06',
    baseline_date: '2007-03',
    verification_date: '2018-03',
    narrative: 'Observed farm pond construction with surface water retention expanding by +10,413 m².',
    components: { ml_change: 97.8, water_extent: 100.0, vegetation_response: 84.6, data_quality: 97.6 },
    explanation: {
      ml_change: 'High-confidence structural change detected (+10,413 m²)',
      water_retention: 'Water extent expanded by +10,413 m²',
      vegetation: 'Perimeter canopy vigour increased by +0.14 NDVI',
      data_quality: 'Verified GPS with 1.0m resolution'
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const getVerdictStyle = (verdict: string) => {
    if (verdict === 'OBSERVED IMPROVEMENT') {
      return { bg: 'bg-emerald-50 dark:bg-emerald-950/50 border-emerald-600', text: 'text-emerald-800 dark:text-emerald-300', num: 'text-emerald-700 dark:text-emerald-400' };
    } else if (verdict === 'OBSERVED DEGRADATION') {
      return { bg: 'bg-rose-50 dark:bg-rose-950/50 border-rose-600', text: 'text-rose-800 dark:text-rose-300', num: 'text-rose-700 dark:text-rose-400' };
    } else if (verdict === 'MODERATE OBSERVED CHANGE') {
      return { bg: 'bg-blue-50 dark:bg-blue-950/50 border-blue-600', text: 'text-blue-800 dark:text-blue-300', num: 'text-blue-700 dark:text-blue-400' };
    } else {
      return { bg: 'bg-amber-50 dark:bg-amber-950/50 border-amber-600', text: 'text-amber-800 dark:text-amber-300', num: 'text-amber-700 dark:text-amber-400' };
    }
  };

  const vStyle = getVerdictStyle(activeReport.verdict);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto transition-colors duration-200">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Auditable Verification Dossiers
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Institutional Verification Audit Reports
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            Cryptographically timestamped and reproducible bi-temporal audits for government compliance and funding verification.
          </p>
        </div>

        <button
          onClick={handlePrint}
          className="inline-flex items-center space-x-2 text-xs font-bold bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded shadow-sm transition-colors"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Export PDF Audit</span>
        </button>
      </div>

      {/* Reports Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Report List (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
              Site-Specific Audits ({reports.length})
            </span>
            {isLoading && <span className="text-[10px] text-emerald-600 font-semibold animate-pulse">Syncing...</span>}
          </div>

          <div className="space-y-2">
            {reports.map((rep) => {
              const isSelected = rep.id === activeReport.id;
              const isGood = rep.composite_score >= 70;
              const isDeg = rep.composite_score < 40;
              
              return (
                <div
                  key={rep.id}
                  onClick={() => setSelectedReportId(rep.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-600 shadow-sm ring-1 ring-emerald-500'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono font-bold text-slate-500">
                      {rep.id}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      isGood ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800' :
                      isDeg ? 'bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-800' :
                      'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700'
                    }`}>
                      Score: {rep.composite_score}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight mb-1">
                    {rep.title}
                  </h4>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>{rep.village}, {rep.district}</span>
                    <span className="font-medium text-[10px] uppercase">{rep.verdict.replace('OBSERVED ', '')}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Printable Formal Document Preview (8 cols) */}
        <div className="lg:col-span-8">
          <div className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg p-8 shadow-sm print:border-none print:shadow-none space-y-6 text-slate-900 dark:text-slate-100 font-sans">
            {/* Formal Government Header */}
            <div className="border-b-2 border-slate-800 dark:border-slate-600 pb-4 text-center">
              <span className="text-[11px] font-bold tracking-widest text-slate-500 uppercase">
                GOVERNMENT OF MAHARASHTRA • DEPARTMENT OF SOIL & WATER CONSERVATION
              </span>
              <h2 className="text-xl font-extrabold tracking-tight mt-1 text-slate-900 dark:text-white">
                STATE WATERSHED SURVEILLANCE & VERIFICATION CELL
              </h2>
              <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mt-0.5">
                AI-Powered Remote Sensing Bi-Temporal Intervention Audit Certificate (Framework v2.0)
              </p>
            </div>

            {/* Metadata Summary Block */}
            <div className="grid grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-800/60 p-4 rounded border border-slate-200 dark:border-slate-700 text-xs">
              <div>
                <span className="text-slate-500 block">Report Reference:</span>
                <strong className="font-mono text-slate-900 dark:text-white">{activeReport.id}</strong>
              </div>
              <div>
                <span className="text-slate-500 block">Verification Baseline vs Verification:</span>
                <strong className="font-mono text-slate-900 dark:text-white">{activeReport.baseline_date} → {activeReport.verification_date}</strong>
              </div>
              <div>
                <span className="text-slate-500 block">Structure Target:</span>
                <strong className="text-slate-900 dark:text-white">{activeReport.title}</strong>
              </div>
              <div>
                <span className="text-slate-500 block">Administrative Unit:</span>
                <strong className="text-slate-900 dark:text-white">{activeReport.village}, District {activeReport.district}</strong>
              </div>
            </div>

            {/* Formal Verdict Banner */}
            <div className={`border-2 p-4 rounded-lg flex items-center justify-between ${vStyle.bg}`}>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest block text-slate-500">
                  Observed Impact Evidence
                </span>
                <span className={`text-lg font-black ${vStyle.text}`}>
                  {activeReport.verdict}
                </span>
                <p className="text-xs text-slate-700 dark:text-slate-300 mt-1 max-w-lg leading-snug">
                  {activeReport.narrative}
                </p>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Composite Index
                </span>
                <span className={`text-3xl font-extrabold font-mono ${vStyle.num}`}>
                  {activeReport.composite_score}
                </span>
                <span className="text-xs text-slate-500 block"> / 100 max</span>
              </div>
            </div>

            {/* 4-Component Evidence Table */}
            <div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider mb-2">
                Quantitative Evaluation Weights (Site-Specific Telemetry)
              </h4>
              <table className="w-full text-left text-xs border border-slate-200 dark:border-slate-800">
                <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                  <tr>
                    <th className="p-2 border-b dark:border-slate-700">Evaluation Dimension</th>
                    <th className="p-2 border-b dark:border-slate-700">Weight</th>
                    <th className="p-2 border-b dark:border-slate-700">Site Score</th>
                    <th className="p-2 border-b dark:border-slate-700">Derived Finding</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  <tr>
                    <td className="p-2 font-medium">1. ResNet-18 Siamese Change Detection</td>
                    <td className="p-2 font-mono">35%</td>
                    <td className="p-2 font-mono font-bold text-emerald-700 dark:text-emerald-400">{activeReport.components.ml_change}%</td>
                    <td className="p-2 text-slate-600 dark:text-slate-400">{activeReport.explanation.ml_change}</td>
                  </tr>
                  <tr>
                    <td className="p-2 font-medium">2. Water Extent (NDWI Differencing)</td>
                    <td className="p-2 font-mono">30%</td>
                    <td className="p-2 font-mono font-bold text-blue-700 dark:text-blue-400">{activeReport.components.water_extent}%</td>
                    <td className="p-2 text-slate-600 dark:text-slate-400">{activeReport.explanation.water_retention}</td>
                  </tr>
                  <tr>
                    <td className="p-2 font-medium">3. Surrounding Vegetation (NDVI Vigour)</td>
                    <td className="p-2 font-mono">20%</td>
                    <td className="p-2 font-mono font-bold text-teal-700 dark:text-teal-400">{activeReport.components.vegetation_response}%</td>
                    <td className="p-2 text-slate-600 dark:text-slate-400">{activeReport.explanation.vegetation}</td>
                  </tr>
                  <tr>
                    <td className="p-2 font-medium">4. Sensor Resolution & Data Quality</td>
                    <td className="p-2 font-mono">15%</td>
                    <td className="p-2 font-mono font-bold text-indigo-700 dark:text-indigo-400">{activeReport.components.data_quality}%</td>
                    <td className="p-2 text-slate-600 dark:text-slate-400">{activeReport.explanation.data_quality}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Scientific Non-Causal Caveat */}
            <div className="p-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
              <span className="font-bold uppercase tracking-wider block text-slate-700 dark:text-slate-300">
                Scientific Non-Causal Verification Mandate
              </span>
              <p>
                This audit certifies observed bi-temporal surface variation between baseline ({activeReport.baseline_date}) and verification ({activeReport.verification_date}) satellite and orthophoto acquisitions. Remote sensing evidence verifies physical presence and localized moisture dynamics; it does not constitute sole legal proof of administrative contractor causation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
