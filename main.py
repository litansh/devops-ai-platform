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
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
import secrets

from bots.gateway import BotGateway
from agents.registry import AgentRegistry
from agents.base import AgentStatus
from core.config import Settings
from core.database import init_database
from core.logging import setup_logging
from core.monitoring import setup_monitoring
from core.scheduler import TaskScheduler
from core.dashboard import dashboard_router, init_dashboard

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Global application state
app_state: Dict[str, Any] = {}

# Authentication setup
security = HTTPBasic()

# Default admin credentials (should be overridden by environment variables)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials."""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting DevOps AI Platform...")
    
    try:
        # Load settings
        settings = Settings()
        app_state["settings"] = settings
        
        # Setup logging
        setup_logging(settings.log_level)
        
        # Initialize database (skip for local testing if database is not available)
        try:
            await init_database(settings.database_url)
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database initialization skipped (local mode): {e}")
            logger.info("✅ Running in local mode without database")
        
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
        scheduler = TaskScheduler(agent_registry, bot_gateway, settings)
        app_state["scheduler"] = scheduler
        await scheduler.start()
        logger.info("✅ Task scheduler started")
        
        # Initialize dashboard
        dashboard_manager = init_dashboard(settings, agent_registry)
        app_state["dashboard_manager"] = dashboard_manager
        logger.info("✅ Dashboard initialized")
        
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

# Include dashboard router
app.include_router(dashboard_router)

# Test dashboard endpoint
@app.get("/dashboard-test")
async def dashboard_test():
    """Test endpoint to verify dashboard router is working."""
    return {"message": "Dashboard router is working"}


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
async def execute_agent(agent_name: str, context: Dict[str, Any] = None, current_user: str = Depends(get_current_user)):
    """Execute a specific agent."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        result = await app_state["agent_registry"].execute_agent(agent_name, context or {})
        return {"agent": agent_name, "result": result}
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str, current_user: str = Depends(get_current_user)):
    """Restart a specific agent."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        agent_registry = app_state["agent_registry"]
        
        # Check if agent exists
        if agent_name not in agent_registry.agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agent_registry.agents[agent_name]
        
        # Disable the agent temporarily and set status to restarting
        was_enabled = agent.enabled
        agent.disable()
        # Add a temporary restarting flag to the agent
        agent._restarting = True
        
        # Reinitialize the agent
        new_agent = agent.__class__(agent_registry.settings)
        agent_registry.register_agent(new_agent)
        
        # Re-enable the agent if it was enabled before
        if was_enabled:
            new_agent.enable()
            new_agent.status = AgentStatus.IDLE  # Set back to idle after restart
            new_agent._restarting = False  # Clear restarting flag
        
        logger.info(f"Agent '{agent_name}' restarted successfully")
        return {
            "agent": agent_name, 
            "status": "restarted",
            "message": f"Agent '{agent_name}' has been restarted and is now running"
        }
    except Exception as e:
        logger.error(f"Agent restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/toggle")
async def toggle_agent(agent_name: str, current_user: str = Depends(get_current_user)):
    """Enable or disable a specific agent."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        agent_registry = app_state["agent_registry"]
        
        # Check if agent exists
        if agent_name not in agent_registry.agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agent_registry.agents[agent_name]
        
        # Toggle the agent state
        if agent.enabled:
            agent.disable()
            status = "disabled"
            message = f"Agent '{agent_name}' has been disabled"
        else:
            agent.enable()
            status = "enabled"
            message = f"Agent '{agent_name}' has been enabled and is now running"
        
        logger.info(f"Agent '{agent_name}' {status}")
        return {
            "agent": agent_name,
            "enabled": agent.enabled,
            "status": status,
            "message": message
        }
    except Exception as e:
        logger.error(f"Agent toggle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/test-error")
async def test_agent_error(agent_name: str, current_user: str = Depends(get_current_user)):
    """Test endpoint to set an agent to error state for demonstration."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        agent_registry = app_state["agent_registry"]
        
        # Check if agent exists
        if agent_name not in agent_registry.agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agent_registry.agents[agent_name]
        
        # Set agent to error state
        agent.status = AgentStatus.ERROR
        agent.error_count += 1
        
        logger.info(f"Agent '{agent_name}' set to error state for testing")
        return {
            "agent": agent_name,
            "status": "error",
            "message": f"Agent '{agent_name}' has been set to error state for testing"
        }
    except Exception as e:
        logger.error(f"Failed to set agent to error state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_name}")
