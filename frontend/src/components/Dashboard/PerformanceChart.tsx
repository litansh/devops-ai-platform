import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { motion } from 'framer-motion';
import { PerformanceTrend } from '../../types/dashboard';

interface PerformanceChartProps {
  data: PerformanceTrend[];
  title: string;
  subtitle?: string;
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <Box
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #ecf0f1',
          borderRadius: 2,
          p: 2,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Typography variant="body2" sx={{ color: '#2c3e50', fontWeight: 600, mb: 1 }}>
          {label}
        </Typography>
        {payload.map((entry: any, index: number) => (
          <Box key={index} display="flex" alignItems="center" gap={1} mb={0.5}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: entry.color,
              }}
            />
            <Typography variant="body2" sx={{ color: '#7f8c8d' }}>
              {entry.name}:
            </Typography>
            <Typography variant="body2" sx={{ color: '#2c3e50', fontWeight: 600 }}>
              {entry.value}
            </Typography>
          </Box>
        ))}
      </Box>
    );
  }
  return null;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  title,
  subtitle,
  height = 300,
}) => {

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        sx={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          height: '100%',
        }}
      >
        <CardContent sx={{ p: 3, height: '100%' }}>
          <Box mb={3}>
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

          <Box sx={{ height: height - 100 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data}
                margin={{
                  top: 5,
                  right: 30,
                  left: 20,
                  bottom: 5,
                }}
              >
                <defs>
                  <linearGradient id="responseTimeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3498db" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3498db" stopOpacity={0.05} />
                  </linearGradient>
                  <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#27ae60" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#27ae60" stopOpacity={0.05} />
                  </linearGradient>
                  <linearGradient id="errorRateGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e74c3c" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#e74c3c" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#ecf0f1"
                  vertical={false}
                />
                
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={formatTime}
                  tick={{ fontSize: 12, fill: '#7f8c8d' }}
                  axisLine={{ stroke: '#ecf0f1' }}
                  tickLine={false}
                />
                
                <YAxis
                  tick={{ fontSize: 12, fill: '#7f8c8d' }}
                  axisLine={{ stroke: '#ecf0f1' }}
                  tickLine={false}
                />
                
                <Tooltip content={<CustomTooltip />} />
                
                <Legend
                  wrapperStyle={{
                    paddingTop: 20,
                  }}
                />
                
                <Area
                  type="monotone"
                  dataKey="response_time"
                  name="Response Time (s)"
                  stroke="#3498db"
                  strokeWidth={2}
                  fill="url(#responseTimeGradient)"
                  dot={{ fill: '#3498db', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3498db', strokeWidth: 2 }}
                />
                
                <Area
                  type="monotone"
                  dataKey="throughput"
                  name="Throughput (req/s)"
                  stroke="#27ae60"
                  strokeWidth={2}
                  fill="url(#throughputGradient)"
                  dot={{ fill: '#27ae60', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#27ae60', strokeWidth: 2 }}
                />
                
                <Area
                  type="monotone"
                  dataKey="error_rate"
                  name="Error Rate (%)"
                  stroke="#e74c3c"
                  strokeWidth={2}
                  fill="url(#errorRateGradient)"
                  dot={{ fill: '#e74c3c', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#e74c3c', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export const SimpleLineChart: React.FC<{
  data: any[];
  title: string;
  dataKey: string;
  color?: string;
  height?: number;
}> = ({ data, title, dataKey, color = '#3498db', height = 200 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        sx={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          borderRadius: 3,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          height: '100%',
        }}
      >
        <CardContent sx={{ p: 3, height: '100%' }}>
          <Typography
            variant="h6"
            component="h3"
            sx={{
              fontWeight: 600,
              color: '#2c3e50',
              fontSize: '1rem',
              mb: 2,
            }}
          >
            {title}
          </Typography>

          <Box sx={{ height: height - 80 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#ecf0f1"
                  vertical={false}
                />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12, fill: '#7f8c8d' }}
                  axisLine={{ stroke: '#ecf0f1' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#7f8c8d' }}
                  axisLine={{ stroke: '#ecf0f1' }}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey={dataKey}
                  stroke={color}
                  strokeWidth={3}
                  dot={{ fill: color, strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: color, strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};
