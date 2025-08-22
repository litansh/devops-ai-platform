"""
Monitoring and metrics collection for DevOps AI Platform.

This module provides Prometheus metrics, health checks, and monitoring
capabilities for the platform.
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, generate_latest,
    CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
)
from prometheus_client.exposition import start_http_server

from core.logging import get_logger
from core.config import Settings

logger = get_logger(__name__)

# Create a custom registry for multiprocess support
registry = CollectorRegistry()

# Metrics definitions
AGENT_EXECUTION_COUNTER = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_name', 'status'],
    registry=registry
)

AGENT_EXECUTION_DURATION = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_name'],
    registry=registry
)

BOT_INTERACTION_COUNTER = Counter(
    'bot_interactions_total',
    'Total number of bot interactions',
    ['bot_type', 'command'],
    registry=registry
)

INFRASTRUCTURE_CHANGES_COUNTER = Counter(
    'infrastructure_changes_total',
    'Total number of infrastructure changes',
    ['change_type', 'status'],
    registry=registry
)

ACTIVE_AGENTS_GAUGE = Gauge(
    'active_agents',
    'Number of currently active agents',
    registry=registry
)

PLATFORM_HEALTH_GAUGE = Gauge(
    'platform_health',
    'Platform health status (1=healthy, 0=unhealthy)',
    registry=registry
)

COST_MONITORING_GAUGE = Gauge(
    'cost_monitoring_dollars',
    'Current cost in dollars',
    ['cloud_provider', 'service'],
    registry=registry
)

PERFORMANCE_METRICS = Summary(
    'performance_metrics',
    'Performance metrics for various operations',
    ['operation_type'],
    registry=registry
)


class MetricsCollector:
    """Collector for platform metrics."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.start_time = time.time()
    
    def record_agent_execution(self, agent_name: str, status: str, duration: float) -> None:
        """Record agent execution metrics."""
        AGENT_EXECUTION_COUNTER.labels(agent_name=agent_name, status=status).inc()
        AGENT_EXECUTION_DURATION.labels(agent_name=agent_name).observe(duration)
    
    def record_bot_interaction(self, bot_type: str, command: str) -> None:
        """Record bot interaction metrics."""
        BOT_INTERACTION_COUNTER.labels(bot_type=bot_type, command=command).inc()
    
    def record_infrastructure_change(self, change_type: str, status: str) -> None:
        """Record infrastructure change metrics."""
        INFRASTRUCTURE_CHANGES_COUNTER.labels(change_type=change_type, status=status).inc()
    
    def set_active_agents(self, count: int) -> None:
        """Set the number of active agents."""
        ACTIVE_AGENTS_GAUGE.set(count)
    
    def set_platform_health(self, healthy: bool) -> None:
        """Set platform health status."""
        PLATFORM_HEALTH_GAUGE.set(1 if healthy else 0)
    
    def record_cost(self, cloud_provider: str, service: str, cost: float) -> None:
        """Record cost metrics."""
        COST_MONITORING_GAUGE.labels(cloud_provider=cloud_provider, service=service).set(cost)
    
    @contextmanager
    def measure_performance(self, operation_type: str):
        """Context manager for measuring operation performance."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            PERFORMANCE_METRICS.labels(operation_type=operation_type).observe(duration)


def setup_monitoring(settings: Settings) -> MetricsCollector:
    """
    Setup monitoring and metrics collection.
    
    Args:
        settings: Application settings
        
    Returns:
        MetricsCollector instance
    """
    try:
        # Start Prometheus metrics server
        start_http_server(9091, registry=registry)
        logger.info("✅ Prometheus metrics server started on port 9091")
        
        # Create metrics collector
        collector = MetricsCollector(settings)
        
        # Set initial platform health
        collector.set_platform_health(True)
        
        logger.info("✅ Monitoring setup complete")
        return collector
        
    except Exception as e:
        logger.error(f"❌ Monitoring setup failed: {e}")
        raise


def get_metrics() -> str:
    """Get Prometheus metrics in text format."""
    return generate_latest(registry)


class HealthChecker:
    """Health checker for platform components."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            from core.database import get_redis_client, get_mongodb_client
            
            # Check Redis
            redis_client = get_redis_client()
            await redis_client.ping()
            
            # Check MongoDB
            mongo_client = get_mongodb_client()
            await mongo_client.admin.command('ping')
            
            return {
                "status": "healthy",
                "components": {
                    "redis": "healthy",
                    "mongodb": "healthy"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "redis": "unhealthy",
                    "mongodb": "unhealthy"
                }
            }
    
    async def check_cloud_health(self) -> Dict[str, Any]:
        """Check cloud provider health."""
        try:
            import boto3
            
            # Check AWS
            if self.settings.aws_access_key_id:
                ec2 = boto3.client('ec2', region_name=self.settings.aws_region)
                ec2.describe_regions()
                aws_status = "healthy"
            else:
                aws_status = "not_configured"
            
            return {
                "status": "healthy" if aws_status == "healthy" else "degraded",
                "components": {
                    "aws": aws_status,
                    "gcp": "not_configured"  # Future implementation
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "components": {
                    "aws": "unhealthy",
                    "gcp": "not_configured"
                }
            }
    
    async def check_agent_health(self, agent_registry) -> Dict[str, Any]:
        """Check agent health."""
        try:
            agents = agent_registry.list_agents()
            healthy_agents = sum(1 for agent in agents if agent.get("status") == "healthy")
            
            return {
                "status": "healthy" if healthy_agents == len(agents) else "degraded",
                "total_agents": len(agents),
                "healthy_agents": healthy_agents,
                "agents": agents
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "total_agents": 0,
                "healthy_agents": 0
            }
    
    async def get_overall_health(self, agent_registry=None) -> Dict[str, Any]:
        """Get overall platform health."""
        db_health = await self.check_database_health()
        cloud_health = await self.check_cloud_health()
        agent_health = await self.check_agent_health(agent_registry) if agent_registry else {"status": "unknown"}
        
        # Determine overall status
        statuses = [db_health["status"], cloud_health["status"], agent_health["status"]]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "components": {
                "database": db_health,
                "cloud": cloud_health,
                "agents": agent_health
            }
        }
