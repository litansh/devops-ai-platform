#!/usr/bin/env python3
"""
DevOps AI Platform Operator

A simple operator that provides unified deployment and management of the DevOps AI Platform.
This operator can deploy to any environment and provides a simple interface for common operations.

Usage:
    python scripts/operator.py deploy --env local
    python scripts/operator.py status
    python scripts/operator.py logs
    python scripts/operator.py scale --replicas 3
    python scripts/operator.py backup
    python scripts/operator.py restore
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from bootstrap import BootstrapManager, load_config

console = Console()


class DevOpsAIOperator:
    """Simple operator for managing the DevOps AI Platform."""
    
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.config = load_config(environment)
        self.project_root = Path(__file__).parent.parent
        self.bootstrap_manager = BootstrapManager(environment, self.config)
    
    def deploy(self, skip_tests: bool = False, skip_build: bool = False) -> bool:
        """Deploy the platform to the target environment."""
        console.print(Panel.fit("🚀 Deploying DevOps AI Platform", style="bold blue"))
        
        try:
            # Check prerequisites
            if not self.bootstrap_manager.check_prerequisites():
                return False
            
            # Setup environment configuration
            if not self.bootstrap_manager.setup_environment_config():
                return False
            
            # Run tests (unless skipped)
            if not skip_tests:
                if not self.bootstrap_manager.run_tests():
                    if not Confirm.ask("Tests failed. Continue anyway?"):
                        return False
            
            # Build and push image (unless skipped)
            if not skip_build:
                self.bootstrap_manager.build_and_push_image()
            
            # Deploy based on environment
            success = False
            if self.environment == "local":
                success = self.bootstrap_manager.deploy_local_environment()
            elif self.environment == "eks":
                success = self.bootstrap_manager.deploy_eks_environment()
            elif self.environment == "gcp":
                success = self.bootstrap_manager.deploy_gcp_environment()
            
            if success:
                self.bootstrap_manager.show_status()
                return True
            else:
                console.print("❌ Deployment failed")
                return False
                
        except Exception as e:
            console.print(f"❌ Deployment failed: {e}")
            return False
    
    def status(self) -> bool:
        """Show the status of the platform."""
        console.print(Panel.fit("📊 Platform Status", style="bold green"))
        
        try:
            # Check if kubectl is available
            try:
                self.bootstrap_manager.run_command(["kubectl", "version", "--client"], check=False)
            except FileNotFoundError:
                console.print("❌ kubectl not found. Cannot check status.")
                return False
            
            # Get cluster info
            console.print("🔍 Cluster Information:")
            try:
                result = self.bootstrap_manager.run_command(["kubectl", "cluster-info"], check=False)
                if result.returncode == 0:
                    console.print(f"✅ {result.stdout.strip()}")
                else:
                    console.print("❌ Not connected to a cluster")
                    return False
            except Exception as e:
                console.print(f"❌ Error getting cluster info: {e}")
                return False
            
            # Get pod status
            console.print("\n📦 Pod Status:")
            try:
                result = self.bootstrap_manager.run_command([
                    "kubectl", "get", "pods", "--all-namespaces", 
                    "-o", "wide"
                ], check=False)
                if result.returncode == 0:
                    console.print(result.stdout)
                else:
                    console.print("❌ Error getting pod status")
            except Exception as e:
                console.print(f"❌ Error getting pod status: {e}")
            
            # Get service status
            console.print("\n🌐 Service Status:")
            try:
                result = self.bootstrap_manager.run_command([
                    "kubectl", "get", "services", "--all-namespaces"
                ], check=False)
                if result.returncode == 0:
                    console.print(result.stdout)
                else:
                    console.print("❌ Error getting service status")
            except Exception as e:
                console.print(f"❌ Error getting service status: {e}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ Status check failed: {e}")
            return False
    
    def logs(self, service: str = "devops-ai-platform", namespace: str = "default", lines: int = 50) -> bool:
        """Show logs for a service."""
        console.print(Panel.fit(f"📋 Logs for {service}", style="bold yellow"))
        
        try:
            result = self.bootstrap_manager.run_command([
                "kubectl", "logs", f"deployment/{service}", 
                "-n", namespace, "--tail", str(lines)
            ], check=False)
            
            if result.returncode == 0:
                console.print(result.stdout)
                return True
            else:
                console.print(f"❌ Error getting logs: {result.stderr}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error getting logs: {e}")
            return False
    
    def scale(self, service: str = "devops-ai-platform", namespace: str = "default", replicas: int = 2) -> bool:
        """Scale a service."""
        console.print(Panel.fit(f"⚖️ Scaling {service} to {replicas} replicas", style="bold magenta"))
        
        try:
            result = self.bootstrap_manager.run_command([
                "kubectl", "scale", "deployment", service,
                "--replicas", str(replicas), "-n", namespace
            ], check=False)
            
            if result.returncode == 0:
                console.print(f"✅ Successfully scaled {service} to {replicas} replicas")
                return True
            else:
                console.print(f"❌ Error scaling service: {result.stderr}")
                return False
                
        except Exception as e:
            console.print(f"❌ Error scaling service: {e}")
            return False
    
    def backup(self) -> bool:
        """Create a backup of the platform."""
        console.print(Panel.fit("💾 Creating Backup", style="bold cyan"))
        
        try:
            # Create backup directory
            backup_dir = self.project_root / "backups" / f"backup-{self.environment}-{int(time.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup Kubernetes resources
            console.print("📦 Backing up Kubernetes resources...")
            self.bootstrap_manager.run_command([
                "kubectl", "get", "all", "--all-namespaces", "-o", "yaml"
            ], cwd=backup_dir, check=False)
            
            # Backup configuration
            console.print("⚙️ Backing up configuration...")
            config_files = [
                ".env",
                "config.env.example",
                "scripts/bootstrap-config.yaml"
            ]
            
            for config_file in config_files:
                src = self.project_root / config_file
                if src.exists():
                    dst = backup_dir / config_file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    self.bootstrap_manager.run_command(["cp", str(src), str(dst)])
            
            console.print(f"✅ Backup created at: {backup_dir}")
            return True
            
        except Exception as e:
            console.print(f"❌ Backup failed: {e}")
            return False
    
    def restore(self, backup_path: str) -> bool:
        """Restore from a backup."""
        console.print(Panel.fit(f"🔄 Restoring from {backup_path}", style="bold orange"))
        
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                console.print(f"❌ Backup directory not found: {backup_path}")
                return False
            
            # Restore Kubernetes resources
            console.print("📦 Restoring Kubernetes resources...")
            k8s_backup = backup_dir / "k8s-backup.yaml"
            if k8s_backup.exists():
                self.bootstrap_manager.run_command([
                    "kubectl", "apply", "-f", str(k8s_backup)
                ], check=False)
            
            # Restore configuration
            console.print("⚙️ Restoring configuration...")
            config_files = [
                ".env",
                "config.env.example",
                "scripts/bootstrap-config.yaml"
            ]
            
            for config_file in config_files:
                src = backup_dir / config_file
                if src.exists():
                    dst = self.project_root / config_file
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    self.bootstrap_manager.run_command(["cp", str(src), str(dst)])
            
            console.print("✅ Restore completed")
            return True
            
        except Exception as e:
            console.print(f"❌ Restore failed: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up the platform."""
        console.print(Panel.fit("🧹 Cleaning up platform", style="bold red"))
        
        if not Confirm.ask("Are you sure you want to clean up the platform? This will delete all resources."):
            console.print("Cleanup cancelled")
            return False
        
        try:
            if self.environment == "local":
                # Delete kind cluster
                console.print("🗑️ Deleting kind cluster...")
                self.bootstrap_manager.run_command([
                    "kind", "delete", "cluster", "--name", "devops-ai-platform"
                ], check=False)
            else:
                # Delete Kubernetes resources
                console.print("🗑️ Deleting Kubernetes resources...")
                self.bootstrap_manager.run_command([
                    "kubectl", "delete", "all", "--all", "--all-namespaces"
                ], check=False)
                
                # Delete namespaces
                self.bootstrap_manager.run_command([
                    "kubectl", "delete", "namespace", "argocd", "monitoring", "default"
                ], check=False)
            
            console.print("✅ Cleanup completed")
            return True
            
        except Exception as e:
            console.print(f"❌ Cleanup failed: {e}")
            return False


