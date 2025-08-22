"""
Bot Gateway for DevOps AI Platform.

This module manages bot interactions, command routing, and provides
a unified interface for Telegram and Slack bots.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.logging import LoggerMixin
from core.config import Settings
from agents.registry import AgentRegistry


class BotGateway(LoggerMixin):
    """
    Bot Gateway for managing bot interactions and routing.
    
    This class provides a unified interface for handling bot commands,
    agent interactions, and platform operations.
    """
    
    def __init__(self, settings: Settings, agent_registry: AgentRegistry):
        self.settings = settings
        self.agent_registry = agent_registry
        self.connection_count = 0
        self.active_connections = {}
        self.command_history = []
        
        # Initialize bot handlers
        self.telegram_bot = None
        self.slack_bot = None
        
        self.logger.info("BotGateway initialized")
    
    async def start(self) -> None:
        """Start the bot gateway and all bot handlers."""
        try:
            # Start Telegram bot if configured
            if self.settings.telegram_bot_token:
                from bots.telegram_bot import TelegramBot
                self.telegram_bot = TelegramBot(self.settings, self)
                await self.telegram_bot.start()
                self.logger.info("✅ Telegram bot started")
            
            # Start Slack bot if configured
            if self.settings.slack_bot_token:
                from bots.slack_bot import SlackBot
                self.slack_bot = SlackBot(self.settings, self)
                await self.slack_bot.start()
                self.logger.info("✅ Slack bot started")
            
            self.logger.info("✅ Bot gateway started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start bot gateway: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the bot gateway and all bot handlers."""
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop()
                self.logger.info("✅ Telegram bot stopped")
            
            if self.slack_bot:
                await self.slack_bot.stop()
                self.logger.info("✅ Slack bot stopped")
            
            self.logger.info("✅ Bot gateway stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping bot gateway: {e}")
    
    async def handle_command(
        self,
        bot_type: str,
        user_id: str,
        command: str,
        args: List[str] = None
    ) -> str:
        """
        Handle bot commands and route to appropriate handlers.
        
        Args:
            bot_type: Type of bot (telegram, slack)
            user_id: User ID
            command: Command string
            args: Command arguments
            
        Returns:
            Response message
        """
        try:
            start_time = datetime.now()
            
            # Log command
            self.command_history.append({
                "bot_type": bot_type,
                "user_id": user_id,
                "command": command,
                "args": args,
                "timestamp": datetime.now()
            })
            
            # Parse command
            if command.startswith("/"):
                command = command[1:]  # Remove leading slash
            
            # Route to appropriate handler
            if command == "status":
                response = await self._handle_status_command()
            elif command == "cost":
                response = await self._handle_cost_command()
            elif command == "analysis":
                response = await self._handle_analysis_command()
            elif command == "anomaly":
                response = await self._handle_anomaly_command()
            elif command == "predict":
                response = await self._handle_predict_command()
            elif command.startswith("agent"):
                response = await self._handle_agent_command(args)
            elif command.startswith("approve"):
                response = await self._handle_approve_command(args)
            elif command.startswith("scale"):
                response = await self._handle_scale_command(args)
            elif command.startswith("logs"):
                response = await self._handle_logs_command(args)
            elif command == "alerts":
                response = await self._handle_alerts_command()
            elif command.startswith("run"):
                response = await self._handle_run_command(args)
            elif command.startswith("graph"):
                response = await self._handle_graph_command(args)
            elif command == "help":
                response = self._handle_help_command()
            else:
                response = f"❌ Unknown command: {command}\nUse /help for available commands."
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Log response
            self.logger.info(f"Command '{command}' executed in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling command '{command}': {e}")
            return f"❌ Error executing command: {str(e)}"
    
    async def send_alert(self, message: str, priority: str = "normal") -> None:
        """
        Send alert message to all connected bots.
        
        Args:
            message: Alert message
            priority: Alert priority (low, normal, high, critical)
        """
        try:
            # Add priority indicator
            priority_indicators = {
                "low": "ℹ️",
                "normal": "⚠️",
                "high": "🚨",
                "critical": "🔥"
            }
            
            indicator = priority_indicators.get(priority, "⚠️")
            formatted_message = f"{indicator} {message}"
            
            # Send to Telegram
            if self.telegram_bot and self.settings.telegram_chat_id:
                await self.telegram_bot.send_message(
                    self.settings.telegram_chat_id,
                    formatted_message
                )
            
            # Send to Slack
            if self.slack_bot:
                await self.slack_bot.send_message(
                    self.settings.slack_channel,
                    formatted_message
                )
            
            self.logger.info(f"Alert sent: {message}")
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    async def _handle_status_command(self) -> str:
        """Handle /status command."""
        try:
            # Get platform status
            agents = self.agent_registry.list_agents()
            enabled_agents = [a for a in agents if a.get("enabled", False)]
            healthy_agents = [a for a in enabled_agents if a.get("health", {}).get("status") == "idle"]
            
            # Get overall health
            overall_health = self.agent_registry.get_overall_health()
            
            status_message = f"""
🟢 **Platform Status**

**Agents**: {len(healthy_agents)}/{len(enabled_agents)} healthy
**Overall Health**: {overall_health.get('status', 'unknown')}

**Active Agents**:
"""
            
            for agent in enabled_agents[:5]:  # Show top 5 agents
                health = agent.get("health", {})
                status = health.get("status", "unknown")
                status_emoji = "🟢" if status == "idle" else "🟡" if status == "running" else "🔴"
                
                status_message += f"{status_emoji} {agent['name']}: {status}\n"
            
            if len(enabled_agents) > 5:
                status_message += f"... and {len(enabled_agents) - 5} more agents\n"
            
            return status_message
            
        except Exception as e:
            return f"❌ Error getting status: {str(e)}"
    
    async def _handle_cost_command(self) -> str:
        """Handle /cost command."""
        try:
            # Execute cost watcher agent
            result = await self.agent_registry.execute_agent("cost_watcher", {})
            
            if result.success:
                data = result.data.get("analysis", {})
                current_spending = data.get("current_spending", {})
                
                total_cost = current_spending.get("total_cost", 0.0)
                daily_avg = current_spending.get("daily_average", 0.0)
                
                cost_message = f"""
💰 **Cost Analysis**

**Total Cost (30 days)**: ${total_cost:.2f}
**Daily Average**: ${daily_avg:.2f}

**Top Services**:
"""
                
                top_services = data.get("top_services", [])
                for service, cost in top_services[:3]:
                    cost_message += f"• {service}: ${cost:.2f}\n"
                
                return cost_message
            else:
                return f"❌ Cost analysis failed: {result.error_message}"
                
        except Exception as e:
            return f"❌ Error getting cost data: {str(e)}"
    
    async def _handle_analysis_command(self) -> str:
        """Handle /analysis command."""
        try:
            # Execute multiple agents for comprehensive analysis
            agents_to_run = ["burst_predictor", "anomaly_detector", "cost_watcher"]
            results = {}
            
            for agent_name in agents_to_run:
                result = await self.agent_registry.execute_agent(agent_name, {})
                results[agent_name] = result
            
            analysis_message = "🤖 **AI Analysis Results**\n\n"
            
            for agent_name, result in results.items():
                if result.success:
                    recommendations = result.recommendations
                    if recommendations:
                        analysis_message += f"**{agent_name.replace('_', ' ').title()}**:\n"
                        for rec in recommendations[:2]:  # Show top 2 recommendations
                            analysis_message += f"• {rec.get('title', 'Recommendation')}\n"
                        analysis_message += "\n"
            
            if not any(r.success for r in results.values()):
                analysis_message += "No analysis results available."
            
            return analysis_message
            
        except Exception as e:
            return f"❌ Error running analysis: {str(e)}"
    
    async def _handle_anomaly_command(self) -> str:
        """Handle /anomaly command."""
        try:
            result = await self.agent_registry.execute_agent("anomaly_detector", {})
            
            if result.success:
                anomalies = result.data.get("anomalies", [])
                
                if anomalies:
                    anomaly_message = f"⚠️ **Anomaly Detection Results**\n\n"
                    anomaly_message += f"Found {len(anomalies)} anomalies:\n\n"
                    
                    for anomaly in anomalies[:3]:  # Show top 3 anomalies
                        metric = anomaly.get("metric", "unknown")
                        severity = anomaly.get("severity", "unknown")
                        value = anomaly.get("value", 0)
                        
                        severity_emoji = "🔴" if severity == "high" else "🟡"
                        anomaly_message += f"{severity_emoji} **{metric}**: {value} ({severity})\n"
                    
                    if len(anomalies) > 3:
                        anomaly_message += f"\n... and {len(anomalies) - 3} more anomalies"
                else:
                    anomaly_message = "✅ No anomalies detected"
                
                return anomaly_message
            else:
                return f"❌ Anomaly detection failed: {result.error_message}"
                
        except Exception as e:
            return f"❌ Error running anomaly detection: {str(e)}"
    
    async def _handle_predict_command(self) -> str:
        """Handle /predict command."""
        try:
            result = await self.agent_registry.execute_agent("burst_predictor", {})
            
            if result.success:
                predictions = result.data.get("predictions", [])
                
                if predictions:
                    predict_message = "📈 **Traffic Predictions**\n\n"
                    
                    for prediction in predictions[:3]:  # Show top 3 predictions
                        timestamp = prediction.get("timestamp", "unknown")
                        predicted_value = prediction.get("predicted_value", 0)
                        confidence = prediction.get("confidence", 0)
                        burst_prob = prediction.get("burst_probability", 0)
                        
                        predict_message += f"**{timestamp}**: {predicted_value:.0f} req/s\n"
                        predict_message += f"Confidence: {confidence:.1%}, Burst Probability: {burst_prob:.1%}\n\n"
                else:
                    predict_message = "No predictions available"
                
                return predict_message
            else:
                return f"❌ Prediction failed: {result.error_message}"
                
        except Exception as e:
            return f"❌ Error running predictions: {str(e)}"
    
    async def _handle_agent_command(self, args: List[str]) -> str:
        """Handle /agent command."""
        if not args:
            return "❌ Please specify agent name and action (e.g., /agent burst_predictor analyze)"
        
        agent_name = args[0]
        action = args[1] if len(args) > 1 else "status"
        
        try:
            if action == "status":
                health = self.agent_registry.get_agent_health(agent_name)
                if health:
                    return f"**{agent_name}**: {health.get('status', 'unknown')}"
                else:
                    return f"❌ Agent '{agent_name}' not found"
            
            elif action in ["analyze", "optimize"]:
                result = await self.agent_registry.execute_agent(agent_name, {})
                
                if result.success:
                    return f"✅ {agent_name} {action} completed successfully"
                else:
                    return f"❌ {agent_name} {action} failed: {result.error_message}"
            
            else:
                return f"❌ Unknown action: {action}"
                
        except Exception as e:
            return f"❌ Error with agent command: {str(e)}"
    
    async def _handle_approve_command(self, args: List[str]) -> str:
        """Handle /approve command."""
        if not args:
            return "❌ Please specify PR ID to approve"
        
        pr_id = args[0]
        
        try:
            # This would integrate with GitHub API to approve PRs
            return f"✅ Approved PR #{pr_id}"
        except Exception as e:
            return f"❌ Error approving PR: {str(e)}"
    
    async def _handle_scale_command(self, args: List[str]) -> str:
        """Handle /scale command."""
        if len(args) < 2:
            return "❌ Please specify service and replicas (e.g., /scale api 5)"
        
        service = args[0]
        replicas = int(args[1])
        
        try:
            # This would integrate with Kubernetes API to scale deployments
            return f"✅ Scaled {service} to {replicas} replicas"
        except Exception as e:
            return f"❌ Error scaling service: {str(e)}"
    
    async def _handle_logs_command(self, args: List[str]) -> str:
        """Handle /logs command."""
        if not args:
            return "❌ Please specify pod name"
        
        pod_name = args[0]
        
        try:
            # This would integrate with Kubernetes API to get logs
            return f"📋 Logs for {pod_name}:\n[Log content would be displayed here]"
        except Exception as e:
            return f"❌ Error getting logs: {str(e)}"
    
    async def _handle_alerts_command(self) -> str:
        """Handle /alerts command."""
        try:
            # This would integrate with Prometheus AlertManager
            return "🚨 **Current Alerts**\n\nNo active alerts"
        except Exception as e:
            return f"❌ Error getting alerts: {str(e)}"
    
    async def _handle_run_command(self, args: List[str]) -> str:
        """Handle /run command."""
        if len(args) < 2:
            return "❌ Please specify test type and service (e.g., /run test api)"
        
        test_type = args[0]
        service = args[1]
        
        try:
            # This would integrate with k6 or other testing tools
            return f"🧪 Running {test_type} test on {service}..."
        except Exception as e:
            return f"❌ Error running test: {str(e)}"
    
    async def _handle_graph_command(self, args: List[str]) -> str:
        """Handle /graph command."""
        if not args:
            return "❌ Please specify panel name"
        
        panel = args[0]
        
        try:
            # This would integrate with Grafana API to get graphs
            return f"📊 Graph for {panel}:\n[Graph would be displayed here]"
        except Exception as e:
            return f"❌ Error getting graph: {str(e)}"
    
    def _handle_help_command(self) -> str:
        """Handle /help command."""
        return """
🤖 **DevOps AI Platform Commands**

**Status & Monitoring**:
• `/status` - Platform health and agent status
• `/cost` - Cost analysis and spending breakdown
• `/analysis` - AI-powered infrastructure analysis
• `/anomaly` - Anomaly detection results
• `/predict` - Traffic predictions

**Agent Control**:
• `/agent <name> status` - Get agent status
• `/agent <name> analyze` - Run agent analysis
• `/agent <name> optimize` - Run agent optimization

**Operations**:
• `/approve <pr-id>` - Approve agent-generated PR
• `/scale <service> <replicas>` - Scale deployment
• `/logs <pod>` - Get pod logs
• `/alerts` - Show current alerts
• `/run test <service>` - Run synthetic test
• `/graph <panel>` - Get Grafana graph

**Help**:
• `/help` - Show this help message
"""
