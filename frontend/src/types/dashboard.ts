export interface Agent {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'offline';
  last_execution: string;
  success_rate: number | null;
  avg_execution_time: number | null;
  total_executions: number;
  description: string;
  enabled: boolean;
  type: string;
}

export interface Bot {
  type: 'telegram' | 'slack';
  status: string;
  commands_processed: number;
  response_time_avg: number;
  last_activity: string | null;
  connected: boolean;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: number;
  active_connections: number;
  timestamp: string;
}

export interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  acknowledged: boolean;
  source: string;
}

export interface Anomaly {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  timestamp: string;
  value: number;
  threshold: number;
}

export interface CostData {
  current_month: number | null;
  previous_month: number | null;
  trend: 'increasing' | 'decreasing' | 'stable';
  breakdown: {
    compute: number | null;
    storage: number | null;
    network: number | null;
    other: number | null;
  };
  currency: string;
  status?: string;
  message?: string;
}

export interface PerformanceData {
  avg_response_time: number;
  throughput: number;
  error_rate: number;
  availability: number;
  uptime: string;
}

export interface DashboardData {
  agents: Agent[];
  bots: Bot[];
  metrics: SystemMetrics;
  alerts: Alert[];
  anomalies: Anomaly[];
  costs: CostData;
  performance: PerformanceData;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface AgentActivityData {
  agent_name: string;
  executions: number;
  success_rate: number;
  avg_time: number;
}

export interface PerformanceTrend {
  timestamp: string;
  response_time: number;
  throughput: number;
  error_rate: number;
}
