#!/usr/bin/env python3
"""
DevOps AI Platform Bootstrap Script

This script provides a unified way to deploy the DevOps AI Platform to any environment:
- Local development with kind cluster
- AWS EKS cluster
- GCP GKE cluster (future)
- Production environments

Usage:
    python scripts/bootstrap.py --env local
    python scripts/bootstrap.py --env eks --region us-west-2
    python scripts/bootstrap.py --env gcp --project my-project
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class BootstrapManager:
    """Manages the bootstrap process for different environments."""
    
    def __init__(self, environment: str, config: Dict):
        self.environment = environment
        self.config = config
        self.project_root = Path(__file__).parent.parent
        
    def run_command(self, command: List[str], cwd: Optional[Path] = None, check: bool = True, ignore_errors: bool = False) -> subprocess.CompletedProcess:
        """Run a shell command with proper error handling."""
        cwd = cwd or self.project_root
        console.print(f"🔄 Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                console.print(f"✅ Output: {result.stdout}")
            return result
        except subprocess.CalledProcessError as e:
            if ignore_errors:
                console.print(f"⚠️ Command failed (ignored): {e.stderr}")
                return e
            else:
                console.print(f"❌ Error: {e.stderr}")
                if check:
                    raise
                return e
    
    def check_prerequisites(self) -> bool:
        """Check if all required tools are installed."""
        console.print("🔍 Checking prerequisites...")
        
        tools = {
            "docker": ["docker", "--version"],
            "kubectl": ["kubectl", "version", "--client"],
            "helm": ["helm", "version"],
            "terraform": ["terraform", "version"],
        }
        
        if self.environment == "local":
            tools["kind"] = ["kind", "version"]
        
        missing_tools = []
        
        for tool, command in tools.items():
            try:
                self.run_command(command, check=False)
                console.print(f"✅ {tool} is installed")
            except FileNotFoundError:
                missing_tools.append(tool)
                console.print(f"❌ {tool} is not installed")
        
        if missing_tools:
            console.print(f"❌ Missing tools: {', '.join(missing_tools)}")
            console.print("Please install the missing tools and try again.")
            return False
        
        return True
    
    def setup_environment_config(self) -> bool:
        """Setup environment-specific configuration."""
        console.print("⚙️ Setting up environment configuration...")
        
        # Create .env file if it doesn't exist
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_example = self.project_root / "config.env.example"
            if env_example.exists():
                self.run_command(["cp", str(env_example), str(env_file)])
                console.print("📝 Created .env file from template")
                console.print("⚠️ Please edit .env file with your configuration before continuing")
                return False
        
        return True
    
    def deploy_local_environment(self) -> bool:
        """Deploy to local environment using kind."""
        console.print("🏠 Deploying to local environment...")
        
        # Check if kind cluster already exists
        try:
            result = self.run_command(["kind", "get", "clusters"], check=False)
            if "devops-ai-platform" in result.stdout:
                if not Confirm.ask("Kind cluster 'devops-ai-platform' already exists. Delete and recreate?"):
                    console.print("Using existing cluster")
                    # Skip cluster creation
                    cluster_exists = True
                else:
                    self.run_command(["kind", "delete", "cluster", "--name", "devops-ai-platform"])
                    cluster_exists = False
            else:
                cluster_exists = False
        except:
            cluster_exists = False
        
        # Create kind cluster if it doesn't exist
        if not cluster_exists:
            console.print("📦 Creating kind cluster...")
            kind_config = """
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
- role: worker
- role: worker
"""
            
            with open("/tmp/kind-config.yaml", "w") as f:
                f.write(kind_config)
            
            self.run_command(["kind", "create", "cluster", "--name", "devops-ai-platform", "--config", "/tmp/kind-config.yaml"])
        else:
            console.print("📦 Using existing kind cluster...")
        
        # Install ArgoCD
        console.print("🚀 Installing ArgoCD...")
        self.run_command(["kubectl", "create", "namespace", "argocd"])
        self.run_command([
            "kubectl", "apply", "-n", "argocd", 
            "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
        ])
        
        # Wait for ArgoCD to be ready
        console.print("⏳ Waiting for ArgoCD to be ready...")
        self.run_command([
            "kubectl", "wait", "--for=condition=ready", "pod", 
            "-l", "app.kubernetes.io/name=argocd-server", 
            "-n", "argocd", "--timeout=300s"
        ])
        
        # Install monitoring stack
        console.print("📊 Installing monitoring stack...")
        self.run_command(["helm", "repo", "add", "prometheus-community", "https://prometheus-community.github.io/helm-charts"])
        self.run_command(["helm", "repo", "update"])
        self.run_command([
            "helm", "install", "monitoring", "prometheus-community/kube-prometheus-stack",
            "--namespace", "monitoring", "--create-namespace",
            "--set", "grafana.enabled=true",
            "--set", "prometheus.enabled=true",
            "--set", "alertmanager.enabled=true"
        ])
        
        # Apply Grafana configuration
        console.print("📈 Configuring Grafana...")
        self.run_command(["kubectl", "apply", "-f", "k8s/base/grafana-configmap.yaml"])
        
        # Deploy application
        console.print("🚀 Deploying application...")
        self.run_command(["kubectl", "apply", "-f", "k8s/base/deployment-simple.yaml"])
        
        # Setup port forwarding
        console.print("🔗 Setting up port forwarding...")
        self._setup_port_forwarding()
        
        return True
    
    def deploy_testing_environment(self) -> bool:
        """Deploy to AWS testing environment using Terraform."""
        console.print("🧪 Deploying to AWS testing environment...")
        return self._deploy_aws_environment("testing")
    
    def deploy_production_environment(self) -> bool:
        """Deploy to AWS production environment using Terraform."""
        console.print("🚀 Deploying to AWS production environment...")
        return self._deploy_aws_environment("production")
    
    def _deploy_aws_environment(self, environment: str) -> bool:
        """Deploy to AWS environment using Terraform."""
        # Check AWS credentials
        try:
            self.run_command(["aws", "sts", "get-caller-identity"])
        except subprocess.CalledProcessError:
            console.print("❌ AWS credentials not configured. Please run 'aws configure' first.")
            return False
        
        # Deploy infrastructure with Terraform
        console.print(f"🏗️ Deploying {environment} infrastructure with Terraform...")
        terraform_dir = self.project_root / "terraform"
        
        # Set Terraform workspace
        self.run_command(["terraform", "workspace", "select", environment], cwd=terraform_dir)
        
        # Initialize Terraform
        self.run_command(["terraform", "init"], cwd=terraform_dir)
        
        # Plan Terraform changes
        self.run_command(["terraform", "plan", "-var", f"environment={environment}"], cwd=terraform_dir)
        
        if Confirm.ask(f"Apply Terraform changes to {environment}?"):
            self.run_command(["terraform", "apply", "-auto-approve", "-var", f"environment={environment}"], cwd=terraform_dir)
        
        # Get EKS cluster info
        cluster_name = self.config.get("cluster_name", f"devops-ai-platform-{environment}")
        region = self.config.get("aws_region", "us-west-2")
        
        self.run_command([
            "aws", "eks", "update-kubeconfig", 
            "--region", region, 
            "--name", cluster_name
        ])
        
        # Install ArgoCD
        console.print("🚀 Installing ArgoCD...")
        self.run_command(["kubectl", "create", "namespace", "argocd"], ignore_errors=True)
        self.run_command([
            "kubectl", "apply", "-n", "argocd", 
            "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
        ])
        
        # Install monitoring stack
        console.print("📊 Installing monitoring stack...")
        self.run_command(["helm", "repo", "add", "prometheus-community", "https://prometheus-community.github.io/helm-charts"])
        self.run_command(["helm", "repo", "update"])
        self.run_command([
            "helm", "install", "monitoring", "prometheus-community/kube-prometheus-stack",
            "--namespace", "monitoring", "--create-namespace",
            "--set", "grafana.enabled=true",
            "--set", "prometheus.enabled=true",
            "--set", "alertmanager.enabled=true"
        ])
        
        # Apply Grafana configuration
        console.print("📈 Configuring Grafana...")
        self.run_command(["kubectl", "apply", "-f", "k8s/base/grafana-configmap.yaml"])
        
        # Deploy ArgoCD applications
        console.print("🔄 Deploying ArgoCD applications...")
        self.run_command(["kubectl", "apply", "-f", "k8s/argocd/applications/"])
        
        return True
    
    def deploy_gcp_environment(self) -> bool:
        """Deploy to GCP GKE environment (future implementation)."""
        console.print("☁️ GCP deployment not yet implemented")
        console.print("This will be available in a future version")
        return False
    
    def _setup_port_forwarding(self):
        """Setup port forwarding for local development."""
        console.print("🔗 Setting up port forwarding...")
        
        # Start port forwarding in background
        port_forwards = [
            ("argocd-server", "argocd", 8080, 443),
            ("monitoring-grafana", "monitoring", 3000, 80),
            ("devops-ai-platform", "default", 8000, 8000),
        ]
        
        for service, namespace, local_port, remote_port in port_forwards:
            try:
                subprocess.Popen([
                    "kubectl", "port-forward", 
                    f"svc/{service}", 
                    f"{local_port}:{remote_port}", 
                    "-n", namespace
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                console.print(f"✅ Port forward {service}:{local_port}:{remote_port}")
            except Exception as e:
                console.print(f"⚠️ Failed to setup port forward for {service}: {e}")
    
    def run_tests(self) -> bool:
        """Run the test suite."""
        console.print("🧪 Running tests...")
        
        try:
            self.run_command(["python", "-m", "pytest", "tests/", "-v", "--tb=short"])
            console.print("✅ Tests passed")
            return True
        except subprocess.CalledProcessError:
            console.print("❌ Tests failed")
            return False
    
    def build_and_push_image(self) -> bool:
        """Build and push Docker image."""
        console.print("🐳 Building and pushing Docker image...")
        
        image_name = self.config.get("image_name", "devops-ai-platform")
        registry = self.config.get("registry", "ghcr.io")
        
        # Build image
        self.run_command(["docker", "build", "-t", f"{registry}/{image_name}:latest", "."])
        
        # Push image (if registry is configured)
        if registry != "local":
            try:
                self.run_command(["docker", "push", f"{registry}/{image_name}:latest"])
                console.print("✅ Image pushed successfully")
            except subprocess.CalledProcessError:
                console.print("⚠️ Failed to push image (this is OK for local development)")
        
        return True
    
    def show_status(self):
        """Show deployment status and access information."""
        console.print("\n" + "="*60)
        console.print("🎉 DEPLOYMENT COMPLETE!")
        console.print("="*60)
        
        if self.environment == "local":
            console.print("""
