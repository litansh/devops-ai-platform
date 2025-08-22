#!/usr/bin/env python3
"""
DevOps AI Platform Bootstrap Script

This script provides a comprehensive bootstrap solution for deploying the
DevOps AI Platform across different environments (local, testing, production).
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.live import Live
from rich.status import Status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_retries: int = 3
    base_delay: float = 5.0
    max_delay: float = 60.0
    timeout: float = 300.0  # 5 minutes default timeout
    backoff_factor: float = 2.0

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

class BootstrapError(Exception):
    """Custom bootstrap exception."""
    pass

class RetryableOperation:
    """Handles retryable operations with timeout and progress tracking."""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.console = Console()
    
    async def execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute an operation with retry logic and timeout."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                with Status(f"[bold blue]Attempting {operation_name} (attempt {attempt + 1}/{self.config.max_retries + 1})", console=self.console):
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        operation_func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                    self.console.print(f"[green]✅ {operation_name} completed successfully!")
                    return result
                    
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"{operation_name} timed out after {self.config.timeout} seconds")
                self.console.print(f"[yellow]⏰ {operation_name} timed out (attempt {attempt + 1})")
                
            except Exception as e:
                last_exception = e
                self.console.print(f"[red]❌ {operation_name} failed (attempt {attempt + 1}): {str(e)}")
            
            # If this wasn't the last attempt, wait before retrying
            if attempt < self.config.max_retries:
                delay = min(self.config.base_delay * (self.config.backoff_factor ** attempt), self.config.max_delay)
                self.console.print(f"[yellow]⏳ Waiting {delay:.1f}s before retry...")
                await asyncio.sleep(delay)
        
        # If we get here, all attempts failed
        raise BootstrapError(f"{operation_name} failed after {self.config.max_retries + 1} attempts. Last error: {last_exception}")

class BootstrapManager:
    """Manages the bootstrap process with retry mechanisms."""
    
    def __init__(self, environment: str, config: Dict[str, Any]):
        self.environment = environment
        self.config = config
        self.retry_config = RetryConfig()
        self.retry_ops = RetryableOperation(self.retry_config)
        self.console = Console()
        
        # Set longer timeouts for specific operations
        self.operation_timeouts = {
            "docker_build": 600.0,  # 10 minutes for Docker builds
            "kind_cluster": 300.0,  # 5 minutes for Kind cluster
            "terraform_apply": 900.0,  # 15 minutes for Terraform
            "helm_install": 300.0,  # 5 minutes for Helm
            "kubectl_apply": 120.0,  # 2 minutes for kubectl
        }
    
    async def run_command_with_progress(self, command: List[str], operation_name: str, timeout: Optional[float] = None, cwd: Optional[str] = None) -> str:
        """Run a command with progress tracking and timeout."""
        timeout = timeout or self.operation_timeouts.get(operation_name, self.retry_config.timeout)
        
        async def _run_command():
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else f"Command failed with return code {process.returncode}"
                raise BootstrapError(f"{operation_name} failed: {error_msg}")
            
            return stdout.decode()
        
        return await self.retry_ops.execute_with_retry(operation_name, _run_command)
    
    async def docker_build_with_progress(self, image_name: str, context: str = ".") -> None:
        """Build Docker image with progress tracking and retry."""
        self.console.print(f"[bold blue]🐳 Building Docker image: {image_name}")
        
        # Check if image already exists and is recent
        try:
            result = await self.run_command_with_progress(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}", image_name],
                "docker_images_check",
                timeout=30.0
            )
            if result.strip():
                self.console.print(f"[yellow]⚠️ Image {image_name} already exists. Skipping build.")
                return
        except:
            pass
        
        # Build with progress
        build_command = ["docker", "build", "-t", image_name, context]
        
        async def _build_with_progress():
            process = await asyncio.create_subprocess_exec(
                *build_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Read output in real-time
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                if output:
                    # Show progress for long-running steps
                    if "Step" in output and ":" in output:
                        self.console.print(f"[dim]{output}")
                    elif "Pulling" in output or "Building" in output:
                        self.console.print(f"[blue]{output}")
                    elif "Successfully" in output:
                        self.console.print(f"[green]{output}")
            
            await process.wait()
            
            if process.returncode != 0:
                raise BootstrapError(f"Docker build failed with return code {process.returncode}")
        
        await self.retry_ops.execute_with_retry("docker_build", _build_with_progress)
    
    async def kind_cluster_with_progress(self, cluster_name: str) -> None:
        """Create Kind cluster with progress tracking and retry."""
        self.console.print(f"[bold blue]🏗️ Creating Kind cluster: {cluster_name}")
        
        # Check if cluster already exists
        try:
            result = await self.run_command_with_progress(
                ["kind", "get", "clusters"],
                "kind_clusters_check",
                timeout=30.0
            )
            if cluster_name in result:
                self.console.print(f"[yellow]⚠️ Cluster {cluster_name} already exists. Skipping creation.")
                return
        except:
            pass
        
        # Create cluster with progress
        async def _create_cluster():
            process = await asyncio.create_subprocess_exec(
                "kind", "create", "cluster", "--name", cluster_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Read output in real-time
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                if output:
                    if "Creating cluster" in output:
                        self.console.print(f"[blue]{output}")
                    elif "Ensuring node image" in output:
                        self.console.print(f"[yellow]{output}")
                    elif "Ready" in output:
                        self.console.print(f"[green]{output}")
            
            await process.wait()
            
            if process.returncode != 0:
                raise BootstrapError(f"Kind cluster creation failed with return code {process.returncode}")
        
        await self.retry_ops.execute_with_retry("kind_cluster", _create_cluster)
    
    async def docker_compose_with_progress(self, action: str = "up", detach: bool = True) -> None:
        """Run docker-compose with progress tracking and retry."""
        self.console.print(f"[bold blue]🐳 Running docker-compose {action}")
        
        command = ["docker-compose", action]
        if detach and action == "up":
            command.append("-d")
        
        async def _docker_compose():
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Read output in real-time
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().strip()
                if output:
                    if "Pulling" in output:
                        self.console.print(f"[blue]{output}")
                    elif "Creating" in output or "Starting" in output:
                        self.console.print(f"[yellow]{output}")
                    elif "Started" in output or "Up" in output:
                        self.console.print(f"[green]{output}")
            
            await process.wait()
            
            if process.returncode != 0:
                raise BootstrapError(f"docker-compose {action} failed with return code {process.returncode}")
        
        await self.retry_ops.execute_with_retry("docker_compose", _docker_compose)
    
    async def check_service_health(self, service_name: str, health_url: str, timeout: float = 60.0) -> None:
        """Check if a service is healthy with retry."""
        self.console.print(f"[bold blue]🏥 Checking {service_name} health")
        
        async def _check_health():
            process = await asyncio.create_subprocess_exec(
                "curl", "-f", "-s", health_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise BootstrapError(f"{service_name} health check failed: {stderr.decode()}")
            
            return stdout.decode()
        
        await self.retry_ops.execute_with_retry(f"{service_name}_health", _check_health)
    
    async def setup_python_environment(self) -> None:
        """Setup Python virtual environment and install dependencies."""
        self.console.print("[bold blue]🐍 Setting up Python environment and dependencies...")
        
        try:
            # Check if virtual environment exists
            venv_path = Path(".venv")
            if not venv_path.exists():
                self.console.print("[yellow]📦 Creating virtual environment...")
                await self.run_command_with_progress(
                    ["python", "-m", "venv", ".venv"],
                    "create_venv",
                    timeout=60.0
                )
            
            # Determine the correct activation command based on OS
            import platform
            if platform.system() == "Windows":
                python_path = ".venv\\Scripts\\python.exe"
                pip_path = ".venv\\Scripts\\pip.exe"
            else:
                python_path = ".venv/bin/python"
                pip_path = ".venv/bin/pip"
            
            # Upgrade pip first
            self.console.print("[yellow]📦 Upgrading pip...")
            await self.run_command_with_progress(
                [pip_path, "install", "--upgrade", "pip"],
                "upgrade_pip",
                timeout=60.0
            )
            
            # Install setuptools first to fix build issues
            self.console.print("[yellow]📦 Installing setuptools and wheel...")
            await self.run_command_with_progress(
                [pip_path, "install", "--upgrade", "setuptools", "wheel"],
                "install_build_tools",
                timeout=120.0
            )
            
            # Install Python dependencies
            self.console.print("[yellow]📦 Installing Python dependencies...")
            await self.run_command_with_progress(
                [pip_path, "install", "-r", "requirements.txt"],
                "install_python_deps",
                timeout=300.0
            )
            
            # Install frontend dependencies
            self.console.print("[yellow]📦 Installing frontend dependencies...")
            await self.run_command_with_progress(
                ["npm", "install"],
                "install_frontend_deps",
                cwd="frontend",
                timeout=300.0
            )
            
            self.console.print("[green]✅ Python environment setup complete!")
            
        except BootstrapError as e:
            self.console.print(f"[red]❌ Python environment setup failed: {e}")
            raise
    
    async def setup_frontend_dependencies(self) -> None:
        """Setup frontend dependencies only."""
        self.console.print("[bold blue]🎨 Setting up frontend dependencies...")
        
        try:
            # Install frontend dependencies
            self.console.print("[yellow]📦 Installing frontend dependencies...")
            await self.run_command_with_progress(
                ["npm", "install"],
                "install_frontend_deps",
                cwd="frontend",
                timeout=300.0
            )
            
            self.console.print("[green]✅ Frontend dependencies setup complete!")
            
        except BootstrapError as e:
            self.console.print(f"[red]❌ Frontend dependencies setup failed: {e}")
            raise
    
    async def run_tests_with_retry(self) -> None:
        """Run tests with retry mechanism."""
        self.console.print("[bold blue]🧪 Running tests...")
        
        try:
            result = await self.run_command_with_progress(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                "tests",
                timeout=120.0
            )
            self.console.print("[green]✅ Tests passed!")
        except BootstrapError as e:
            self.console.print(f"[yellow]⚠️ Tests failed: {e}")
            if not Confirm.ask("Tests failed. Continue anyway?"):
                raise BootstrapError("Bootstrap cancelled due to test failures")
    
    async def bootstrap_local_environment(self) -> None:
        """Bootstrap local environment with comprehensive retry mechanisms."""
        self.console.print(Panel.fit(
            "[bold blue]🚀 Starting Local Environment Bootstrap[/bold blue]\n"
            "This will set up the complete DevOps AI Platform locally\n"
            "with retry mechanisms for all operations.",
            title="Local Bootstrap"
        ))
        
        try:
            # Step 1: Build Docker image with retry (includes Python environment)
            await self.docker_build_with_progress("local/devops-ai-platform:latest")
            
            # Step 2: Setup frontend dependencies
            self.console.print("[bold blue]🎨 Setting up frontend dependencies...")
            await self.setup_frontend_dependencies()
            
            # Step 3: Start services with docker-compose
            await self.docker_compose_with_progress("up", detach=True)
            
            # Step 4: Wait for services to be ready
            self.console.print("[bold blue]⏳ Waiting for services to be ready...")
            await asyncio.sleep(30)
            
            # Step 5: Check service health
            services = [
                ("Application", "http://localhost:8000/health"),
                ("Grafana", "http://localhost:3001/api/health"),
                ("Prometheus", "http://localhost:9090/-/healthy"),
            ]
            
            for service_name, health_url in services:
                try:
                    await self.check_service_health(service_name, health_url)
                except BootstrapError as e:
                    self.console.print(f"[yellow]⚠️ {service_name} health check failed: {e}")
            
            # Step 6: Start React frontend
            self.console.print("[bold blue]🎨 Starting React frontend...")
            try:
                await self.run_command_with_progress(
                    ["npm", "start"],
                    "react_frontend",
                    cwd="frontend",
                    timeout=60.0
                )
            except BootstrapError as e:
                self.console.print(f"[yellow]⚠️ React frontend start failed: {e}")
                self.console.print("[yellow]You can start it manually with: cd frontend && npm start")
            
            self.console.print(Panel.fit(
                "[bold green]🎉 Local Environment Bootstrap Complete![/bold green]\n\n"
                "[bold]Services Available:[/bold]\n"
                "• Application API: http://localhost:8000\n"
                "• React Dashboard: http://localhost:3000\n"
                "• Grafana: http://localhost:3001 (admin/admin)\n"
                "• Prometheus: http://localhost:9090\n\n"
                "[bold]Next Steps:[/bold]\n"
                "• Open the React dashboard at http://localhost:3000\n"
                "• Test the Telegram bot\n"
                "• Monitor services in Grafana",
                title="✅ Success"
            ))
            
        except BootstrapError as e:
            self.console.print(Panel.fit(
                f"[bold red]❌ Bootstrap Failed: {e}[/bold red]\n\n"
                "The bootstrap process encountered an error.\n"
                "Check the logs above for details.\n\n"
                "[bold]Recovery Options:[/bold]\n"
                "• Run the destroy script: ./scripts/destroy-local.sh\n"
                "• Check Docker and system resources\n"
                "• Try running individual components manually",
                title="❌ Error"
            ))
            raise
    
    async def bootstrap_testing_environment(self) -> None:
        """Bootstrap testing environment."""
        self.console.print("[bold blue]🧪 Testing environment bootstrap not yet implemented")
        # TODO: Implement testing environment bootstrap
    
    async def bootstrap_production_environment(self) -> None:
        """Bootstrap production environment."""
        self.console.print("[bold blue]🏭 Production environment bootstrap not yet implemented")
        # TODO: Implement production environment bootstrap

def load_config(environment: str) -> Dict[str, Any]:
    """Load configuration for the specified environment."""
    config = {
        "local": {
            "cluster_name": "devops-ai-platform-local",
            "registry": "local",
            "monitoring": True,
            "grafana_admin_password": "admin",
            "argocd_admin_password": "admin",
            "terraform": {
                "workspace": "local",
                "backend": "local",
                "variables": {
                    "environment": "local",
                    "aws_region": "us-west-2"
                }
            },
            "ports": {
                "application": 8000,
                "argocd": 8080,
                "grafana": 3001,
                "prometheus": 9090
            },
            "resources": {
                "cpu_limit": "1000m",
                "memory_limit": "2Gi",
                "cpu_request": "500m",
                "memory_request": "1Gi"
            }
        },
        "testing": {
            "cluster_name": "devops-ai-platform-testing",
            "registry": "ecr",
            "monitoring": True,
            "terraform": {
                "workspace": "testing",
                "backend": "s3",
                "variables": {
                    "environment": "testing",
                    "aws_region": "us-west-2"
                }
            }
        },
        "production": {
            "cluster_name": "devops-ai-platform-production",
            "registry": "ecr",
            "monitoring": True,
            "terraform": {
                "workspace": "production",
                "backend": "s3",
                "variables": {
                    "environment": "production",
                    "aws_region": "us-west-2"
                }
            }
        }
    }
    
    return config.get(environment, config["local"])

def check_prerequisites() -> bool:
    """Check if all prerequisites are installed."""
    console.print("[bold blue]🔍 Checking prerequisites...")
    
    prerequisites = [
        ("docker", ["docker", "--version"]),
        ("kubectl", ["kubectl", "version", "--client"]),
        ("helm", ["helm", "version"]),
        ("terraform", ["terraform", "version"]),
        ("kind", ["kind", "version"])
    ]
    
    all_installed = True
    
    for name, command in prerequisites:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                console.print(f"✅ {name} is installed")
                console.print(f"   Output: {result.stdout.strip()}")
            else:
                console.print(f"❌ {name} is not installed or not working")
                all_installed = False
        except subprocess.TimeoutExpired:
            console.print(f"❌ {name} check timed out")
            all_installed = False
        except FileNotFoundError:
            console.print(f"❌ {name} is not installed")
            all_installed = False
    
    return all_installed

async def main():
    """Main bootstrap function."""
    parser = argparse.ArgumentParser(description="DevOps AI Platform Bootstrap")
    parser.add_argument("--env", choices=["local", "testing", "production"], 
                       default="local", help="Environment to bootstrap")
    parser.add_argument("--skip-tests", action="store_true", 
                       help="Skip running tests")
    parser.add_argument("--timeout", type=float, default=300.0,
                       help="Timeout for operations in seconds")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.env)
    
    # Display configuration
    console.print(Panel.fit(
        f"[bold blue]🚀 DevOps AI Platform Bootstrap[/bold blue]\n"
        f"Environment: {args.env}\n"
        f"Configuration: {json.dumps(config, indent=2)}",
        title="Bootstrap Configuration"
    ))
    
    # Check prerequisites
    if not check_prerequisites():
        console.print("[red]❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Create bootstrap manager
    manager = BootstrapManager(args.env, config)
    
    # Set timeout
    manager.retry_config.timeout = args.timeout
    
    # Run bootstrap based on environment
    try:
        if args.env == "local":
            await manager.bootstrap_local_environment()
        elif args.env == "testing":
            await manager.bootstrap_testing_environment()
        elif args.env == "production":
            await manager.bootstrap_production_environment()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Bootstrap failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
