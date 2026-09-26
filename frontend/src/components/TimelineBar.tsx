import React from 'react';
import { Calendar, Clock, CheckCircle2, Flag } from 'lucide-react';

interface TimelineEvent {
  date: string;
  label: string;
  type: 'T0' | 'CONSTRUCTION' | 'T1' | 'MONITORING';
  details?: string;
}

interface TimelineBarProps {
  events?: TimelineEvent[];
  t0Date?: string;
  t1Date?: string;
  implementationDate?: string;
  className?: string;
}

export const TimelineBar: React.FC<TimelineBarProps> = ({
  events,
  t0Date = '2007-03-01',
  t1Date = '2018-03-01',
  implementationDate = '2012-05-15',
  className = '',
}) => {
  const defaultEvents: TimelineEvent[] = events || [
    {
      date: t0Date,
      label: 'Baseline Imagery (T0)',
      type: 'T0',
      details: 'Google Earth / Landsat-7 Baseline Scene',
    },
    {
      date: implementationDate,
      label: 'Intervention Execution',
      type: 'CONSTRUCTION',
      details: 'Farm Pond Excavation & Bund Construction',
    },
    {
      date: t1Date,
      label: 'Post-Construction Verification (T1)',
      type: 'T1',
      details: 'Sentinel-2 / GE High Resolution Verification',
    },
    {
      date: '2026-09-06',
      label: 'Current Surveillance',
      type: 'MONITORING',
      details: 'Operational AI Satellite Monitoring Active',
    },
  ];

  return (
    <div className={`bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-3 shadow-sm transition-colors duration-200 ${className}`}>
      <div className="flex items-center justify-between mb-3 text-xs">
        <div className="flex items-center space-x-2 font-bold text-slate-800 dark:text-white">
          <Clock className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
          <span>Intervention Lifecycle & Surveillance Timeline</span>
        </div>
        <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">2007 — 2026</span>
      </div>

      <div className="relative flex items-center justify-between pt-2 pb-1 px-4">
        {/* Horizontal background track line */}
        <div className="absolute top-4 left-6 right-6 h-0.5 bg-slate-200 dark:bg-slate-700 -z-0"></div>

        {defaultEvents.map((evt, idx) => {
          const isT0 = evt.type === 'T0';
          const isT1 = evt.type === 'T1';
          const isConst = evt.type === 'CONSTRUCTION';

          return (
            <div key={idx} className="relative z-10 flex flex-col items-center text-center max-w-[120px]">
              {/* Dot */}
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center border-2 bg-white dark:bg-slate-800 shadow-sm ${
                  isT0
                    ? 'border-blue-600 text-blue-600'
                    : isT1
                    ? 'border-emerald-600 text-emerald-600'
                    : isConst
                    ? 'border-amber-600 text-amber-600'
                    : 'border-slate-400 dark:border-slate-600 text-slate-400 dark:text-slate-500'
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    isT0
                      ? 'bg-blue-600'
                      : isT1
                      ? 'bg-emerald-600'
                      : isConst
                      ? 'bg-amber-600'
                      : 'bg-slate-400 dark:bg-slate-500'
                  }`}
                />
              </div>

              {/* Date */}
              <span className="text-[10px] font-mono font-bold text-slate-700 dark:text-slate-300 mt-1">
                {evt.date}
              </span>

              {/* Label */}
              <span className="text-[11px] font-semibold text-slate-800 dark:text-slate-200 leading-tight mt-0.5">
                {evt.label}
              </span>

              {/* Details */}
              {evt.details && (
                <span className="text-[9px] text-slate-400 dark:text-slate-500 leading-tight mt-0.5 hidden sm:block">
                  {evt.details}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
