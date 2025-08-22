import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Typography,
  Container,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
  CircularProgress,
  Fab,
} from '@mui/material';
import {
  Refresh,
  Settings,
  Notifications,
  Dashboard as DashboardIcon,
  TrendingUp,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from 'react-query';
import toast from 'react-hot-toast';

import { StatusCard } from './StatusCard';
import { AgentStatusCard } from './AgentStatusCard';
import { PerformanceChart } from './PerformanceChart';
import { dashboardApi, websocketService } from '../../services/api';
import { useDashboardStore } from '../../store/dashboardStore';
import { DashboardData, PerformanceTrend } from '../../types/dashboard';

const DashboardHeader: React.FC = () => {
  const { websocketConnected, lastUpdated } = useDashboardStore();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Box
        sx={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          p: 4,
          mb: 4,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          border: '1px solid rgba(52, 152, 219, 0.1)',
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                color: '#2c3e50',
                mb: 1,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              🚀 DevOps AI Platform
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: '#7f8c8d',
                fontWeight: 400,
              }}
            >
              Command Center - Real-time Monitoring & Control
            </Typography>
          </Box>
          
          <Box display="flex" alignItems="center" gap={2}>
            <Box display="flex" alignItems="center" gap={1}>
              {websocketConnected ? (
                <Wifi sx={{ color: '#27ae60' }} />
              ) : (
                <WifiOff sx={{ color: '#e74c3c' }} />
              )}
              <Typography variant="body2" sx={{ color: '#7f8c8d' }}>
                {websocketConnected ? 'Live' : 'Offline'}
              </Typography>
            </Box>
            
            {lastUpdated && (
              <Chip
                label={`Updated ${lastUpdated.toLocaleTimeString()}`}
                size="small"
                variant="outlined"
                sx={{
                  borderColor: '#bdc3c7',
                  color: '#7f8c8d',
                }}
              />
            )}
            
            <Tooltip title="Settings">
              <IconButton
                sx={{
                  color: '#7f8c8d',
                  '&:hover': {
                    backgroundColor: '#ecf0f1',
                  },
                }}
              >
                <Settings />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Notifications">
              <IconButton
                sx={{
                  color: '#7f8c8d',
                  '&:hover': {
                    backgroundColor: '#ecf0f1',
                  },
                }}
              >
                <Notifications />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
};

const OverviewCards: React.FC<{ data: DashboardData }> = ({ data }) => {
  const healthyAgents = data.agents.filter(agent => agent.status === 'healthy').length;
  const totalAgents = data.agents.length;
  const connectedBots = data.bots.filter(bot => bot.connected).length;
  
  return (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} sm={6} md={3}>
        <StatusCard
          title="Platform Overview"
          value={`${healthyAgents}/${totalAgents}`}
          subtitle="Active Agents"
          status={healthyAgents === totalAgents ? 'success' : healthyAgents > totalAgents / 2 ? 'warning' : 'error'}
          progress={(healthyAgents / totalAgents) * 100}
          icon={<DashboardIcon />}
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <StatusCard
          title="Bot Activity"
          value={connectedBots}
          subtitle="Connected Bots"
          status={connectedBots > 0 ? 'success' : 'error'}
          icon={<TrendingUp />}
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <StatusCard
          title="System Health"
          value={`${data.metrics.cpu_usage.toFixed(1)}%`}
          subtitle="CPU Usage"
          status={data.metrics.cpu_usage < 70 ? 'success' : data.metrics.cpu_usage < 90 ? 'warning' : 'error'}
          progress={data.metrics.cpu_usage}
          icon={<TrendingUp />}
        />
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <StatusCard
          title="Cost Analysis"
          value={`$${data.costs.current_month.toFixed(2)}`}
          subtitle="Current Month"
          status={data.costs.current_month < 100 ? 'success' : data.costs.current_month < 500 ? 'warning' : 'error'}
          trend={data.costs.trend === 'increasing' ? 'up' : data.costs.trend === 'decreasing' ? 'down' : 'stable'}
          icon={<TrendingUp />}
        />
      </Grid>
    </Grid>
  );
};

