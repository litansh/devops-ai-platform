"""
Base agent class for DevOps AI Platform.

This module provides the foundation for all MCP (Model Context Protocol) agents
with common functionality and interfaces.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from core.logging import LoggerMixin
from core.config import Settings


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


class AgentType(Enum):
    """Agent type enumeration."""
    BURST_PREDICTOR = "burst_predictor"
    AUTO_SCALER_ADVISOR = "auto_scaler_advisor"
    BOTTLENECK_SCANNER = "bottleneck_scanner"
    COST_WATCHER = "cost_watcher"
    ANOMALY_DETECTOR = "anomaly_detector"
    SECURITY_RESPONDER = "security_responder"
    CAPACITY_PLANNER = "capacity_planner"
    LOAD_SHIFTER = "load_shifter"


@dataclass
class AgentContext:
    """Context information for agent execution."""
    infrastructure_data: Dict[str, Any]
    metrics_data: Dict[str, Any]
    cost_data: Dict[str, Any]
    security_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    execution_id: str
    timestamp: float


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    data: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    error_message: Optional[str] = None
    execution_time: float = 0.0


class BaseAgent(ABC, LoggerMixin):
    """
    Base class for all MCP agents.
    
    This class provides common functionality for agent lifecycle management,
    context handling, and result processing.
    """
    
    def __init__(self, agent_type: AgentType, settings: Settings):
        self.agent_type = agent_type
        self.settings = settings
        self.status = AgentStatus.IDLE
        self.last_execution = None
        self.execution_count = 0
        self.error_count = 0
        self.enabled = True
        
        # Performance tracking
        self.total_execution_time = 0.0
        self.avg_execution_time = 0.0
        
        self.logger.info(f"Initialized {self.agent_type.value} agent")
    
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.agent_type.value
    
    @property
    def description(self) -> str:
        """Get agent description."""
        return self._get_description()
    
    @abstractmethod
    def _get_description(self) -> str:
        """Get agent description - to be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentResult:
        """
        Analyze the current infrastructure state.
        
        Args:
            context: Agent execution context
            
        Returns:
            Analysis result
        """
        pass
    
    @abstractmethod
    async def optimize(self, context: AgentContext) -> AgentResult:
        """
        Generate optimization recommendations.
        
        Args:
            context: Agent execution context
            
        Returns:
            Optimization result
        """
        pass
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Execute the agent's main logic.
        
        Args:
            context: Agent execution context
            
        Returns:
            Execution result
        """
        if not self.enabled:
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message="Agent is disabled"
            )
        
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        self.execution_count += 1
        
        try:
            self.logger.info(f"Starting {self.name} execution")
            
            # Perform analysis
            analysis_result = await self.analyze(context)
            
            # Generate optimizations
            optimization_result = await self.optimize(context)
            
            # Combine results
            result = AgentResult(
                success=analysis_result.success and optimization_result.success,
                data={
                    "analysis": analysis_result.data,
                    "optimization": optimization_result.data
                },
                recommendations=analysis_result.recommendations + optimization_result.recommendations,
                actions=analysis_result.actions + optimization_result.actions,
                execution_time=time.time() - start_time
            )
            
            # Update performance metrics
            self._update_performance_metrics(result.execution_time)
            
            self.status = AgentStatus.IDLE
            self.last_execution = time.time()
            
            self.logger.info(f"Completed {self.name} execution in {result.execution_time:.2f}s")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.status = AgentStatus.ERROR
            self.logger.error(f"Error in {self.name} execution: {e}")
            
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _update_performance_metrics(self, execution_time: float) -> None:
        """Update agent performance metrics."""
        self.total_execution_time += execution_time
        self.avg_execution_time = self.total_execution_time / self.execution_count
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status."""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "status": self.status.value,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_execution": self.last_execution,
            "avg_execution_time": self.avg_execution_time,
            "success_rate": (self.execution_count - self.error_count) / max(self.execution_count, 1)
        }
    
    def enable(self) -> None:
        """Enable the agent."""
        self.enabled = True
        self.status = AgentStatus.IDLE
        self.logger.info(f"Enabled {self.name} agent")
    
    def disable(self) -> None:
        """Disable the agent."""
        self.enabled = False
        self.status = AgentStatus.DISABLED
        self.logger.info(f"Disabled {self.name} agent")
    
    def reset(self) -> None:
        """Reset agent statistics."""
        self.execution_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        self.avg_execution_time = 0.0
        self.last_execution = None
        self.logger.info(f"Reset {self.name} agent statistics")
    
    async def validate_context(self, context: AgentContext) -> bool:
        """
        Validate the execution context.
        
        Args:
            context: Agent execution context
            
        Returns:
            True if context is valid, False otherwise
        """
        required_fields = ["infrastructure_data", "metrics_data", "execution_id"]
        
        for field in required_fields:
            if not hasattr(context, field) or getattr(context, field) is None:
                self.logger.error(f"Missing required context field: {field}")
                return False
        
        return True
    
    def format_recommendation(self, recommendation: Dict[str, Any]) -> str:
        """
        Format a recommendation for display.
        
        Args:
            recommendation: Recommendation data
            
        Returns:
            Formatted recommendation string
        """
        title = recommendation.get("title", "Recommendation")
        description = recommendation.get("description", "")
        priority = recommendation.get("priority", "normal")
        impact = recommendation.get("impact", "unknown")
        
        return f"**{title}** ({priority.upper()})\n{description}\nImpact: {impact}"
    
    def format_action(self, action: Dict[str, Any]) -> str:
        """
        Format an action for display.
        
        Args:
            action: Action data
            
        Returns:
            Formatted action string
        """
        title = action.get("title", "Action")
        description = action.get("description", "")
        resource = action.get("resource", "unknown")
        change = action.get("change", "unknown")
        
        return f"**{title}**\n{description}\nResource: {resource}\nChange: {change}"
