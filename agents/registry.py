"""
Agent registry for DevOps AI Platform.

This module manages the registration, discovery, and execution of all MCP agents
in the platform.
"""

import asyncio
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

from core.logging import LoggerMixin
from core.config import Settings
from agents.base import BaseAgent, AgentType, AgentContext, AgentResult

# Import all agent implementations
from agents.burst_predictor import BurstPredictorAgent
from agents.cost_watcher import CostWatcherAgent
from agents.anomaly_detector import AnomalyDetectorAgent
from agents.auto_scaler_advisor import AutoScalerAdvisorAgent
from agents.bottleneck_scanner import BottleneckScannerAgent
from agents.security_responder import SecurityResponderAgent
from agents.capacity_planner import CapacityPlannerAgent
from agents.load_shifter import LoadShifterAgent


class AgentRegistry(LoggerMixin):
    """
    Registry for managing all MCP agents.
    
    This class handles agent registration, discovery, execution, and lifecycle
    management.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[AgentType, Type[BaseAgent]] = {
            AgentType.BURST_PREDICTOR: BurstPredictorAgent,
            AgentType.COST_WATCHER: CostWatcherAgent,
            AgentType.ANOMALY_DETECTOR: AnomalyDetectorAgent,
            AgentType.AUTO_SCALER_ADVISOR: AutoScalerAdvisorAgent,
            AgentType.BOTTLENECK_SCANNER: BottleneckScannerAgent,
            AgentType.SECURITY_RESPONDER: SecurityResponderAgent,
            AgentType.CAPACITY_PLANNER: CapacityPlannerAgent,
            AgentType.LOAD_SHIFTER: LoadShifterAgent,
        }
        
        self._initialize_agents()
        self.logger.info(f"AgentRegistry initialized with {len(self.agents)} agents")
    
    def _initialize_agents(self) -> None:
        """Initialize all registered agents."""
        for agent_type, agent_class in self.agent_classes.items():
            try:
                agent = agent_class(self.settings)
                self.agents[agent.name] = agent
                self.logger.info(f"Initialized agent: {agent.name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_type.value}: {e}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents with their status.
        
        Returns:
            List of agent information dictionaries
        """
        return [
            {
                "name": agent.name,
                "type": agent.agent_type.value,
                "description": agent.description,
                "status": agent.status.value,
                "enabled": agent.enabled,
                "health": agent.get_health_status()
            }
            for agent in self.agents.values()
        ]
    
    def list_enabled_agents(self) -> List[BaseAgent]:
        """
        Get list of enabled agents.
        
        Returns:
            List of enabled agent instances
        """
        return [agent for agent in self.agents.values() if agent.enabled]
    
    async def execute_agent(
        self,
        agent_name: str,
        context_data: Dict[str, Any]
    ) -> AgentResult:
        """
        Execute a specific agent.
        
        Args:
            agent_name: Name of the agent to execute
            context_data: Context data for the agent
            
        Returns:
            Agent execution result
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Agent '{agent_name}' not found"
            )
        
        if not agent.enabled:
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Agent '{agent_name}' is disabled"
            )
        
        # Create agent context
        context = AgentContext(
            infrastructure_data=context_data.get("infrastructure", {}),
            metrics_data=context_data.get("metrics", {}),
            cost_data=context_data.get("cost", {}),
            security_data=context_data.get("security", {}),
            user_preferences=context_data.get("preferences", {}),
            execution_id=f"{agent_name}_{int(datetime.utcnow().timestamp())}",
            timestamp=datetime.utcnow().timestamp()
        )
        
        # Validate context
        if not await agent.validate_context(context):
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message="Invalid context data"
            )
        
        # Execute agent with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute(context),
                timeout=self.settings.agent_timeout
            )
            return result
        except asyncio.TimeoutError:
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Agent execution timed out after {self.settings.agent_timeout}s"
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Agent execution failed: {str(e)}"
            )
    
    async def execute_all_agents(self, context_data: Dict[str, Any]) -> Dict[str, AgentResult]:
        """
        Execute all enabled agents.
        
        Args:
            context_data: Context data for all agents
            
        Returns:
            Dictionary mapping agent names to their results
        """
        enabled_agents = self.list_enabled_agents()
        results = {}
        
        # Execute agents concurrently with semaphore for limiting concurrency
        semaphore = asyncio.Semaphore(self.settings.max_concurrent_agents)
        
        async def execute_single_agent(agent: BaseAgent) -> tuple[str, AgentResult]:
            async with semaphore:
                result = await self.execute_agent(agent.name, context_data)
                return agent.name, result
        
        # Execute all agents concurrently
        tasks = [execute_single_agent(agent) for agent in enabled_agents]
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for agent_name, result in agent_results:
            if isinstance(result, Exception):
                results[agent_name] = AgentResult(
                    success=False,
                    data={},
                    recommendations=[],
                    actions=[],
                    error_message=f"Agent execution failed: {str(result)}"
                )
            else:
                results[agent_name] = result
        
        return results
    
    def enable_agent(self, agent_name: str) -> bool:
        """
        Enable an agent.
        
        Args:
            agent_name: Name of the agent to enable
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_name)
        if agent:
            agent.enable()
            self.logger.info(f"Enabled agent: {agent_name}")
            return True
        else:
            self.logger.error(f"Agent not found: {agent_name}")
            return False
    
    def disable_agent(self, agent_name: str) -> bool:
        """
        Disable an agent.
        
        Args:
            agent_name: Name of the agent to disable
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_name)
        if agent:
            agent.disable()
            self.logger.info(f"Disabled agent: {agent_name}")
            return True
        else:
            self.logger.error(f"Agent not found: {agent_name}")
            return False
    
    def reset_agent(self, agent_name: str) -> bool:
        """
        Reset an agent's statistics.
        
        Args:
            agent_name: Name of the agent to reset
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.get_agent(agent_name)
        if agent:
            agent.reset()
            self.logger.info(f"Reset agent: {agent_name}")
            return True
        else:
            self.logger.error(f"Agent not found: {agent_name}")
            return False
    
    def get_agent_health(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get health status of an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Health status dictionary or None if agent not found
        """
        agent = self.get_agent(agent_name)
        if agent:
            return agent.get_health_status()
        return None
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall health status of all agents.
        
        Returns:
            Overall health status
        """
        agents = list(self.agents.values())
        enabled_agents = [agent for agent in agents if agent.enabled]
        healthy_agents = [agent for agent in enabled_agents if agent.status.value != "error"]
        
        return {
            "total_agents": len(agents),
            "enabled_agents": len(enabled_agents),
            "healthy_agents": len(healthy_agents),
            "agent_health": {
                agent.name: agent.get_health_status()
                for agent in agents
            }
        }
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register a new agent.
        
        Args:
            agent: Agent instance to register
            
        Returns:
            True if successful, False otherwise
        """
        if agent.name in self.agents:
            self.logger.error(f"Agent '{agent.name}' already registered")
            return False
        
        self.agents[agent.name] = agent
        self.logger.info(f"Registered new agent: {agent.name}")
        return True
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_name: Name of the agent to unregister
            
        Returns:
            True if successful, False otherwise
        """
        if agent_name not in self.agents:
            self.logger.error(f"Agent '{agent_name}' not found")
            return False
        
        del self.agents[agent_name]
        self.logger.info(f"Unregistered agent: {agent_name}")
        return True