const AgentSection: React.FC<{ agents: any[] }> = ({ agents }) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const handleExecuteAgent = async (agentName: string) => {
    try {
      await dashboardApi.executeAgent(agentName);
      toast.success(`Executed agent: ${agentName}`);
    } catch (error) {
      toast.error(`Failed to execute agent: ${agentName}`);
    }
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Typography
        variant="h5"
        component="h2"
        sx={{
          fontWeight: 600,
          color: '#2c3e50',
          mb: 3,
        }}
      >
        🤖 AI Agents Status
      </Typography>
      
      <Grid container spacing={3}>
        {agents.map((agent, index) => (
          <Grid item xs={12} sm={6} md={4} key={agent.name}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <AgentStatusCard
                agent={agent}
                onExecute={handleExecuteAgent}
                onToggle={(agentName) => {
                  setSelectedAgent(selectedAgent === agentName ? null : agentName);
                }}
              />
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const PerformanceSection: React.FC<{ performance: any }> = ({ performance }) => {
  // Generate sample performance data
  const performanceData: PerformanceTrend[] = Array.from({ length: 20 }, (_, i) => ({
    timestamp: new Date(Date.now() - (19 - i) * 60000).toISOString(),
    response_time: performance.avg_response_time + Math.random() * 0.2,
    throughput: performance.throughput + Math.random() * 5,
    error_rate: performance.error_rate + Math.random() * 0.01,
  }));

  return (
    <Box sx={{ mb: 4 }}>
      <Typography
        variant="h5"
        component="h2"
        sx={{
          fontWeight: 600,
          color: '#2c3e50',
          mb: 3,
        }}
      >
        📈 Performance Trends
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <PerformanceChart
            data={performanceData}
            title="System Performance"
            subtitle="Real-time metrics over time"
            height={400}
          />
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <StatusCard
                title="Response Time"
                value={`${performance.avg_response_time.toFixed(2)}s`}
                status={performance.avg_response_time < 1 ? 'success' : performance.avg_response_time < 2 ? 'warning' : 'error'}
                progress={Math.min((performance.avg_response_time / 2) * 100, 100)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <StatusCard
                title="Throughput"
                value={`${performance.throughput.toFixed(1)} req/s`}
                status={performance.throughput > 10 ? 'success' : performance.throughput > 5 ? 'warning' : 'error'}
                progress={Math.min((performance.throughput / 20) * 100, 100)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <StatusCard
                title="Availability"
                value={`${performance.availability.toFixed(1)}%`}
                status={performance.availability > 99 ? 'success' : performance.availability > 95 ? 'warning' : 'error'}
                progress={performance.availability}
              />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

const AlertsSection: React.FC<{ alerts: any[]; anomalies: any[] }> = ({ alerts, anomalies }) => {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography
        variant="h5"
        component="h2"
        sx={{
          fontWeight: 600,
          color: '#2c3e50',
          mb: 3,
        }}
      >
        ⚠️ Alerts & Anomalies
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: 3,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: '#2c3e50' }}>
              Recent Alerts
            </Typography>
            
            <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
              {alerts.length > 0 ? (
                alerts.map((alert) => (
                  <Alert
                    key={alert.id}
                    severity={alert.severity}
                    sx={{ mb: 1 }}
                    action={
                      <Chip
                        label={alert.source}
                        size="small"
                        variant="outlined"
                      />
                    }
                  >
                    {alert.message}
                  </Alert>
                ))
              ) : (
                <Typography variant="body2" sx={{ color: '#7f8c8d', fontStyle: 'italic' }}>
                  No alerts at the moment
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper
            sx={{
              p: 3,
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              borderRadius: 3,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, color: '#2c3e50' }}>
              Detected Anomalies
            </Typography>
            
            <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
              {anomalies.length > 0 ? (
                anomalies.map((anomaly) => (
                  <Box
                    key={anomaly.id}
                    sx={{
                      p: 2,
                      mb: 1,
                      borderRadius: 2,
                      backgroundColor: '#fff3cd',
                      border: '1px solid #ffeaa7',
                    }}
                  >
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#856404', mb: 0.5 }}>
                      {anomaly.description}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#856404' }}>
                      Value: {anomaly.value} (Threshold: {anomaly.threshold})
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" sx={{ color: '#7f8c8d', fontStyle: 'italic' }}>
                  No anomalies detected
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export const MainDashboard: React.FC = () => {
  const {
    data,
    loading,
    error,
    setData,
    setLoading,
    setError,
    setWebsocketConnected,
  } = useDashboardStore();

  const { refetch } = useQuery(
    'dashboardData',
    dashboardApi.getDashboardData,
    {
      onSuccess: (data) => {
        setData(data);
        setError(null);
      },
      onError: (error: any) => {
        setError(error.message);
        toast.error('Failed to load dashboard data');
      },
      refetchInterval: 30000, // Refresh every 30 seconds
      refetchIntervalInBackground: true,
    }
  );

  useEffect(() => {
    let ws: WebSocket | null = null;

    const connectWebSocket = () => {
      ws = websocketService.connect(
        (message) => {
          if (message.type === 'dashboard_update') {
            setData(message.data);
          }
        },
        (error) => {
          console.error('WebSocket error:', error);
          setWebsocketConnected(false);
        }
      );

      ws.onopen = () => {
        setWebsocketConnected(true);
      };

      ws.onclose = () => {
        setWebsocketConnected(false);
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [setData, setWebsocketConnected]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await refetch();
      toast.success('Dashboard refreshed');
    } catch (error) {
      toast.error('Failed to refresh dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <CircularProgress size={60} sx={{ color: 'white' }} />
      </Box>
    );
  }

  if (error && !data) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        <DashboardHeader />
        
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <OverviewCards data={data} />
            <AgentSection agents={data.agents} />
            <PerformanceSection performance={data.performance} />
            <AlertsSection alerts={data.alerts} anomalies={data.anomalies} />
          </motion.div>
        </AnimatePresence>
        
        <Fab
          color="primary"
          aria-label="refresh"
          onClick={handleRefresh}
          disabled={loading}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            background: 'rgba(52, 152, 219, 0.9)',
            backdropFilter: 'blur(10px)',
            '&:hover': {
              background: 'rgba(52, 152, 219, 1)',
            },
          }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : <Refresh />}
        </Fab>
        
        <Snackbar
          open={!!error}
          autoHideDuration={6000}
          onClose={() => setError(null)}
        >
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};
