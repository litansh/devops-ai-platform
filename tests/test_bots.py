"""
Tests for bot components in DevOps AI Platform.

This module contains comprehensive tests for the bot gateway,
Telegram bot, and Slack bot implementations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from bots.gateway import BotGateway
from bots.telegram_bot import TelegramBot
from bots.slack_bot import SlackBot
from core.config import Settings
from agents.registry import AgentRegistry


class TestBotGateway:
    """Test suite for BotGateway."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    def agent_registry(self, settings):
        """Create a mock agent registry."""
        registry = Mock(spec=AgentRegistry)
        registry.list_agents.return_value = [
            {
                "name": "burst_predictor",
                "enabled": True,
                "health": {"status": "idle"}
            },
            {
                "name": "cost_watcher",
                "enabled": True,
                "health": {"status": "idle"}
            }
        ]
        registry.get_overall_health.return_value = {
            "status": "healthy",
            "total_agents": 2,
            "enabled_agents": 2,
            "healthy_agents": 2
        }
        return registry
    
    @pytest.fixture
    def gateway(self, settings, agent_registry):
        """Create a BotGateway instance."""
        return BotGateway(settings, agent_registry)
    
    def test_gateway_initialization(self, gateway):
        """Test gateway initialization."""
        assert gateway.settings is not None
        assert gateway.agent_registry is not None
        assert gateway.connection_count == 0
        assert len(gateway.command_history) == 0
    
    @pytest.mark.asyncio
    async def test_start_gateway(self, gateway):
        """Test starting the bot gateway."""
        with patch('bots.telegram_bot.TelegramBot') as mock_telegram, \
             patch('bots.slack_bot.SlackBot') as mock_slack:
            
            # Mock bot instances
            mock_telegram_instance = AsyncMock()
            mock_slack_instance = AsyncMock()
            mock_telegram.return_value = mock_telegram_instance
            mock_slack.return_value = mock_slack_instance
            
            # Set bot tokens
            gateway.settings.telegram_bot_token = "test_telegram_token"
            gateway.settings.slack_bot_token = "test_slack_token"
            
            await gateway.start()
            
            # Verify bots were started
            mock_telegram_instance.start.assert_called_once()
            mock_slack_instance.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_gateway(self, gateway):
        """Test stopping the bot gateway."""
        with patch('bots.telegram_bot.TelegramBot') as mock_telegram, \
             patch('bots.slack_bot.SlackBot') as mock_slack:
            
            # Mock bot instances
            mock_telegram_instance = AsyncMock()
            mock_slack_instance = AsyncMock()
            mock_telegram.return_value = mock_telegram_instance
            mock_slack.return_value = mock_slack_instance
            
            # Set bot tokens and start
            gateway.settings.telegram_bot_token = "test_telegram_token"
            gateway.settings.slack_bot_token = "test_slack_token"
            await gateway.start()
            
            # Stop gateway
            await gateway.stop()
            
            # Verify bots were stopped
            mock_telegram_instance.stop.assert_called_once()
            mock_slack_instance.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_status_command(self, gateway):
        """Test handling /status command."""
        response = await gateway._handle_status_command()
        
        assert "Platform Status" in response
        assert "Agents" in response
        assert "Overall Health" in response
    
    @pytest.mark.asyncio
    async def test_handle_cost_command(self, gateway):
        """Test handling /cost command."""
        # Mock agent execution
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            "analysis": {
                "current_spending": {
                    "total_cost": 150.0,
                    "daily_average": 5.0
                },
                "top_services": [("AmazonEC2", 80.0), ("AmazonRDS", 40.0)]
            }
        }
        
        gateway.agent_registry.execute_agent = AsyncMock(return_value=mock_result)
        
        response = await gateway._handle_cost_command()
        
        assert "Cost Analysis" in response
        assert "$150.00" in response
        assert "AmazonEC2" in response
    
    @pytest.mark.asyncio
    async def test_handle_analysis_command(self, gateway):
        """Test handling /analysis command."""
        # Mock agent executions
        mock_result = Mock()
        mock_result.success = True
        mock_result.recommendations = [{"title": "Test Recommendation"}]
        
        gateway.agent_registry.execute_agent = AsyncMock(return_value=mock_result)
        
        response = await gateway._handle_analysis_command()
        
        assert "AI Analysis Results" in response
        assert "Test Recommendation" in response
    
    @pytest.mark.asyncio
    async def test_handle_anomaly_command(self, gateway):
        """Test handling /anomaly command."""
        # Mock agent execution
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            "anomalies": [
                {
                    "metric": "cpu_utilization",
                    "value": 95,
                    "severity": "high"
                }
            ]
        }
        
        gateway.agent_registry.execute_agent = AsyncMock(return_value=mock_result)
        
        response = await gateway._handle_anomaly_command()
        
        assert "Anomaly Detection Results" in response
        assert "cpu_utilization" in response
        assert "high" in response
    
    @pytest.mark.asyncio
    async def test_handle_predict_command(self, gateway):
        """Test handling /predict command."""
        # Mock agent execution
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            "predictions": [
                {
                    "timestamp": "2024-01-01T13:00:00Z",
                    "predicted_value": 250,
                    "confidence": 0.8,
                    "burst_probability": 0.6
                }
            ]
        }
        
        gateway.agent_registry.execute_agent = AsyncMock(return_value=mock_result)
        
        response = await gateway._handle_predict_command()
        
        assert "Traffic Predictions" in response
        assert "250" in response
        assert "80%" in response
    
    @pytest.mark.asyncio
    async def test_handle_agent_command(self, gateway):
        """Test handling /agent command."""
        # Test agent status
        mock_health = {
            "name": "burst_predictor",
            "status": "idle",
            "enabled": True
        }
        gateway.agent_registry.get_agent_health = Mock(return_value=mock_health)
        
        response = await gateway._handle_agent_command(["burst_predictor", "status"])
        assert "burst_predictor" in response
        assert "idle" in response
        
        # Test agent not found
        gateway.agent_registry.get_agent_health = Mock(return_value=None)
        response = await gateway._handle_agent_command(["unknown_agent", "status"])
        assert "not found" in response
    
    @pytest.mark.asyncio
    async def test_handle_scale_command(self, gateway):
        """Test handling /scale command."""
        response = await gateway._handle_scale_command(["api", "5"])
        assert "Scaled api to 5 replicas" in response
        
        # Test invalid arguments
        response = await gateway._handle_scale_command(["api"])
        assert "Please specify service and replicas" in response
    
    @pytest.mark.asyncio
    async def test_handle_logs_command(self, gateway):
        """Test handling /logs command."""
        response = await gateway._handle_logs_command(["api-pod-123"])
        assert "Logs for api-pod-123" in response
        
        # Test missing pod name
        response = await gateway._handle_logs_command([])
        assert "Please specify pod name" in response
    
    @pytest.mark.asyncio
    async def test_handle_alerts_command(self, gateway):
        """Test handling /alerts command."""
        response = await gateway._handle_alerts_command()
        assert "Current Alerts" in response
    
    @pytest.mark.asyncio
    async def test_handle_run_command(self, gateway):
        """Test handling /run command."""
        response = await gateway._handle_run_command(["test", "api"])
        assert "Running test test on api" in response
        
        # Test invalid arguments
        response = await gateway._handle_run_command(["test"])
        assert "Please specify test type and service" in response
    
    @pytest.mark.asyncio
    async def test_handle_graph_command(self, gateway):
        """Test handling /graph command."""
        response = await gateway._handle_graph_command(["cpu_usage"])
        assert "Graph for cpu_usage" in response
        
        # Test missing panel name
        response = await gateway._handle_graph_command([])
        assert "Please specify panel name" in response
    
    def test_handle_help_command(self, gateway):
        """Test handling /help command."""
        response = gateway._handle_help_command()
        
        assert "DevOps AI Platform Commands" in response
        assert "/status" in response
        assert "/cost" in response
        assert "/analysis" in response
        assert "/help" in response
    
    @pytest.mark.asyncio
    async def test_handle_command_routing(self, gateway):
        """Test command routing to appropriate handlers."""
        # Test status command
        response = await gateway.handle_command("telegram", "user123", "/status")
        assert "Platform Status" in response
        
        # Test unknown command
        response = await gateway.handle_command("telegram", "user123", "/unknown")
        assert "Unknown command" in response
        assert "/help" in response
    
    @pytest.mark.asyncio
    async def test_send_alert(self, gateway):
        """Test sending alerts."""
        with patch('bots.telegram_bot.TelegramBot') as mock_telegram, \
             patch('bots.slack_bot.SlackBot') as mock_slack:
            
            # Mock bot instances
            mock_telegram_instance = AsyncMock()
            mock_slack_instance = AsyncMock()
            mock_telegram.return_value = mock_telegram_instance
            mock_slack.return_value = mock_slack_instance
            
            # Set up gateway with bots
            gateway.settings.telegram_bot_token = "test_token"
            gateway.settings.slack_bot_token = "test_token"
            gateway.settings.telegram_chat_id = "chat123"
            gateway.settings.slack_channel = "#alerts"
            
            gateway.telegram_bot = mock_telegram_instance
            gateway.slack_bot = mock_slack_instance
            
            # Send alert
            await gateway.send_alert("Test alert message", "high")
            
            # Verify alerts were sent
            mock_telegram_instance.send_message.assert_called_once()
            mock_slack_instance.send_message.assert_called_once()
    
    def test_command_history_tracking(self, gateway):
        """Test command history tracking."""
        # Simulate command execution
        gateway.command_history.append({
            "bot_type": "telegram",
            "user_id": "user123",
            "command": "/status",
            "args": [],
            "timestamp": datetime.now()
        })
        
        assert len(gateway.command_history) == 1
        assert gateway.command_history[0]["command"] == "/status"
        assert gateway.command_history[0]["user_id"] == "user123"


