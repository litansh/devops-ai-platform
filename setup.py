#!/usr/bin/env python3
"""
Setup script for DevOps AI Platform.

This script handles the initial setup and configuration of the platform.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def check_dependencies():
    """Check if required system dependencies are installed."""
    dependencies = {
        "docker": "Docker",
        "docker-compose": "Docker Compose",
        "git": "Git"
    }
    
    missing = []
    for cmd, name in dependencies.items():
        if shutil.which(cmd) is None:
            missing.append(name)
        else:
            print(f"✅ {name} found")
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install the missing dependencies and try again.")
        return False
    
    return True


def create_env_file():
    """Create .env file from template."""
    env_template = Path("config.env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️ .env file already exists, skipping creation")
        return True
    
    if not env_template.exists():
        print("❌ config.env.example not found")
        return False
    
    shutil.copy(env_template, env_file)
    print("✅ Created .env file from template")
    print("⚠️ Please update .env file with your configuration")
    return True


def install_python_dependencies():
    """Install Python dependencies."""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command("pip install -r requirements.txt", "Installing Python dependencies")


def setup_database():
    """Setup database initialization script."""
    init_db_sql = """
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
"""
    
    with open("init-db.sql", "w") as f:
        f.write(init_db_sql)
    
    print("✅ Created database initialization script")
    return True


def setup_monitoring():
    """Setup monitoring configuration."""
    monitoring_dir = Path("monitoring")
    monitoring_dir.mkdir(exist_ok=True)
    
    # Prometheus configuration
    prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'devops-ai-platform'
    static_configs:
      - targets: ['devops-ai-platform:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
"""
    
    with open(monitoring_dir / "prometheus.yml", "w") as f:
        f.write(prometheus_config)
    
    # AlertManager configuration
    alertmanager_config = """
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://devops-ai-platform:8000/alerts'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
"""
    
    with open(monitoring_dir / "alertmanager.yml", "w") as f:
        f.write(alertmanager_config)
    
    # Create Grafana directories
    grafana_dir = monitoring_dir / "grafana"
    grafana_dir.mkdir(exist_ok=True)
    (grafana_dir / "provisioning").mkdir(exist_ok=True)
    (grafana_dir / "dashboards").mkdir(exist_ok=True)
    
    print("✅ Created monitoring configuration")
    return True


def run_tests():
    """Run the test suite."""
    if not Path("tests").exists():
        print("⚠️ No tests directory found, skipping tests")
        return True
    
    return run_command("python -m pytest tests/ -v", "Running tests")


def build_docker():
    """Build Docker image."""
    return run_command("docker-compose build", "Building Docker image")


def main():
    """Main setup function."""
    print("🚀 DevOps AI Platform Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Creating environment file", create_env_file),
        ("Installing Python dependencies", install_python_dependencies),
        ("Setting up database", setup_database),
        ("Setting up monitoring", setup_monitoring),
        ("Running tests", run_tests),
        ("Building Docker image", build_docker),
    ]
    
    failed_steps = []
    
    for description, step_func in steps:
        if not step_func():
            failed_steps.append(description)
    
    print("\n" + "=" * 50)
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease fix the errors and run setup again.")
        sys.exit(1)
    else:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with your configuration")
        print("2. Start the platform: docker-compose up -d")
        print("3. Access the platform at http://localhost:8000")
        print("4. Access Grafana at http://localhost:3000 (admin/admin)")
        print("5. Access Prometheus at http://localhost:9090")


if __name__ == "__main__":
    main()
