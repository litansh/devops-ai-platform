import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Collapse,
} from '@mui/material';
import {
  SmartToy,
  CheckCircle,
  Warning,
  Error,
  RadioButtonUnchecked,
  ExpandMore,
  ExpandLess,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { Agent } from '../../types/dashboard';

interface AgentStatusCardProps {
  agent: Agent;
  onExecute?: (agentName: string) => void;
  onToggle?: (agentName: string) => void;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle sx={{ color: '#27ae60' }} />;
    case 'degraded':
      return <Warning sx={{ color: '#f39c12' }} />;
    case 'unhealthy':
      return <Error sx={{ color: '#e74c3c' }} />;
    case 'offline':
      return <RadioButtonUnchecked sx={{ color: '#95a5a6' }} />;
    default:
      return <RadioButtonUnchecked sx={{ color: '#95a5a6' }} />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return '#27ae60';
    case 'degraded':
      return '#f39c12';
    case 'unhealthy':
      return '#e74c3c';
    case 'offline':
      return '#95a5a6';
    default:
      return '#95a5a6';
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'Healthy';
    case 'degraded':
      return 'Degraded';
    case 'unhealthy':
      return 'Unhealthy';
    case 'offline':
      return 'Offline';
    default:
      return 'Unknown';
  }
};

export const AgentStatusCard: React.FC<AgentStatusCardProps> = ({
  agent,
  onExecute,
  onToggle,
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const handleToggleExpand = () => {
    setExpanded(!expanded);
  };

  const handleExecute = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExecute?.(agent.name);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle?.(agent.name);
  };

  const successRateColor = agent.success_rate >= 0.9 ? '#27ae60' : 
                          agent.success_rate >= 0.7 ? '#f39c12' : '#e74c3c';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -2 }}
    >
      <Card
        sx={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${getStatusColor(agent.status)}20`,
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
          },
        }}
      >
        <CardContent sx={{ p: 2.5 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center" gap={2}>
              <Avatar
                sx={{
                  bgcolor: `${getStatusColor(agent.status)}15`,
                  color: getStatusColor(agent.status),
                  width: 48,
                  height: 48,
                }}
              >
                <SmartToy />
              </Avatar>
              
              <Box>
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{
                    fontWeight: 600,
                    color: '#2c3e50',
                    fontSize: '1.1rem',
                    mb: 0.5,
                  }}
                >
                  {agent.name}
                </Typography>
                
                <Box display="flex" alignItems="center" gap={1}>
                  {getStatusIcon(agent.status)}
                  <Chip
                    label={getStatusLabel(agent.status)}
                    size="small"
                    sx={{
                      backgroundColor: `${getStatusColor(agent.status)}15`,
                      color: getStatusColor(agent.status),
                      fontWeight: 500,
                      fontSize: '0.75rem',
                    }}
                  />
                  <Chip
                    label={agent.type}
                    size="small"
                    variant="outlined"
                    sx={{
                      borderColor: '#bdc3c7',
                      color: '#7f8c8d',
                      fontSize: '0.75rem',
                    }}
                  />
                </Box>
              </Box>
            </Box>
            
            <Box display="flex" alignItems="center" gap={1}>
              <Tooltip title={agent.enabled ? 'Disable Agent' : 'Enable Agent'}>
                <IconButton
                  size="small"
                  onClick={handleToggle}
                  sx={{
                    color: agent.enabled ? '#27ae60' : '#95a5a6',
                    '&:hover': {
                      backgroundColor: '#ecf0f1',
                    },
                  }}
                >
                  {agent.enabled ? <Stop fontSize="small" /> : <PlayArrow fontSize="small" />}
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Execute Agent">
                <IconButton
                  size="small"
                  onClick={handleExecute}
                  disabled={!agent.enabled}
                  sx={{
                    color: '#3498db',
                    '&:hover': {
                      backgroundColor: '#ecf0f1',
                    },
                    '&.Mui-disabled': {
                      color: '#bdc3c7',
                    },
                  }}
                >
                  <PlayArrow fontSize="small" />
                </IconButton>
              </Tooltip>
              
              <Tooltip title={expanded ? 'Show Less' : 'Show More'}>
                <IconButton
                  size="small"
                  onClick={handleToggleExpand}
                  sx={{
                    color: '#7f8c8d',
                    '&:hover': {
                      backgroundColor: '#ecf0f1',
                    },
                  }}
                >
                  {expanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Box>
              <Typography variant="body2" sx={{ color: '#7f8c8d', mb: 0.5 }}>
                Success Rate
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  color: successRateColor,
                }}
              >
                {(agent.success_rate * 100).toFixed(1)}%
              </Typography>
            </Box>
            
            <Box textAlign="right">
              <Typography variant="body2" sx={{ color: '#7f8c8d', mb: 0.5 }}>
                Avg Time
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  color: '#2c3e50',
                }}
              >
                {agent.avg_execution_time.toFixed(2)}s
              </Typography>
            </Box>
            
            <Box textAlign="right">
              <Typography variant="body2" sx={{ color: '#7f8c8d', mb: 0.5 }}>
                Executions
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  color: '#2c3e50',
                }}
              >
                {agent.total_executions}
              </Typography>
            </Box>
          </Box>

          <Collapse in={expanded}>
            <Box mt={2} pt={2} borderTop="1px solid #ecf0f1">
              <Typography
                variant="body2"
                sx={{
                  color: '#7f8c8d',
                  mb: 1.5,
                  lineHeight: 1.6,
                }}
              >
                {agent.description}
              </Typography>
              
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="caption" sx={{ color: '#95a5a6' }}>
                  Last execution:
                </Typography>
                <Typography variant="caption" sx={{ color: '#2c3e50', fontWeight: 500 }}>
                  {formatDistanceToNow(new Date(agent.last_execution), { addSuffix: true })}
                </Typography>
              </Box>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    </motion.div>
  );
};
