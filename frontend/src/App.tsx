import React from 'react';
import { Switch, Route, Redirect } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { InterventionsPage } from './pages/InterventionsPage';
import { InterventionDetailPage } from './pages/InterventionDetailPage';
import { BeforeAfterPage } from './pages/BeforeAfterPage';
import { ChangeDetectionPage } from './pages/ChangeDetectionPage';
import { WatershedsPage } from './pages/WatershedsPage';
import { WatershedDetailPage } from './pages/WatershedDetailPage';
import { PriorityZonesPage } from './pages/PriorityZonesPage';
import { ReportsPage } from './pages/ReportsPage';
import { EvidencePage } from './pages/EvidencePage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { SettingsPage } from './pages/SettingsPage';
import { AnalysisDetailPage } from './pages/AnalysisDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
        {/* Institutional Navbar */}
        <Navbar />

        {/* Main Content Layout with Sidebar */}
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
            <Switch>
              <Route path="/" component={DashboardPage} />
              <Route path="/interventions" component={InterventionsPage} />
              <Route path="/interventions/:id" component={InterventionDetailPage} />
              <Route path="/before-after" component={BeforeAfterPage} />
              <Route path="/change-detection" component={ChangeDetectionPage} />
              <Route path="/watersheds" component={WatershedsPage} />
              <Route path="/watersheds/:id" component={WatershedDetailPage} />
              <Route path="/priority-zones" component={PriorityZonesPage} />
              <Route path="/reports" component={ReportsPage} />
              <Route path="/evidence" component={EvidencePage} />
              <Route path="/assistant" component={AIAssistantPage} />
              <Route path="/data-sources" component={DataSourcesPage} />
              <Route path="/settings" component={SettingsPage} />
              <Route path="/analysis/:id" component={AnalysisDetailPage} />
              <Route>
                <Redirect to="/" />
              </Route>
            </Switch>
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
};

export default App;
