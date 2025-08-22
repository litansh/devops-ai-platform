"""
Database configuration and initialization for DevOps AI Platform.

This module handles database connections, migrations, and session management
for PostgreSQL, Redis, and MongoDB.
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

import asyncpg
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float

from core.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy setup
Base = declarative_base()

# Global database connections
_postgres_engine: Optional[AsyncSession] = None
_redis_client: Optional[redis.Redis] = None
_mongodb_client: Optional[AsyncIOMotorClient] = None


async def init_database(database_url: str) -> None:
    """
    Initialize database connections.
    
    Args:
        database_url: PostgreSQL connection URL
    """
    global _postgres_engine, _redis_client, _mongodb_client
    
    try:
        # Initialize PostgreSQL
        _postgres_engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        
        # Test PostgreSQL connection
        async with _postgres_engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("✅ PostgreSQL connection established")
        
        # Initialize Redis
        _redis_client = redis.from_url(
            "redis://localhost:6379/0",
            decode_responses=True,
            max_connections=20
        )
        
        # Test Redis connection
        await _redis_client.ping()
        logger.info("✅ Redis connection established")
        
        # Initialize MongoDB
        _mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
        
        # Test MongoDB connection
        await _mongodb_client.admin.command('ping')
        logger.info("✅ MongoDB connection established")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_database() -> None:
    """Close all database connections."""
    global _postgres_engine, _redis_client, _mongodb_client
    
    try:
        if _postgres_engine:
            await _postgres_engine.dispose()
            logger.info("✅ PostgreSQL connection closed")
        
        if _redis_client:
            await _redis_client.close()
            logger.info("✅ Redis connection closed")
        
        if _mongodb_client:
            _mongodb_client.close()
            logger.info("✅ MongoDB connection closed")
            
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")


def get_postgres_session() -> async_sessionmaker[AsyncSession]:
    """Get PostgreSQL session factory."""
    if not _postgres_engine:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return async_sessionmaker(
        _postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


def get_redis_client() -> redis.Redis:
    """Get Redis client."""
    if not _redis_client:
        raise RuntimeError("Redis not initialized. Call init_database() first.")
    
    return _redis_client


def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client."""
    if not _mongodb_client:
        raise RuntimeError("MongoDB not initialized. Call init_database() first.")
    
    return _mongodb_client


@asynccontextmanager
async def get_db_session():
    """Get a database session with automatic cleanup."""
    session_factory = get_postgres_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Database models
class AgentExecution(Base):
    """Model for tracking agent executions."""
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    execution_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # success, failed, running
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BotInteraction(Base):
    """Model for tracking bot interactions."""
    __tablename__ = "bot_interactions"
    
    id = Column(Integer, primary_key=True)
    bot_type = Column(String, nullable=False)  # telegram, slack
    user_id = Column(String, nullable=False)
    command = Column(String, nullable=False)
    response = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InfrastructureChange(Base):
    """Model for tracking infrastructure changes."""
    __tablename__ = "infrastructure_changes"
    
    id = Column(Integer, primary_key=True)
    change_type = Column(String, nullable=False)  # scaling, deployment, configuration
    resource_name = Column(String, nullable=False)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    status = Column(String, nullable=False)  # pending, approved, rejected, executed
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


# Add missing imports
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
