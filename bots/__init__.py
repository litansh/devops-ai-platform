"""
Bot Interface module for DevOps AI Platform.

This module provides Telegram and Slack bot interfaces for interacting
with the platform and its AI agents.
"""

from .gateway import BotGateway
from .telegram_bot import TelegramBot
from .slack_bot import SlackBot

__version__ = "1.0.0"
__all__ = ["BotGateway", "TelegramBot", "SlackBot"]
