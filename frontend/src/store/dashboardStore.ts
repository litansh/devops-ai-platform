import { create } from 'zustand';
import { DashboardData, Agent, Bot, SystemMetrics, Alert, Anomaly } from '../types/dashboard';

interface DashboardState {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  websocketConnected: boolean;
  
  // Actions
  setData: (data: DashboardData) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setWebsocketConnected: (connected: boolean) => void;
  updateAgent: (agentName: string, updates: Partial<Agent>) => void;
  updateBot: (botType: string, updates: Partial<Bot>) => void;
  updateMetrics: (metrics: SystemMetrics) => void;
  addAlert: (alert: Alert) => void;
  removeAlert: (alertId: string) => void;
  addAnomaly: (anomaly: Anomaly) => void;
  clearError: () => void;
  reset: () => void;
}

// Initial data structure for reference
// const initialData: DashboardData = {
//   agents: [],
//   bots: [],
//   metrics: {
//     cpu_usage: 0,
//     memory_usage: 0,
//     disk_usage: 0,
//     network_io: 0,
//     active_connections: 0,
//     timestamp: new Date().toISOString(),
//   },
//   alerts: [],
//   anomalies: [],
//   costs: {
//     current_month: 0,
//     previous_month: 0,
//     trend: 'stable',
//     breakdown: {
//       compute: 0,
//       storage: 0,
//       network: 0,
//       other: 0,
//     },
//     currency: 'USD',
//   },
//   performance: {
//     avg_response_time: 0,
//     throughput: 0,
//     error_rate: 0,
//     availability: 0,
//     uptime: '0h 0m',
//   },
// };

export const useDashboardStore = create<DashboardState>((set, get) => ({
  data: null,
  loading: false,
  error: null,
  lastUpdated: null,
  websocketConnected: false,

  setData: (data) => set({ 
    data, 
    lastUpdated: new Date(),
    error: null 
  }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  setWebsocketConnected: (connected) => set({ websocketConnected: connected }),

  updateAgent: (agentName, updates) => {
    const { data } = get();
    if (!data) return;

    const updatedAgents = data.agents.map(agent =>
      agent.name === agentName ? { ...agent, ...updates } : agent
    );

    set({
      data: { ...data, agents: updatedAgents },
      lastUpdated: new Date(),
    });
  },

  updateBot: (botType, updates) => {
    const { data } = get();
    if (!data) return;

    const updatedBots = data.bots.map(bot =>
      bot.type === botType ? { ...bot, ...updates } : bot
    );

    set({
      data: { ...data, bots: updatedBots },
      lastUpdated: new Date(),
    });
  },

  updateMetrics: (metrics) => {
    const { data } = get();
    if (!data) return;

    set({
      data: { ...data, metrics },
      lastUpdated: new Date(),
    });
  },

  addAlert: (alert) => {
    const { data } = get();
    if (!data) return;

    const updatedAlerts = [alert, ...data.alerts].slice(0, 50); // Keep last 50 alerts

    set({
      data: { ...data, alerts: updatedAlerts },
      lastUpdated: new Date(),
    });
  },

  removeAlert: (alertId) => {
    const { data } = get();
    if (!data) return;

    const updatedAlerts = data.alerts.filter(alert => alert.id !== alertId);

    set({
      data: { ...data, alerts: updatedAlerts },
      lastUpdated: new Date(),
    });
  },

  addAnomaly: (anomaly) => {
    const { data } = get();
    if (!data) return;

    const updatedAnomalies = [anomaly, ...data.anomalies].slice(0, 20); // Keep last 20 anomalies

    set({
      data: { ...data, anomalies: updatedAnomalies },
      lastUpdated: new Date(),
    });
  },

  clearError: () => set({ error: null }),

  reset: () => set({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null,
    websocketConnected: false,
  }),
}));

// Selectors for better performance
export const useAgents = () => useDashboardStore(state => state.data?.agents || []);
export const useBots = () => useDashboardStore(state => state.data?.bots || []);
export const useMetrics = () => useDashboardStore(state => state.data?.metrics);
export const useAlerts = () => useDashboardStore(state => state.data?.alerts || []);
export const useAnomalies = () => useDashboardStore(state => state.data?.anomalies || []);
export const useCosts = () => useDashboardStore(state => state.data?.costs);
export const usePerformance = () => useDashboardStore(state => state.data?.performance);
export const useDashboardLoading = () => useDashboardStore(state => state.loading);
export const useDashboardError = () => useDashboardStore(state => state.error);
export const useWebsocketStatus = () => useDashboardStore(state => state.websocketConnected);
export const useLastUpdated = () => useDashboardStore(state => state.lastUpdated);
