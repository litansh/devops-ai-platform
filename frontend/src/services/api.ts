import axios from 'axios';
import { DashboardData, Agent } from '../types/dashboard';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// API endpoints
const ENDPOINTS = {
  dashboardData: '/api/dashboard/data',
  dashboardHealth: '/api/dashboard/health',
  health: '/health',
  agents: '/agents',
  executeAgent: (name: string) => `/agents/${name}/execute`,
  restartAgent: (name: string) => `/agents/${name}/restart`,
  toggleAgent: (name: string) => `/agents/${name}/toggle`,
  deleteAgent: (name: string) => `/agents/${name}`,
  metrics: '/metrics',
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  // Get dashboard data
  getDashboardData: async (): Promise<DashboardData> => {
    const response = await api.get(ENDPOINTS.dashboardData);
    return response.data;
  },

  // Refresh dashboard data
  refreshDashboard: async (): Promise<{ status: string; message: string }> => {
    const response = await api.get(ENDPOINTS.dashboardData);
    return response.data;
  },

  // Get platform health
  getHealth: async () => {
    const response = await api.get(ENDPOINTS.dashboardHealth);
    return response.data;
  },

  // Get agents list
  getAgents: async (): Promise<{ agents: Agent[] }> => {
    const response = await api.get(ENDPOINTS.agents);
    return response.data;
  },

  // Execute agent
  executeAgent: async (agentName: string, context?: any) => {
    const response = await api.post(ENDPOINTS.executeAgent(agentName), { context });
    return response.data;
  },

  // Restart agent
  restartAgent: async (agentName: string) => {
    const response = await api.post(ENDPOINTS.restartAgent(agentName));
    return response.data;
  },

  // Toggle agent (enable/disable)
  toggleAgent: async (agentName: string) => {
    const response = await api.post(ENDPOINTS.toggleAgent(agentName));
    return response.data;
  },

  // Delete agent
  deleteAgent: async (agentName: string) => {
    const response = await api.delete(ENDPOINTS.deleteAgent(agentName));
    return response.data;
  },

  // Get metrics
  getMetrics: async () => {
    const response = await api.get(ENDPOINTS.metrics);
    return response.data;
  },
};

export const websocketService = {
  connect: (onMessage: (data: any) => void, onError?: (error: any) => void) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host.replace('3000', '8000')}/dashboard/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    return ws;
  },
};

export default api;
