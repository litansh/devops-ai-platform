"""
Telegram Bot for DevOps AI Platform.

This module provides the Telegram bot interface for interacting with
the platform and its AI agents.
"""

import asyncio
from typing import Optional, List
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from core.logging import LoggerMixin
from core.config import Settings
from bots.gateway import BotGateway


class TelegramBot(LoggerMixin):
    """
    Telegram bot for DevOps AI Platform.
    
    This class handles Telegram bot interactions, command processing,
    and message routing to the bot gateway.
    """
    
    def __init__(self, settings: Settings, gateway: BotGateway):
        self.settings = settings
        self.gateway = gateway
        self.bot = Bot(token=settings.telegram_bot_token)
        self.application: Optional[Application] = None
        self.running = False
        
        self.logger.info("TelegramBot initialized")
    
    async def start(self) -> None:
        """Start the Telegram bot."""
        try:
            # Create application
            self.application = Application.builder().token(self.settings.telegram_bot_token).build()
            
            # Add command handlers
            self._add_command_handlers()
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.running = True
            self.logger.info("✅ Telegram bot started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Telegram bot: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Telegram bot."""
        if not self.running:
            return
        
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self.running = False
            self.logger.info("✅ Telegram bot stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping Telegram bot: {e}")
    
    def _add_command_handlers(self) -> None:
        """Add command handlers to the bot."""
        if not self.application:
            return
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("cost", self._handle_cost))
        self.application.add_handler(CommandHandler("analysis", self._handle_analysis))
        self.application.add_handler(CommandHandler("anomaly", self._handle_anomaly))
        self.application.add_handler(CommandHandler("predict", self._handle_predict))
        self.application.add_handler(CommandHandler("agent", self._handle_agent))
        self.application.add_handler(CommandHandler("approve", self._handle_approve))
        self.application.add_handler(CommandHandler("scale", self._handle_scale))
        self.application.add_handler(CommandHandler("logs", self._handle_logs))
        self.application.add_handler(CommandHandler("alerts", self._handle_alerts))
        self.application.add_handler(CommandHandler("run", self._handle_run))
        self.application.add_handler(CommandHandler("graph", self._handle_graph))
        
        # Add message handler for general commands
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome_message = """
🤖 **Welcome to DevOps AI Platform!**

I'm your AI-powered DevOps assistant. I can help you with:

• **Infrastructure Monitoring** - Check platform health and status
• **Cost Analysis** - Monitor and optimize cloud spending
• **Anomaly Detection** - Identify unusual patterns and issues
• **Traffic Prediction** - Predict traffic bursts and scaling needs
• **Agent Management** - Control and monitor AI agents
• **Operations** - Scale services, view logs, run tests

Use `/help` to see all available commands.

**Quick Start**:
• `/status` - Check platform health
• `/cost` - View cost analysis
• `/analysis` - Run AI-powered analysis
"""
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_message = """
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
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/status")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_cost(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cost command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/cost")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analysis command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/analysis")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_anomaly(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /anomaly command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/anomaly")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /predict command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/predict")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_agent(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /agent command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/agent {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /approve command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/approve {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_scale(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /scale command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/scale {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logs command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/logs {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /alerts command."""
        user_id = str(update.effective_user.id)
        response = await self.gateway.handle_command("telegram", user_id, "/alerts")
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /run command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/run {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_graph(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /graph command."""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        command = f"/graph {' '.join(args)}"
        response = await self.gateway.handle_command("telegram", user_id, command)
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle general messages."""
        user_id = str(update.effective_user.id)
        message_text = update.message.text
        
        # Check if message looks like a command
        if message_text.startswith('/'):
            response = await self.gateway.handle_command("telegram", user_id, message_text)
        else:
            response = """
🤖 I understand you're trying to interact with me, but I only respond to commands.

Use `/help` to see all available commands, or try:
• `/status` - Check platform health
• `/cost` - View cost analysis
• `/analysis` - Run AI analysis
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def send_message(self, chat_id: str, message: str) -> None:
        """
        Send a message to a specific chat.
        
        Args:
            chat_id: Telegram chat ID
            message: Message to send
        """
        try:
            if self.bot and self.running:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                self.logger.info(f"Message sent to Telegram chat {chat_id}")
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
    
    async def send_alert(self, chat_id: str, message: str, priority: str = "normal") -> None:
        """
        Send an alert message to a specific chat.
        
        Args:
            chat_id: Telegram chat ID
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
            formatted_message = f"{indicator} **ALERT**: {message}"
            
            await self.send_message(chat_id, formatted_message)
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
