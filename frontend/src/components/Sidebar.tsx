import React from 'react';
import { Link, useLocation } from 'wouter';
import {
  LayoutDashboard,
  MapPin,
  SplitSquareVertical,
  ScanEye,
  Waves,
  AlertOctagon,
  FileCheck,
  FolderArchive,
  Bot,
  Layers,
  Settings,
  ShieldCheck,
  ExternalLink,
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const [location] = useLocation();
  const { selectedInterventionId } = useAppStore();

  const monitoringNav: NavItem[] = [
    { name: 'GIS Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Interventions Registry', href: '/interventions', icon: MapPin },
    {
      name: 'Site Inspection',
      href: `/interventions/${selectedInterventionId || 'int-akola-akhatwada-0'}`,
      icon: ScanEye,
      badge: 'CORE',
    },
    { name: 'Before/After Studio', href: '/before-after', icon: SplitSquareVertical },
    { name: 'Change Detection ML', href: '/change-detection', icon: ShieldCheck },
  ];

  const analysisNav: NavItem[] = [
    { name: 'Watershed Units', href: '/watersheds', icon: Waves },
    { name: 'Priority Zones', href: '/priority-zones', icon: AlertOctagon, badge: 'ALERT' },
  ];

  const verificationNav: NavItem[] = [
    { name: 'Evidence Vault', href: '/evidence', icon: FolderArchive },
    { name: 'Audit Reports', href: '/reports', icon: FileCheck },
    { name: 'AI GIS Assistant', href: '/assistant', icon: Bot },
    { name: 'Data Sources & Sensors', href: '/data-sources', icon: Layers },
  ];

  const renderNavGroup = (title: string, items: NavItem[]) => (
    <div className="mb-5">
      <h3 className="px-3 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
        {title}
      </h3>
      <div className="space-y-0.5">
        {items.map((item) => {
          const isActive =
            location === item.href ||
            (item.href.startsWith('/interventions/') && location.startsWith('/interventions/'));
          const Icon = item.icon;

          return (
            <Link key={item.name} href={item.href}>
              <a
                className={`flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-300 border-l-4 border-emerald-700 dark:border-emerald-500 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      item.badge === 'ALERT'
                        ? 'bg-rose-100 dark:bg-rose-950/70 text-rose-800 dark:text-rose-300'
                        : 'bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </a>
            </Link>
          );
        })}
      </div>
    </div>
  );

  return (
    <aside className="w-64 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)] select-none transition-colors duration-200">
      <div className="p-3 overflow-y-auto">
        {renderNavGroup('Monitoring & GIS', monitoringNav)}
        {renderNavGroup('Spatial Hydrology', analysisNav)}
        {renderNavGroup('Verification & Evidence', verificationNav)}

        <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
          <Link href="/settings">
            <a
              className={`flex items-center space-x-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                location === '/settings'
                  ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-900 dark:text-emerald-300 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <Settings className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              <span>Settings & System</span>
            </a>
          </Link>
        </div>
      </div>

      {/* Institutional Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-[11px] text-slate-500 dark:text-slate-400 transition-colors duration-200">
        <div className="flex items-center justify-between font-semibold text-slate-700 dark:text-slate-200 mb-1">
          <span>Maharashtra State GIS</span>
          <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-700">
            SECURE
          </span>
        </div>
        <p className="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">
          Soil & Water Conservation Dept. Institutional Watershed Verification Engine.
        </p>
      </div>
    </aside>
  );
};
