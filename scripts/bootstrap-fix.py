#!/usr/bin/env python3
"""
Simple test script to verify the DevOps AI Platform deployment works.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result."""
    cwd = cwd or Path.cwd()
    print(f"🔄 Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        if result.stderr and result.returncode != 0:
            print(f"⚠️ Warning: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Test the deployment."""
    print("🧪 Testing DevOps AI Platform Deployment")
    print("=" * 50)
    
    # Check if kind cluster exists
    if not run_command(["kind", "get", "clusters"]):
        print("❌ Kind cluster not found")
        return False
    
    # Check if kubectl is connected
    if not run_command(["kubectl", "cluster-info"]):
        print("❌ Not connected to cluster")
        return False
    
    # Check if ArgoCD namespace exists
    if not run_command(["kubectl", "get", "namespace", "argocd"]):
        print("⚠️ ArgoCD namespace not found, creating...")
        run_command(["kubectl", "create", "namespace", "argocd"])
    
    # Check if monitoring namespace exists
    if not run_command(["kubectl", "get", "namespace", "monitoring"]):
        print("⚠️ Monitoring namespace not found, creating...")
        run_command(["kubectl", "create", "namespace", "monitoring"])
    
    # Deploy the application
    print("🚀 Deploying application...")
    if run_command(["kubectl", "apply", "-f", "k8s/base/deployment-simple.yaml"]):
        print("✅ Application deployed successfully")
    else:
        print("❌ Application deployment failed")
        return False
    
    # Check pod status
    print("📊 Checking pod status...")
    run_command(["kubectl", "get", "pods", "--all-namespaces"])
    
    # Check service status
    print("🌐 Checking service status...")
    run_command(["kubectl", "get", "services", "--all-namespaces"])
    
    print("🎉 Deployment test completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
