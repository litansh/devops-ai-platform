"""
Modern Web Dashboard for DevOps AI Platform

This module provides a comprehensive web dashboard with real-time monitoring,
agent status, bot activity, and interactive controls for the platform.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.logging import LoggerMixin
from core.config import Settings
from agents.registry import AgentRegistry


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


class BotType(str, Enum):
    """Bot type enumeration."""
    TELEGRAM = "telegram"
    SLACK = "slack"


@dataclass
class AgentInfo:
    """Agent information for dashboard."""
    name: str
    status: AgentStatus
    last_execution: datetime
    success_rate: float
    avg_execution_time: float
    total_executions: int
    description: str
    enabled: bool


@dataclass
class BotInfo:
    """Bot information for dashboard."""
    type: BotType
    status: str
    commands_processed: int
    response_time_avg: float
    last_activity: datetime
    connected: bool


@dataclass
class SystemMetrics:
    """System metrics for dashboard."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    active_connections: int


@dataclass
class AlertInfo:
    """Alert information for dashboard."""
    id: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool
    source: str


class DashboardData(BaseModel):
    """Dashboard data model."""
    agents: List[Dict[str, Any]]
    bots: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    costs: Dict[str, Any]
    performance: Dict[str, Any]


class DashboardManager(LoggerMixin):
    """Manages the dashboard data and real-time updates."""
    
    def __init__(self, settings: Settings, agent_registry: AgentRegistry):
        self.settings = settings
        self.agent_registry = agent_registry
        self.websocket_connections: List[WebSocket] = []
        self.dashboard_data = DashboardData(
            agents=[],
            bots=[],
            metrics={},
            alerts=[],
            anomalies=[],
            costs={},
            performance={}
        )
        
        self.logger.info("DashboardManager initialized")
    
    async def get_agent_data(self) -> List[Dict[str, Any]]:
        """Get current agent data for dashboard."""
        agents = []
        
        for agent in self.agent_registry.agents.values():
            # Simulate agent metrics (in real implementation, get from monitoring)
            agent_info = {
                "name": agent.name,
                "status": agent.get_health_status(),
                "last_execution": datetime.now().isoformat(),
                "success_rate": 0.95,  # Simulated
                "avg_execution_time": 0.5,  # Simulated
                "total_executions": 150,  # Simulated
                "description": agent.description,
                "enabled": agent.enabled,
                "type": agent.agent_type.value
            }
            agents.append(agent_info)
        
        return agents
    
    async def get_bot_data(self) -> List[Dict[str, Any]]:
        """Get current bot data for dashboard."""
        bots = []
        
        # Simulate bot data (in real implementation, get from bot gateway)
        telegram_bot = {
            "type": "telegram",
            "status": "connected",
            "commands_processed": 45,
            "response_time_avg": 0.3,
            "last_activity": datetime.now().isoformat(),
            "connected": True
        }
        
        slack_bot = {
            "type": "slack",
            "status": "not_configured",
            "commands_processed": 0,
            "response_time_avg": 0.0,
            "last_activity": None,
            "connected": False
        }
        
        bots.extend([telegram_bot, slack_bot])
        return bots
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        # Simulate system metrics (in real implementation, get from monitoring)
        return {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 23.1,
            "network_io": 12.5,
            "active_connections": 8,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts."""
        # Simulate alerts (in real implementation, get from alert manager)
        alerts = [
            {
                "id": "alert-001",
                "severity": "warning",
                "message": "Agent health check: 0/8 agents healthy",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False,
                "source": "agent_health_check"
            }
        ]
        return alerts
    
    async def get_anomalies(self) -> List[Dict[str, Any]]:
        """Get detected anomalies."""
        # Simulate anomalies (in real implementation, get from anomaly detector)
        return [
            {
                "id": "anomaly-001",
                "type": "performance",
                "severity": "medium",
                "description": "Unusual CPU spike detected",
                "timestamp": datetime.now().isoformat(),
                "value": 85.2,
                "threshold": 70.0
            }
        ]
    
    async def get_cost_data(self) -> Dict[str, Any]:
        """Get cost analysis data."""
        # Simulate cost data (in real implementation, get from cost watcher)
        return {
            "current_month": 0.0,
            "previous_month": 0.0,
            "trend": "stable",
            "breakdown": {
                "compute": 0.0,
                "storage": 0.0,
                "network": 0.0,
                "other": 0.0
            },
            "currency": "USD"
        }
    
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get performance metrics."""
        # Simulate performance data (in real implementation, get from monitoring)
        return {
            "avg_response_time": 0.3,
            "throughput": 15.2,
            "error_rate": 0.02,
            "availability": 99.8,
            "uptime": "2h 15m"
        }
    
    async def update_dashboard_data(self):
        """Update dashboard data with current information."""
        try:
            self.dashboard_data.agents = await self.get_agent_data()
            self.dashboard_data.bots = await self.get_bot_data()
            self.dashboard_data.metrics = await self.get_system_metrics()
            self.dashboard_data.alerts = await self.get_alerts()
            self.dashboard_data.anomalies = await self.get_anomalies()
            self.dashboard_data.costs = await self.get_cost_data()
            self.dashboard_data.performance = await self.get_performance_data()
            
            # Broadcast to all connected clients
            await self.broadcast_update()
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard data: {e}")
    
    async def broadcast_update(self):
        """Broadcast dashboard update to all connected clients."""
        if not self.websocket_connections:
            return
        
        data = self.dashboard_data.dict()
        message = json.dumps({
            "type": "dashboard_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        disconnected = []
        for connection in self.websocket_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending to websocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.websocket_connections.remove(connection)
    
    async def add_websocket_connection(self, websocket: WebSocket):
        """Add a new websocket connection."""
        self.websocket_connections.append(websocket)
        self.logger.info(f"New dashboard connection. Total: {len(self.websocket_connections)}")
    
    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove a websocket connection."""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            self.logger.info(f"Dashboard connection removed. Total: {len(self.websocket_connections)}")


# FastAPI router for dashboard endpoints
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Global dashboard manager instance
dashboard_manager: Optional[DashboardManager] = None


@dashboard_router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the main dashboard HTML page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DevOps AI Platform - Command Center</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
            }
            
            .dashboard {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            
            .header h1 {
                color: #2c3e50;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-align: center;
            }
            
            .header p {
                color: #7f8c8d;
                text-align: center;
                font-size: 1.1em;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }
            
            .card h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.3em;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            
            .metric {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding: 10px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 8px;
            }
            
            .metric-label {
                font-weight: 600;
                color: #2c3e50;
            }
            
            .metric-value {
                font-weight: bold;
                color: #3498db;
            }
            
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            
            .status-healthy { background-color: #27ae60; }
            .status-degraded { background-color: #f39c12; }
            .status-unhealthy { background-color: #e74c3c; }
            .status-offline { background-color: #95a5a6; }
            
            .agent-list {
                max-height: 300px;
                overflow-y: auto;
            }
            
            .agent-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                margin-bottom: 8px;
                background: rgba(52, 152, 219, 0.05);
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }
            
            .chart-container {
                position: relative;
                height: 200px;
                margin-top: 15px;
            }
            
            .alert-item {
                padding: 10px;
                margin-bottom: 8px;
                border-radius: 8px;
                border-left: 4px solid;
            }
            
            .alert-warning {
                background: rgba(243, 156, 18, 0.1);
                border-left-color: #f39c12;
            }
            
            .alert-error {
                background: rgba(231, 76, 60, 0.1);
                border-left-color: #e74c3c;
            }
            
            .refresh-button {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.3s ease;
            }
            
            .refresh-button:hover {
                background: #2980b9;
            }
            
            .connection-status {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 15px;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }
            
            .connected {
                background: #27ae60;
            }
            
            .disconnected {
                background: #e74c3c;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🚀 DevOps AI Platform</h1>
                <p>Command Center - Real-time Monitoring & Control</p>
            </div>
            
            <div class="connection-status" id="connectionStatus">
                Connecting...
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🤖 AI Agents Status</h3>
                    <div class="agent-list" id="agentsList">
                        Loading agents...
                    </div>
                </div>
                
                <div class="card">
                    <h3>💬 Bot Activity</h3>
                    <div id="botsList">
                        Loading bots...
                    </div>
                </div>
                
                <div class="card">
                    <h3>📊 System Metrics</h3>
                    <div id="systemMetrics">
                        Loading metrics...
                    </div>
                </div>
                
                <div class="card">
                    <h3>💰 Cost Analysis</h3>
                    <div id="costData">
                        Loading cost data...
                    </div>
                </div>
                
                <div class="card">
                    <h3>⚠️ Recent Alerts</h3>
                    <div id="alertsList">
                        Loading alerts...
                    </div>
                </div>
                
                <div class="card">
                    <h3>🔍 Anomaly Detection</h3>
                    <div id="anomaliesList">
                        Loading anomalies...
                    </div>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📈 Performance Trends</h3>
                    <div class="chart-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎯 Agent Activity</h3>
                    <div class="chart-container">
                        <canvas id="activityChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px;">
                <button class="refresh-button" onclick="refreshData()">
                    🔄 Refresh Data
                </button>
            </div>
        </div>
        
        <script>
            let ws = null;
            let performanceChart = null;
            let activityChart = null;
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/dashboard/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    document.getElementById('connectionStatus').textContent = '🟢 Connected';
                    document.getElementById('connectionStatus').className = 'connection-status connected';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'dashboard_update') {
                        updateDashboard(data.data);
                    }
                };
                
                ws.onclose = function() {
                    document.getElementById('connectionStatus').textContent = '🔴 Disconnected';
                    document.getElementById('connectionStatus').className = 'connection-status disconnected';
                    setTimeout(connectWebSocket, 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function updateDashboard(data) {
                updateAgents(data.agents);
                updateBots(data.bots);
                updateSystemMetrics(data.metrics);
                updateCostData(data.costs);
                updateAlerts(data.alerts);
                updateAnomalies(data.anomalies);
                updateCharts(data);
            }
            
            function updateAgents(agents) {
                const container = document.getElementById('agentsList');
                container.innerHTML = agents.map(agent => `
                    <div class="agent-item">
                        <div>
                            <span class="status-indicator status-${agent.status}"></span>
                            <strong>${agent.name}</strong>
                        </div>
                        <div>
                            <small>${agent.success_rate * 100}% success</small>
                        </div>
                    </div>
                `).join('');
            }
            
            function updateBots(bots) {
                const container = document.getElementById('botsList');
                container.innerHTML = bots.map(bot => `
                    <div class="metric">
                        <span class="metric-label">${bot.type.toUpperCase()}</span>
                        <span class="metric-value">${bot.status}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Commands</span>
                        <span class="metric-value">${bot.commands_processed}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Response Time</span>
                        <span class="metric-value">${bot.response_time_avg.toFixed(2)}s</span>
                    </div>
                `).join('');
            }
            
            function updateSystemMetrics(metrics) {
                const container = document.getElementById('systemMetrics');
                container.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">CPU Usage</span>
                        <span class="metric-value">${metrics.cpu_usage.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Memory Usage</span>
                        <span class="metric-value">${metrics.memory_usage.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Disk Usage</span>
                        <span class="metric-value">${metrics.disk_usage.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Network I/O</span>
                        <span class="metric-value">${metrics.network_io.toFixed(1)} MB/s</span>
                    </div>
                `;
            }
            
            function updateCostData(costs) {
                const container = document.getElementById('costData');
                container.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Current Month</span>
                        <span class="metric-value">$${costs.current_month.toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Previous Month</span>
                        <span class="metric-value">$${costs.previous_month.toFixed(2)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Trend</span>
                        <span class="metric-value">${costs.trend}</span>
                    </div>
                `;
            }
            
            function updateAlerts(alerts) {
                const container = document.getElementById('alertsList');
                container.innerHTML = alerts.map(alert => `
                    <div class="alert-item alert-${alert.severity}">
                        <strong>${alert.message}</strong><br>
                        <small>${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>
                `).join('');
            }
            
            function updateAnomalies(anomalies) {
                const container = document.getElementById('anomaliesList');
                container.innerHTML = anomalies.map(anomaly => `
                    <div class="alert-item alert-warning">
                        <strong>${anomaly.description}</strong><br>
                        <small>Value: ${anomaly.value} (Threshold: ${anomaly.threshold})</small>
                    </div>
                `).join('');
            }
            
            function updateCharts(data) {
                // Update performance chart
                if (performanceChart) {
                    performanceChart.data.labels.push(new Date().toLocaleTimeString());
                    performanceChart.data.datasets[0].data.push(data.performance.avg_response_time);
                    performanceChart.data.datasets[1].data.push(data.performance.throughput);
                    
                    if (performanceChart.data.labels.length > 20) {
                        performanceChart.data.labels.shift();
                        performanceChart.data.datasets[0].data.shift();
                        performanceChart.data.datasets[1].data.shift();
                    }
                    
                    performanceChart.update('none');
                }
                
                // Update activity chart
                if (activityChart) {
                    const agentNames = data.agents.map(a => a.name);
                    const executionCounts = data.agents.map(a => a.total_executions);
                    
                    activityChart.data.labels = agentNames;
                    activityChart.data.datasets[0].data = executionCounts;
                    activityChart.update();
                }
            }
            
            function initCharts() {
                // Performance chart
                const perfCtx = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(perfCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Response Time (s)',
                            data: [],
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4
                        }, {
                            label: 'Throughput (req/s)',
                            data: [],
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                
                // Activity chart
                const activityCtx = document.getElementById('activityChart').getContext('2d');
                activityChart = new Chart(activityCtx, {
                    type: 'bar',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Total Executions',
                            data: [],
                            backgroundColor: 'rgba(52, 152, 219, 0.8)',
                            borderColor: '#3498db',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function refreshData() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({type: 'refresh_request'}));
                }
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                initCharts();
                connectWebSocket();
                
                // Auto-refresh every 30 seconds
                setInterval(refreshData, 30000);
            });
        </script>
    </body>
    </html>
    """


@dashboard_router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await websocket.accept()
    
    if dashboard_manager:
        await dashboard_manager.add_websocket_connection(websocket)
        
        try:
            while True:
                # Keep connection alive
                await websocket.receive_text()
        except WebSocketDisconnect:
            await dashboard_manager.remove_websocket_connection(websocket)


@dashboard_router.get("/api/data")
async def get_dashboard_data():
    """Get current dashboard data via REST API."""
    if dashboard_manager:
        return dashboard_manager.dashboard_data.dict()
    return {"error": "Dashboard manager not initialized"}


@dashboard_router.post("/api/refresh")
async def refresh_dashboard():
    """Trigger dashboard data refresh."""
    if dashboard_manager:
        await dashboard_manager.update_dashboard_data()
        return {"status": "success", "message": "Dashboard data refreshed"}
    return {"error": "Dashboard manager not initialized"}


def init_dashboard(settings: Settings, agent_registry: AgentRegistry):
    """Initialize the dashboard manager."""
    global dashboard_manager
    dashboard_manager = DashboardManager(settings, agent_registry)
    return dashboard_manager
