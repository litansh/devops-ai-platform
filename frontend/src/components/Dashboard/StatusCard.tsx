import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Refresh,
  Info,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

interface StatusCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  status?: 'success' | 'warning' | 'error' | 'info';
  trend?: 'up' | 'down' | 'stable';
  progress?: number;
  icon?: React.ReactNode;
  onClick?: () => void;
  onRefresh?: () => void;
  timestamp?: string;
  children?: React.ReactNode;
}

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'success':
      return '#27ae60';
    case 'warning':
      return '#f39c12';
    case 'error':
      return '#e74c3c';
    case 'info':
      return '#3498db';
    default:
      return '#95a5a6';
  }
};

const getTrendIcon = (trend?: string) => {
  switch (trend) {
    case 'up':
      return <TrendingUp sx={{ color: '#27ae60' }} />;
    case 'down':
      return <TrendingDown sx={{ color: '#e74c3c' }} />;
    case 'stable':
      return <TrendingFlat sx={{ color: '#95a5a6' }} />;
    default:
      return null;
  }
};

const getTrendColor = (trend?: string) => {
  switch (trend) {
    case 'up':
      return '#27ae60';
    case 'down':
      return '#e74c3c';
    case 'stable':
      return '#95a5a6';
    default:
      return '#95a5a6';
  }
};

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtitle,
  status,
  trend,
  progress,
  icon,
  onClick,
  onRefresh,
  timestamp,
  children,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -5 }}
    >
      <Card
        sx={{
          height: '100%',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${getStatusColor(status)}20`,
          cursor: onClick ? 'pointer' : 'default',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.15)',
            transform: 'translateY(-2px)',
          },
        }}
        onClick={onClick}
      >
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              {icon && (
                <Box
                  sx={{
                    p: 1,
                    borderRadius: 2,
                    backgroundColor: `${getStatusColor(status)}15`,
                    color: getStatusColor(status),
                  }}
                >
                  {icon}
                </Box>
              )}
              <Box>
                <Typography
                  variant="h6"
                  component="h3"
                  sx={{
                    fontWeight: 600,
                    color: '#2c3e50',
                    fontSize: '1.1rem',
                  }}
                >
                  {title}
                </Typography>
                {subtitle && (
                  <Typography
                    variant="body2"
                    sx={{
                      color: '#7f8c8d',
                      fontSize: '0.875rem',
                    }}
                  >
                    {subtitle}
                  </Typography>
                )}
              </Box>
            </Box>
            
            <Box display="flex" alignItems="center" gap={1}>
              {trend && getTrendIcon(trend)}
              {onRefresh && (
                <Tooltip title="Refresh">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRefresh();
                    }}
                    sx={{
                      color: '#7f8c8d',
                      '&:hover': {
                        backgroundColor: '#ecf0f1',
                      },
                    }}
                  >
                    <Refresh fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>

          <Box mb={2}>
            <Typography
              variant="h4"
              component="div"
              sx={{
                fontWeight: 700,
                color: getStatusColor(status),
                fontSize: '2rem',
                lineHeight: 1.2,
              }}
            >
              {value}
            </Typography>
            
            {trend && (
              <Box display="flex" alignItems="center" gap={0.5} mt={0.5}>
                {getTrendIcon(trend)}
                <Typography
                  variant="body2"
                  sx={{
                    color: getTrendColor(trend),
                    fontWeight: 500,
                    fontSize: '0.875rem',
                  }}
                >
                  {trend === 'up' && 'Increasing'}
                  {trend === 'down' && 'Decreasing'}
                  {trend === 'stable' && 'Stable'}
                </Typography>
              </Box>
            )}
          </Box>

          {progress !== undefined && (
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={0.5}>
                <Typography variant="body2" sx={{ color: '#7f8c8d' }}>
                  Progress
                </Typography>
                <Typography variant="body2" sx={{ color: '#7f8c8d' }}>
                  {progress}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: '#ecf0f1',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3,
                    backgroundColor: getStatusColor(status),
                  },
                }}
              />
            </Box>
          )}

          {timestamp && (
            <Box display="flex" alignItems="center" gap={0.5} mb={1}>
              <Info fontSize="small" sx={{ color: '#95a5a6', fontSize: '1rem' }} />
              <Typography
                variant="caption"
                sx={{
                  color: '#95a5a6',
                  fontSize: '0.75rem',
                }}
              >
                Updated {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
              </Typography>
            </Box>
          )}

          {children}
        </CardContent>
      </Card>
    </motion.div>
  );
};