def main():
    """Main operator function."""
    parser = argparse.ArgumentParser(description="DevOps AI Platform Operator")
    parser.add_argument("command", choices=["deploy", "status", "logs", "scale", "backup", "restore", "cleanup"],
                       help="Command to execute")
    parser.add_argument("--env", choices=["local", "testing", "production", "gcp"], default="local",
                       help="Target environment")
    parser.add_argument("--skip-tests", action="store_true",
                       help="Skip running tests during deployment")
    parser.add_argument("--skip-build", action="store_true",
                       help="Skip building Docker image during deployment")
    parser.add_argument("--service", default="devops-ai-platform",
                       help="Service name for logs/scale commands")
    parser.add_argument("--namespace", default="default",
                       help="Namespace for logs/scale commands")
    parser.add_argument("--replicas", type=int, default=2,
                       help="Number of replicas for scale command")
    parser.add_argument("--backup-path", type=str,
                       help="Backup path for restore command")
    parser.add_argument("--lines", type=int, default=50,
                       help="Number of log lines to show")
    
    args = parser.parse_args()
    
    # Initialize operator
    operator = DevOpsAIOperator(args.env)
    
    # Execute command
    success = False
    
    if args.command == "deploy":
        success = operator.deploy(skip_tests=args.skip_tests, skip_build=args.skip_build)
    elif args.command == "status":
        success = operator.status()
    elif args.command == "logs":
        success = operator.logs(service=args.service, namespace=args.namespace, lines=args.lines)
    elif args.command == "scale":
        success = operator.scale(service=args.service, namespace=args.namespace, replicas=args.replicas)
    elif args.command == "backup":
        success = operator.backup()
    elif args.command == "restore":
        if not args.backup_path:
            console.print("❌ Backup path is required for restore command")
            sys.exit(1)
        success = operator.restore(args.backup_path)
    elif args.command == "cleanup":
        success = operator.cleanup()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()
