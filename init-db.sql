
-- Initialize DevOps AI Platform database
CREATE DATABASE IF NOT EXISTS devops_ai_platform;

-- Create tables for agent executions
CREATE TABLE IF NOT EXISTS agent_executions (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    execution_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for bot interactions
CREATE TABLE IF NOT EXISTS bot_interactions (
    id SERIAL PRIMARY KEY,
    bot_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    command VARCHAR(255) NOT NULL,
    response TEXT,
    execution_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tables for infrastructure changes
CREATE TABLE IF NOT EXISTS infrastructure_changes (
    id SERIAL PRIMARY KEY,
    change_type VARCHAR(100) NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    approved_by VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_name ON agent_executions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_created_at ON agent_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_bot_interactions_bot_type ON bot_interactions(bot_type);
CREATE INDEX IF NOT EXISTS idx_bot_interactions_user_id ON bot_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_infrastructure_changes_status ON infrastructure_changes(status);
CREATE INDEX IF NOT EXISTS idx_infrastructure_changes_created_at ON infrastructure_changes(created_at);
