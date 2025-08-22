#!/usr/bin/env python3
"""
DevOps AI Platform - Main Application Entry Point

A comprehensive AI-powered DevOps platform that automates complex infrastructure
operations using MCP (Model Context Protocol) agents with human oversight.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from bots.gateway import BotGateway
from agents.registry import AgentRegistry
from core.config import Settings
from core.database import init_database
from core.logging import setup_logging
from core.monitoring import setup_monitoring
from core.scheduler import TaskScheduler

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("🚀 Starting DevOps AI Platform...")
    
    try:
        # Initialize configuration
        settings = Settings()
        app_state["settings"] = settings
        
        # Setup logging
        setup_logging(settings.log_level)
        
        # Initialize database
        await init_database(settings.database_url)
        logger.info("✅ Database initialized")
        
        # Setup monitoring
        setup_monitoring(settings)
        logger.info("✅ Monitoring setup complete")
        
        # Initialize agent registry
        agent_registry = AgentRegistry(settings)
        app_state["agent_registry"] = agent_registry
        logger.info("✅ Agent registry initialized")
        
        # Initialize bot gateway
        bot_gateway = BotGateway(settings, agent_registry)
        app_state["bot_gateway"] = bot_gateway
        await bot_gateway.start()
        logger.info("✅ Bot gateway started")
        
        # Initialize task scheduler
        scheduler = TaskScheduler(agent_registry, bot_gateway)
        app_state["scheduler"] = scheduler
        await scheduler.start()
        logger.info("✅ Task scheduler started")
        
        logger.info("🎉 DevOps AI Platform started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start platform: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down DevOps AI Platform...")
    
    try:
        # Stop scheduler
        if "scheduler" in app_state:
            await app_state["scheduler"].stop()
            logger.info("✅ Task scheduler stopped")
        
        # Stop bot gateway
        if "bot_gateway" in app_state:
            await app_state["bot_gateway"].stop()
            logger.info("✅ Bot gateway stopped")
        
        logger.info("✅ Platform shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="DevOps AI Platform",
    description="AI-powered DevOps platform with human oversight",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with platform status."""
    return {
        "message": "DevOps AI Platform",
        "version": "1.0.0",
        "status": "operational",
        "agents": len(app_state.get("agent_registry", {}).agents) if "agent_registry" in app_state else 0
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if all components are healthy
        health_status = {
            "status": "healthy",
            "components": {
                "database": "healthy",
                "bot_gateway": "healthy" if "bot_gateway" in app_state else "unhealthy",
                "agent_registry": "healthy" if "agent_registry" in app_state else "unhealthy",
                "scheduler": "healthy" if "scheduler" in app_state else "unhealthy"
            }
        }
        
        # Check if any component is unhealthy
        if any(status == "unhealthy" for status in health_status["components"].values()):
            health_status["status"] = "degraded"
            return JSONResponse(status_code=503, content=health_status)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    agents = app_state["agent_registry"].list_agents()
    return {"agents": agents}


@app.post("/agents/{agent_name}/execute")
async def execute_agent(agent_name: str, context: Dict[str, Any] = None):
    """Execute a specific agent."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        result = await app_state["agent_registry"].execute_agent(agent_name, context or {})
        return {"agent": agent_name, "result": result}
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get platform metrics."""
    # This would integrate with Prometheus metrics
    return {
        "total_agents": len(app_state.get("agent_registry", {}).agents) if "agent_registry" in app_state else 0,
        "active_tasks": app_state.get("scheduler", {}).active_tasks if "scheduler" in app_state else 0,
        "bot_connections": app_state.get("bot_gateway", {}).connection_count if "bot_gateway" in app_state else 0
    }


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENABLE_DEBUG_MODE", "false").lower() == "true"
    
    # Start the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
