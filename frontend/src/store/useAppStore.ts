import { create } from 'zustand';
import { AnalysisJob, Intervention, PresetItem } from '../types/api';

interface AppState {
  selectedInterventionId: string | null;
  selectedWatershedId: string | null;
  isDemoMode: boolean;
  activeBufferDistance: number;
  selectedPreset: PresetItem | null;
  recentAnalyses: AnalysisJob[];
  
  theme: 'light' | 'dark';
  
  // Actions
  setSelectedInterventionId: (id: string | null) => void;
  setSelectedWatershedId: (id: string | null) => void;
  toggleDemoMode: () => void;
  setDemoMode: (enabled: boolean) => void;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setActiveBufferDistance: (dist: number) => void;
  setSelectedPreset: (preset: PresetItem | null) => void;
  addRecentAnalysis: (job: AnalysisJob) => void;
}

const getInitialTheme = (): 'light' | 'dark' => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('waterscope-theme');
    if (saved === 'dark' || saved === 'light') {
      if (saved === 'dark') document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      return saved;
    }
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.classList.add('dark');
      return 'dark';
    }
  }
  return 'light';
};

export const useAppStore = create<AppState>((set) => ({
  selectedInterventionId: 'int-akola-akhatwada-0',
  selectedWatershedId: null,
  isDemoMode: true,
  theme: getInitialTheme(),
  activeBufferDistance: 250,
  selectedPreset: null,
  recentAnalyses: [],

  setSelectedInterventionId: (id) => set({ selectedInterventionId: id }),
  setSelectedWatershedId: (id) => set({ selectedWatershedId: id }),
  toggleDemoMode: () => set((state) => ({ isDemoMode: !state.isDemoMode })),
  setDemoMode: (enabled) => set({ isDemoMode: enabled }),
  toggleTheme: () =>
    set((state) => {
      const next = state.theme === 'dark' ? 'light' : 'dark';
      if (typeof window !== 'undefined') {
        localStorage.setItem('waterscope-theme', next);
        if (next === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
      return { theme: next };
    }),
  setTheme: (theme) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('waterscope-theme', theme);
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
    set({ theme });
  },
  setActiveBufferDistance: (dist) => set({ activeBufferDistance: dist }),
  setSelectedPreset: (preset) => set({ selectedPreset: preset }),
  addRecentAnalysis: (job) =>
    set((state) => ({
      recentAnalyses: [job, ...state.recentAnalyses.filter((j) => j.id !== job.id)].slice(0, 10),
    })),
}));