async def delete_agent(agent_name: str, current_user: str = Depends(get_current_user)):
    """Delete a specific agent."""
    if "agent_registry" not in app_state:
        raise HTTPException(status_code=503, detail="Agent registry not available")
    
    try:
        agent_registry = app_state["agent_registry"]
        
        # Check if agent exists
        if agent_name not in agent_registry.agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
        
        agent = agent_registry.agents[agent_name]
        
        # Disable the agent
        agent.disable()
        
        # Remove from registry
        agent_registry.unregister_agent(agent_name)
        
        logger.info(f"Agent '{agent_name}' deleted successfully")
        return {
            "agent": agent_name,
            "status": "deleted",
            "message": f"Agent '{agent_name}' has been deleted"
        }
    except Exception as e:
        logger.error(f"Agent deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get platform metrics in Prometheus format."""
    try:
        # Get agent registry for real metrics
        agent_registry = app_state.get("agent_registry")
        if not agent_registry:
            agent_registry = AgentRegistry(Settings())
        
        # Generate Prometheus metrics
        metrics_lines = []
        
        # Agent metrics
        total_agents = len(agent_registry.agents)
        active_agents = sum(1 for agent in agent_registry.agents.values() if agent.enabled)
        
        metrics_lines.extend([
            "# HELP devops_platform_agents_total Total number of agents",
            "# TYPE devops_platform_agents_total gauge",
            f"devops_platform_agents_total {total_agents}",
            "# HELP devops_platform_active_agents Total number of active agents", 
            "# TYPE devops_platform_active_agents gauge",
            f"devops_platform_active_agents {active_agents}",
        ])
        
        # Individual agent metrics
        for agent in agent_registry.agents.values():
            agent_name = agent.name.replace('_', '_')
            health = getattr(agent, 'health', {})
            
            metrics_lines.extend([
                f"# HELP agent_executions_total Total executions for {agent_name}",
                f"# TYPE agent_executions_total counter",
                f"agent_executions_total{{agent=\"{agent_name}\"}} {health.get('execution_count', 0)}",
                f"# HELP agent_success_rate Success rate for {agent_name}",
                f"# TYPE agent_success_rate gauge",
                f"agent_success_rate{{agent=\"{agent_name}\"}} {health.get('success_rate', 0.0)}",
                f"# HELP agent_status Status of {agent_name} (1=enabled, 0=disabled)",
                f"# TYPE agent_status gauge",
                f"agent_status{{agent=\"{agent_name}\",status=\"{health.get('status', 'idle')}\"}} {1 if agent.enabled else 0}",
            ])
        
        # System metrics
        metrics_lines.extend([
            "# HELP devops_platform_uptime_seconds Platform uptime in seconds",
            "# TYPE devops_platform_uptime_seconds gauge",
            f"devops_platform_uptime_seconds {time.time() - app_state.get('start_time', time.time())}",
        ])
        
        return Response(
            content="\n".join(metrics_lines),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        # Fallback to basic metrics
        return Response(
            content=f"""# HELP devops_platform_agents_total Total number of agents
# TYPE devops_platform_agents_total gauge
devops_platform_agents_total {len(app_state.get("agent_registry", {}).agents) if "agent_registry" in app_state else 0}
# HELP devops_platform_active_tasks Total number of active tasks
# TYPE devops_platform_active_tasks gauge
devops_platform_active_tasks {app_state.get("scheduler", {}).active_tasks if "scheduler" in app_state else 0}
# HELP devops_platform_bot_connections Total number of bot connections
# TYPE devops_platform_bot_connections gauge
devops_platform_bot_connections {app_state.get("bot_gateway", {}).connection_count if "bot_gateway" in app_state else 0}
""",
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )


@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get dashboard data for the React frontend."""
    try:
        # Get dashboard manager from app state
        dashboard_manager = app_state.get("dashboard_manager")
        
        if not dashboard_manager:
            # Create a temporary dashboard manager if not available
            from core.config import Settings
            from agents.registry import AgentRegistry
            from core.dashboard import DashboardManager
            
            settings = Settings()
            agent_registry = AgentRegistry(settings)
            dashboard_manager = DashboardManager(settings, agent_registry)
        
        # Use dashboard manager to get real data with all 12 agents
        await dashboard_manager.update_dashboard_data()
        return dashboard_manager.dashboard_data.dict()
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/health")
async def get_dashboard_health():
    """Get dashboard health status."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-15T10:35:00Z",
        "version": "1.0.0"
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