class TestTelegramBot:
    """Test suite for TelegramBot."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        settings = Settings()
        settings.telegram_bot_token = "test_telegram_token"
        return settings
    
    @pytest.fixture
    def gateway(self, settings):
        """Create a mock gateway."""
        return Mock()
    
    @pytest.fixture
    def telegram_bot(self, settings, gateway):
        """Create a TelegramBot instance."""
        with patch('telegram.Bot'):
            return TelegramBot(settings, gateway)
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, telegram_bot):
        """Test bot initialization."""
        assert telegram_bot.settings is not None
        assert telegram_bot.gateway is not None
        assert telegram_bot.running is False
    
    @pytest.mark.asyncio
    async def test_start_bot(self, telegram_bot):
        """Test starting the Telegram bot."""
        with patch('telegram.ext.Application') as mock_app:
            mock_application = AsyncMock()
            mock_app.builder.return_value.token.return_value.build.return_value = mock_application
            
            await telegram_bot.start()
            
            assert telegram_bot.running is True
            mock_application.initialize.assert_called_once()
            mock_application.start.assert_called_once()
            mock_application.updater.start_polling.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_bot(self, telegram_bot):
        """Test stopping the Telegram bot."""
        with patch('telegram.ext.Application') as mock_app:
            mock_application = AsyncMock()
            mock_app.builder.return_value.token.return_value.build.return_value = mock_application
            
            # Start bot first
            await telegram_bot.start()
            
            # Stop bot
            await telegram_bot.stop()
            
            assert telegram_bot.running is False
            mock_application.updater.stop.assert_called_once()
            mock_application.stop.assert_called_once()
            mock_application.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_start_command(self, telegram_bot):
        """Test handling /start command."""
        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        
        await telegram_bot._handle_start(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Welcome to DevOps AI Platform" in call_args
        assert "AI-powered DevOps assistant" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_help_command(self, telegram_bot):
        """Test handling /help command."""
        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        
        await telegram_bot._handle_help(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "DevOps AI Platform Commands" in call_args
        assert "/status" in call_args
        assert "/cost" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_status_command(self, telegram_bot):
        """Test handling /status command."""
        mock_update = Mock()
        mock_update.effective_user.id = "user123"
        mock_update.message.reply_text = AsyncMock()
        mock_context = Mock()
        
        # Mock gateway response
        telegram_bot.gateway.handle_command = AsyncMock(return_value="Platform Status: Healthy")
        
        await telegram_bot._handle_status(mock_update, mock_context)
        
        telegram_bot.gateway.handle_command.assert_called_once_with("telegram", "user123", "/status")
        mock_update.message.reply_text.assert_called_once_with("Platform Status: Healthy", parse_mode='Markdown')
    
    @pytest.mark.asyncio
    async def test_send_message(self, telegram_bot):
        """Test sending messages."""
        with patch('telegram.Bot') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot_class.return_value = mock_bot
            telegram_bot.bot = mock_bot
            telegram_bot.running = True
            
            await telegram_bot.send_message("chat123", "Test message")
            
            mock_bot.send_message.assert_called_once_with(
                chat_id="chat123",
                text="Test message",
                parse_mode='Markdown'
            )
    
    @pytest.mark.asyncio
    async def test_send_alert(self, telegram_bot):
        """Test sending alerts."""
        with patch.object(telegram_bot, 'send_message') as mock_send:
            await telegram_bot.send_alert("chat123", "Test alert", "high")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "chat123"
            assert "🚨" in call_args[1]  # High priority indicator
            assert "ALERT" in call_args[1]


class TestSlackBot:
    """Test suite for SlackBot."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        settings = Settings()
        settings.slack_bot_token = "test_slack_token"
        return settings
    
    @pytest.fixture
    def gateway(self, settings):
        """Create a mock gateway."""
        return Mock()
    
    @pytest.fixture
    def slack_bot(self, settings, gateway):
        """Create a SlackBot instance."""
        with patch('slack_sdk.web.async_client.AsyncWebClient'):
            return SlackBot(settings, gateway)
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, slack_bot):
        """Test bot initialization."""
        assert slack_bot.settings is not None
        assert slack_bot.gateway is not None
        assert slack_bot.running is False
    
    @pytest.mark.asyncio
    async def test_start_bot(self, slack_bot):
        """Test starting the Slack bot."""
        with patch('slack_sdk.socket_mode.async_client.AsyncSocketModeClient') as mock_socket:
            mock_socket_client = AsyncMock()
            mock_socket.return_value = mock_socket_client
            
            await slack_bot.start()
            
            assert slack_bot.running is True
            mock_socket_client.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_bot(self, slack_bot):
        """Test stopping the Slack bot."""
        with patch('slack_sdk.socket_mode.async_client.AsyncSocketModeClient') as mock_socket:
            mock_socket_client = AsyncMock()
            mock_socket.return_value = mock_socket_client
            
            # Start bot first
            await slack_bot.start()
            
            # Stop bot
            await slack_bot.stop()
            
            assert slack_bot.running is False
            mock_socket_client.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_socket_request(self, slack_bot):
        """Test handling socket requests."""
        mock_client = AsyncMock()
        mock_request = Mock()
        mock_request.type = "events_api"
        mock_request.payload = {"event": {"type": "message", "text": "/status"}}
        mock_request.envelope_id = "test_envelope"
        
        with patch.object(slack_bot, '_handle_event') as mock_handle_event:
            await slack_bot._handle_socket_request(mock_client, mock_request)
            
            mock_handle_event.assert_called_once_with(mock_request)
            mock_client.send_socket_mode_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_message_event(self, slack_bot):
        """Test handling message events."""
        event = {
            "type": "message",
            "text": "/status",
            "user": "user123",
            "channel": "channel123"
        }
        
        with patch.object(slack_bot, '_send_message') as mock_send:
            slack_bot.gateway.handle_command = AsyncMock(return_value="Status: Healthy")
            
            await slack_bot._handle_message_event(event)
            
            slack_bot.gateway.handle_command.assert_called_once_with("slack", "user123", "/status")
            mock_send.assert_called_once_with("channel123", "Status: Healthy")
    
    @pytest.mark.asyncio
    async def test_handle_app_mention(self, slack_bot):
        """Test handling app mentions."""
        event = {
            "type": "app_mention",
            "text": "<@BOT_ID> /status",
            "user": "user123",
            "channel": "channel123"
        }
        
        with patch.object(slack_bot, '_send_message') as mock_send:
            slack_bot.gateway.handle_command = AsyncMock(return_value="Status: Healthy")
            
            await slack_bot._handle_app_mention(event)
            
            slack_bot.gateway.handle_command.assert_called_once_with("slack", "user123", "/status")
            mock_send.assert_called_once_with("channel123", "Status: Healthy")
    
    @pytest.mark.asyncio
    async def test_send_message(self, slack_bot):
        """Test sending messages."""
        with patch.object(slack_bot, '_send_message') as mock_send:
            await slack_bot.send_message("channel123", "Test message")
            
            mock_send.assert_called_once_with("channel123", "Test message")
    
    @pytest.mark.asyncio
    async def test_send_alert(self, slack_bot):
        """Test sending alerts."""
        with patch.object(slack_bot, 'send_message') as mock_send:
            await slack_bot.send_alert("channel123", "Test alert", "high")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "channel123"
            assert "🚨" in call_args[1]  # High priority indicator
            assert "ALERT" in call_args[1]


if __name__ == "__main__":
    pytest.main([__file__])
