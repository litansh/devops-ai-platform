"""
Tests for AI agents in DevOps AI Platform.

This module contains comprehensive tests for all MCP agents including
unit tests, integration tests, and performance tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from agents.base import AgentContext, AgentResult, AgentType
from agents.burst_predictor import BurstPredictorAgent
from agents.cost_watcher import CostWatcherAgent
from agents.anomaly_detector import AnomalyDetectorAgent
from core.config import Settings


class TestBurstPredictorAgent:
    """Test suite for BurstPredictor agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a BurstPredictor agent instance."""
        settings = Settings()
        return BurstPredictorAgent(settings)
    
    @pytest.fixture
    def context(self):
        """Create a test context."""
        return AgentContext(
            infrastructure_data={},
            metrics_data={
                "traffic": {
                    "time_series": [
                        {"timestamp": "2024-01-01T10:00:00Z", "value": 100},
                        {"timestamp": "2024-01-01T11:00:00Z", "value": 150},
                        {"timestamp": "2024-01-01T12:00:00Z", "value": 200},
                    ]
                }
            },
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "burst_predictor"
        assert agent.agent_type == AgentType.BURST_PREDICTOR
        assert agent.enabled is True
        assert agent.status.value == "idle"
    
    def test_agent_description(self, agent):
        """Test agent description."""
        description = agent.description
        assert "traffic" in description.lower()
        assert "predicts" in description.lower() or "prediction" in description.lower()
    
    @pytest.mark.asyncio
    async def test_analyze_with_valid_data(self, agent, context):
        """Test analysis with valid traffic data."""
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "analysis" in result.data
        assert "predictions" in result.data
    
    @pytest.mark.asyncio
    async def test_analyze_with_no_data(self, agent):
        """Test analysis with no traffic data."""
        context = AgentContext(
            infrastructure_data={},
            metrics_data={},
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
        
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "No traffic data available" in result.error_message
    
    @pytest.mark.asyncio
    async def test_optimize(self, agent, context):
        """Test optimization functionality."""
        result = await agent.optimize(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "scaling_analysis" in result.data
    
    @pytest.mark.asyncio
    async def test_execute_disabled_agent(self, agent, context):
        """Test executing a disabled agent."""
        agent.disable()
        result = await agent.execute(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "disabled" in result.error_message.lower()
    
    def test_agent_health_status(self, agent):
        """Test agent health status."""
        health = agent.get_health_status()
        
        assert "name" in health
        assert "status" in health
        assert "enabled" in health
        assert "execution_count" in health
        assert "error_count" in health
    
    def test_agent_enable_disable(self, agent):
        """Test agent enable/disable functionality."""
        # Test disable
        agent.disable()
        assert agent.enabled is False
        assert agent.status.value == "disabled"
        
        # Test enable
        agent.enable()
        assert agent.enabled is True
        assert agent.status.value == "idle"
    
    def test_agent_reset(self, agent):
        """Test agent reset functionality."""
        # Simulate some executions
        agent.execution_count = 5
        agent.error_count = 2
        agent.total_execution_time = 10.0
        
        agent.reset()
        
        assert agent.execution_count == 0
        assert agent.error_count == 0
        assert agent.total_execution_time == 0.0
        assert agent.last_execution is None


class TestCostWatcherAgent:
    """Test suite for CostWatcher agent."""
    
    @pytest.fixture
    def agent(self):
        """Create a CostWatcher agent instance."""
        settings = Settings()
        return CostWatcherAgent(settings)
    
    @pytest.fixture
    def context(self):
        """Create a test context with cost data."""
        return AgentContext(
            infrastructure_data={},
            metrics_data={},
            cost_data={
                "total_cost": 150.0,
                "daily_costs": [
                    {"date": "2024-01-01", "cost": 5.0},
                    {"date": "2024-01-02", "cost": 5.5},
                ],
                "service_costs": {
                    "AmazonEC2": 80.0,
                    "AmazonRDS": 40.0,
                    "AmazonS3": 30.0
                }
            },
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "cost_watcher"
        assert agent.agent_type == AgentType.COST_WATCHER
        assert agent.enabled is True
    
    @pytest.mark.asyncio
    async def test_analyze_with_cost_data(self, agent, context):
        """Test analysis with cost data."""
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "cost_analysis" in result.data
        assert "optimization_opportunities" in result.data
    
    @pytest.mark.asyncio
    async def test_analyze_with_no_cost_data(self, agent):
        """Test analysis with no cost data."""
        context = AgentContext(
            infrastructure_data={},
            metrics_data={},
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
        
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "No cost data available" in result.error_message
    
    @pytest.mark.asyncio
    @patch('agents.cost_watcher.boto3.client')
    async def test_fetch_aws_cost_data(self, mock_boto3, agent):
        """Test fetching AWS cost data."""
        # Mock AWS response
        mock_response = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2024-01-01', 'End': '2024-01-02'},
                    'Total': {'UnblendedCost': {'Amount': '5.0'}},
                    'Groups': [
                        {
                            'Keys': ['AmazonEC2', 'Usage'],
                            'Metrics': {'UnblendedCost': {'Amount': '3.0'}}
                        }
                    ]
                }
            ]
        }
        
        mock_ce_client = Mock()
        mock_ce_client.get_cost_and_usage.return_value = mock_response
        mock_boto3.return_value = mock_ce_client
        
        # Set AWS credentials
        agent.settings.aws_access_key_id = "test_key"
        agent.settings.aws_secret_access_key = "test_secret"
        
        cost_data = await agent._fetch_aws_cost_data()
        
        assert "total_cost" in cost_data
        assert "service_costs" in cost_data
        assert cost_data["total_cost"] > 0
    
    def test_cost_pattern_analysis(self, agent, context):
        """Test cost pattern analysis."""
        cost_data = context.cost_data
        analysis = agent._analyze_cost_patterns(cost_data)
        
        assert "total_cost" in analysis
        assert "avg_daily_cost" in analysis
        assert "top_services" in analysis
        assert "trend" in analysis
    
    def test_optimization_opportunities(self, agent, context):
        """Test optimization opportunities identification."""
        cost_data = context.cost_data
        opportunities = agent._identify_optimization_opportunities(cost_data)
        
        assert isinstance(opportunities, list)
        # Should find opportunities for EC2, RDS, and S3
        assert len(opportunities) > 0


class TestAnomalyDetectorAgent:
    """Test suite for AnomalyDetector agent."""
    
    @pytest.fixture
    def agent(self):
        """Create an AnomalyDetector agent instance."""
        settings = Settings()
        return AnomalyDetectorAgent(settings)
    
    @pytest.fixture
    def context(self):
        """Create a test context with metrics data."""
        return AgentContext(
            infrastructure_data={},
            metrics_data={
                "cpu_utilization": [
                    {"value": 50, "timestamp": "2024-01-01T10:00:00Z"},
                    {"value": 55, "timestamp": "2024-01-01T11:00:00Z"},
                    {"value": 95, "timestamp": "2024-01-01T12:00:00Z"},  # Anomaly
                    {"value": 52, "timestamp": "2024-01-01T13:00:00Z"},
                ],
                "memory_utilization": [
                    {"value": 60, "timestamp": "2024-01-01T10:00:00Z"},
                    {"value": 62, "timestamp": "2024-01-01T11:00:00Z"},
                    {"value": 65, "timestamp": "2024-01-01T12:00:00Z"},
                    {"value": 63, "timestamp": "2024-01-01T13:00:00Z"},
                ]
            },
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "anomaly_detector"
        assert agent.agent_type == AgentType.ANOMALY_DETECTOR
        assert agent.enabled is True
    
    @pytest.mark.asyncio
    async def test_analyze_with_metrics_data(self, agent, context):
        """Test analysis with metrics data."""
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert "anomalies" in result.data
        assert "metrics_analyzed" in result.data
    
    @pytest.mark.asyncio
    async def test_analyze_with_no_data(self, agent):
        """Test analysis with no metrics data."""
        context = AgentContext(
            infrastructure_data={},
            metrics_data={},
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test_execution",
            timestamp=datetime.now().timestamp()
        )
        
        result = await agent.analyze(context)
        
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert "No metrics data available" in result.error_message
    
    def test_anomaly_detection(self, agent, context):
        """Test anomaly detection logic."""
        metrics_data = context.metrics_data
        anomalies = agent._detect_anomalies(metrics_data)
        
        assert isinstance(anomalies, list)
        # Should detect the CPU anomaly (95% utilization)
        assert len(anomalies) > 0
        
        if anomalies:
            anomaly = anomalies[0]
            assert "metric" in anomaly
            assert "value" in anomaly
            assert "severity" in anomaly
            assert "z_score" in anomaly
    
    def test_anomaly_recommendations(self, agent, context):
        """Test anomaly recommendation generation."""
        metrics_data = context.metrics_data
        anomalies = agent._detect_anomalies(metrics_data)
        recommendations = agent._generate_anomaly_recommendations(anomalies)
        
        assert isinstance(recommendations, list)
        if anomalies:
            assert len(recommendations) > 0
    
    def test_agent_performance_tracking(self, agent):
        """Test agent performance tracking."""
        # Simulate execution
        agent.execution_count = 3
        agent.total_execution_time = 15.0
        
        assert agent.avg_execution_time == 5.0
        
        # Test performance update
        agent._update_performance_metrics(2.0)
        assert agent.execution_count == 4
        assert agent.avg_execution_time == 4.25  # (15 + 2) / 4


class TestAgentContextValidation:
    """Test suite for agent context validation."""
    
    def test_valid_context(self):
        """Test context validation with valid data."""
        context = AgentContext(
            infrastructure_data={"test": "data"},
            metrics_data={"test": "data"},
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test",
            timestamp=datetime.now().timestamp()
        )
        
        # This should not raise any exceptions
        assert context.execution_id == "test"
    
    def test_context_required_fields(self):
        """Test that context has all required fields."""
        context = AgentContext(
            infrastructure_data={},
            metrics_data={},
            cost_data={},
            security_data={},
            user_preferences={},
            execution_id="test",
            timestamp=datetime.now().timestamp()
        )
        
        required_fields = [
            "infrastructure_data", "metrics_data", "execution_id"
        ]
        
        for field in required_fields:
            assert hasattr(context, field)


class TestAgentResult:
    """Test suite for AgentResult."""
    
    def test_successful_result(self):
        """Test successful agent result."""
        result = AgentResult(
            success=True,
            data={"test": "data"},
            recommendations=[{"title": "Test"}],
            actions=[{"action": "test"}],
            execution_time=1.5
        )
        
        assert result.success is True
        assert "test" in result.data
        assert len(result.recommendations) == 1
        assert len(result.actions) == 1
        assert result.execution_time == 1.5
        assert result.error_message is None
    
    def test_failed_result(self):
        """Test failed agent result."""
        result = AgentResult(
            success=False,
            data={},
            recommendations=[],
            actions=[],
            error_message="Test error",
            execution_time=0.5
        )
        
        assert result.success is False
        assert result.error_message == "Test error"
        assert result.execution_time == 0.5


if __name__ == "__main__":
    pytest.main([__file__])
