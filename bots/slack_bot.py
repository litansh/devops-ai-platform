"""
Slack Bot for DevOps AI Platform.

This module provides the Slack bot interface for interacting with
the platform and its AI agents.
"""

import asyncio
from typing import Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.async_client import AsyncBaseSocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from core.logging import LoggerMixin
from core.config import Settings
from bots.gateway import BotGateway


class SlackBot(LoggerMixin):
    """
    Slack bot for DevOps AI Platform.
    
    This class handles Slack bot interactions, command processing,
    and message routing to the bot gateway.
    """
    
    def __init__(self, settings: Settings, gateway: BotGateway):
        self.settings = settings
        self.gateway = gateway
        self.client = AsyncWebClient(token=settings.slack_bot_token)
        self.socket_client: Optional[AsyncBaseSocketModeClient] = None
        self.running = False
        
        self.logger.info("SlackBot initialized")
    
    async def start(self) -> None:
        """Start the Slack bot."""
        try:
            # Initialize socket mode client
            self.socket_client = AsyncBaseSocketModeClient(
                app_token=self.settings.slack_bot_token,
                web_client=self.client
            )
            
            # Add event handlers
            self.socket_client.socket_mode_request_listeners.append(self._handle_socket_request)
            
            # Start the client
            await self.socket_client.start()
            
            self.running = True
            self.logger.info("✅ Slack bot started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Slack bot: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Slack bot."""
        if not self.running:
            return
        
        try:
            if self.socket_client:
                await self.socket_client.stop()
            
            self.running = False
            self.logger.info("✅ Slack bot stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping Slack bot: {e}")
    
    async def _handle_socket_request(self, client: AsyncBaseSocketModeClient, req: SocketModeRequest) -> None:
        """Handle socket mode requests."""
        try:
            if req.type == "events_api":
                # Handle events API requests
                await self._handle_event(req)
            elif req.type == "interactive":
                # Handle interactive requests
                await self._handle_interactive(req)
            
            # Send acknowledgment
            await client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
            
        except Exception as e:
            self.logger.error(f"Error handling socket request: {e}")
    
    async def _handle_event(self, req: SocketModeRequest) -> None:
        """Handle Slack events."""
        try:
            event = req.payload.get("event", {})
            event_type = event.get("type")
            
            if event_type == "message":
                await self._handle_message_event(event)
            elif event_type == "app_mention":
                await self._handle_app_mention(event)
                
        except Exception as e:
            self.logger.error(f"Error handling event: {e}")
    
    async def _handle_message_event(self, event: dict) -> None:
        """Handle message events."""
        try:
            text = event.get("text", "")
            user_id = event.get("user", "")
            channel = event.get("channel", "")
            
            # Check if message is a command
            if text.startswith("/"):
                response = await self.gateway.handle_command("slack", user_id, text)
                await self._send_message(channel, response)
                
        except Exception as e:
            self.logger.error(f"Error handling message event: {e}")
    
    async def _handle_app_mention(self, event: dict) -> None:
        """Handle app mention events."""
        try:
            text = event.get("text", "")
            user_id = event.get("user", "")
            channel = event.get("channel", "")
            
            # Remove bot mention from text
            command = text.split(">", 1)[1].strip() if ">" in text else text
            
            if command.startswith("/"):
                response = await self.gateway.handle_command("slack", user_id, command)
            else:
                response = """
🤖 I understand you're trying to interact with me, but I only respond to commands.

Use `/help` to see all available commands, or try:
• `/status` - Check platform health
• `/cost` - View cost analysis
• `/analysis` - Run AI analysis
"""
            
            await self._send_message(channel, response)
            
        except Exception as e:
            self.logger.error(f"Error handling app mention: {e}")
    
    async def _handle_interactive(self, req: SocketModeRequest) -> None:
        """Handle interactive requests."""
        try:
            # Handle interactive components like buttons, menus, etc.
            payload = req.payload
            # Process interactive payload
            self.logger.info(f"Received interactive request: {payload}")
            
        except Exception as e:
            self.logger.error(f"Error handling interactive request: {e}")
    
    async def _send_message(self, channel: str, message: str) -> None:
        """Send a message to a Slack channel."""
        try:
            await self.client.chat_postMessage(
                channel=channel,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            self.logger.info(f"Message sent to Slack channel {channel}")
            
        except Exception as e:
            self.logger.error(f"Error sending Slack message: {e}")
    
    async def send_message(self, channel: str, message: str) -> None:
        """
        Send a message to a specific channel.
        
        Args:
            channel: Slack channel name or ID
            message: Message to send
        """
        await self._send_message(channel, message)
    
    async def send_alert(self, channel: str, message: str, priority: str = "normal") -> None:
        """
        Send an alert message to a specific channel.
        
        Args:
            channel: Slack channel name or ID
            message: Alert message
            priority: Alert priority
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
            formatted_message = f"{indicator} *ALERT*: {message}"
            
            await self.send_message(channel, formatted_message)
            
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")