🌐 Access URLs:
   • Application: http://localhost:8000
   • ArgoCD UI: https://localhost:8080 (admin/admin)
   • Grafana: http://localhost:3000 (admin/admin)

📋 Next Steps:
   1. Configure your bot tokens in .env file
   2. Test the application endpoints
   3. Import Grafana dashboards
   4. Configure monitoring alerts
""")
        else:
            console.print("""
🌐 Access URLs:
   • ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443
   • Grafana: kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
   • Application: kubectl port-forward svc/devops-ai-platform 8000:8000

📋 Next Steps:
   1. Configure your bot tokens in Kubernetes secrets
   2. Set up SSL/TLS certificates
   3. Configure monitoring alerts
   4. Test the application endpoints
""")
        
        console.print("📚 Documentation: README.md")
        console.print("🔧 Troubleshooting: DEPLOYMENT.md")
        console.print("="*60)


def load_config(environment: str) -> Dict:
    """Load environment-specific configuration."""
    config_file = Path(__file__).parent / "bootstrap-config.yaml"
    
    if config_file.exists():
        with open(config_file) as f:
            configs = yaml.safe_load(f)
            return configs.get(environment, {})
    
    # Default configurations
    defaults = {
        "local": {
            "cluster_name": "devops-ai-platform",
            "registry": "local",
            "monitoring": True,
        },
        "eks": {
            "cluster_name": "devops-ai-platform-prod",
            "aws_region": "us-west-2",
            "registry": "ghcr.io",
            "monitoring": True,
        },
        "gcp": {
            "cluster_name": "devops-ai-platform-gcp",
            "gcp_project": "your-project",
            "gcp_region": "us-central1",
            "registry": "gcr.io",
            "monitoring": True,
        }
    }
    
    return defaults.get(environment, {})


def main():
    """Main bootstrap function."""
    parser = argparse.ArgumentParser(description="DevOps AI Platform Bootstrap")
    parser.add_argument("--env", choices=["local", "testing", "production", "gcp"], default="local", 
                       help="Target environment")
    parser.add_argument("--skip-tests", action="store_true", 
                       help="Skip running tests")
    parser.add_argument("--skip-build", action="store_true", 
                       help="Skip building Docker image")
    parser.add_argument("--config", type=str, 
                       help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.env)
    
    # Override with command line config if provided
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config.update(yaml.safe_load(f))
    
    console.print(Panel.fit(
        f"🚀 DevOps AI Platform Bootstrap\n"
        f"Environment: {args.env}\n"
        f"Configuration: {json.dumps(config, indent=2)}",
        title="Bootstrap Configuration"
    ))
    
    # Initialize bootstrap manager
    manager = BootstrapManager(args.env, config)
    
    try:
        # Check prerequisites
        if not manager.check_prerequisites():
            console.print("❌ Prerequisites check failed")
            sys.exit(1)
        
        # Setup environment configuration
        if not manager.setup_environment_config():
            console.print("⚠️ Please configure your .env file and run again")
            sys.exit(1)
        
        # Run tests (unless skipped)
        if not args.skip_tests:
            if not manager.run_tests():
                if not Confirm.ask("Tests failed. Continue anyway?"):
                    sys.exit(1)
        
        # Build and push image (unless skipped)
        if not args.skip_build:
            manager.build_and_push_image()
        
        # Deploy based on environment
        success = False
        if args.env == "local":
            success = manager.deploy_local_environment()
        elif args.env == "testing":
            success = manager.deploy_testing_environment()
        elif args.env == "production":
            success = manager.deploy_production_environment()
        elif args.env == "gcp":
            success = manager.deploy_gcp_environment()
        
        if success:
            manager.show_status()
        else:
            console.print("❌ Deployment failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n⚠️ Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Bootstrap failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
