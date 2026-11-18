import type { ComponentType } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/context/ThemeContext';
import { AppShell } from '@/components/layout/AppShell';
import Landing from '@/pages/Landing';
import DashboardHome from '@/pages/dashboard/Home';
import ImageAnalysis from '@/pages/dashboard/Analyze';
import AskSatQuery from '@/pages/dashboard/Ask';
import ChangeDetection from '@/pages/dashboard/ChangeDetection';
import SatelliteMap from '@/pages/dashboard/SatelliteMap';
import Reports from '@/pages/dashboard/Reports';
import History from '@/pages/dashboard/History';
import Settings from '@/pages/dashboard/Settings';
import LiveEarth from '@/pages/dashboard/LiveEarth';
import Events from '@/pages/dashboard/Events';
import Monitoring from '@/pages/dashboard/Monitoring';
import EarthAnalyst from '@/pages/dashboard/EarthAnalyst';
import MissionMode from '@/pages/dashboard/MissionMode';
import MapCopilot from '@/pages/dashboard/MapCopilot';
import TimeMachine from '@/pages/dashboard/TimeMachine';
import Vegetation from '@/pages/dashboard/Vegetation';
import Water from '@/pages/dashboard/Water';
import NightLights from '@/pages/dashboard/NightLights';

function withShell(Component: ComponentType) {
  return (
    <AppShell>
      <Component />
    </AppShell>
  );
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={withShell(DashboardHome)} />
          <Route path="/dashboard/analyze" element={withShell(ImageAnalysis)} />
          <Route path="/dashboard/ask" element={withShell(AskSatQuery)} />
          <Route path="/dashboard/change" element={withShell(ChangeDetection)} />
          <Route path="/dashboard/map" element={withShell(SatelliteMap)} />
          <Route path="/dashboard/reports" element={withShell(Reports)} />
          <Route path="/dashboard/history" element={withShell(History)} />
          <Route path="/dashboard/settings" element={withShell(Settings)} />
          <Route path="/dashboard/live-earth" element={withShell(LiveEarth)} />
          <Route path="/dashboard/events" element={withShell(Events)} />
          <Route path="/dashboard/monitoring" element={withShell(Monitoring)} />
          <Route path="/dashboard/analyst" element={withShell(EarthAnalyst)} />
          <Route path="/dashboard/mission" element={withShell(MissionMode)} />
          <Route path="/dashboard/copilot" element={withShell(MapCopilot)} />
          <Route path="/dashboard/time-machine" element={withShell(TimeMachine)} />
          <Route path="/dashboard/vegetation" element={withShell(Vegetation)} />
          <Route path="/dashboard/water" element={withShell(Water)} />
          <Route path="/dashboard/night-lights" element={withShell(NightLights)} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
