#!/bin/bash

set -e

echo "🧹 Cleaning up local DevOps AI Platform environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Kill background processes
cleanup_processes() {
    print_status "Stopping background processes..."
    
    if [ -f .argocd-pid ]; then
        PID=$(cat .argocd-pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_status "Stopped ArgoCD port forward"
        fi
        rm .argocd-pid
    fi
    
    if [ -f .grafana-pid ]; then
        PID=$(cat .grafana-pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_status "Stopped Grafana port forward"
        fi
        rm .grafana-pid
    fi
    
    if [ -f .app-pid ]; then
        PID=$(cat .app-pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_status "Stopped application port forward"
        fi
        rm .app-pid
    fi
}

# Cleanup Kubernetes resources
cleanup_kubernetes() {
    print_status "Cleaning up Kubernetes resources..."
    
    # Delete application resources
    kubectl delete -f k8s/base/ --ignore-not-found=true || true
    
    # Delete monitoring stack
    helm uninstall monitoring -n monitoring --ignore-not-found=true || true
    kubectl delete namespace monitoring --ignore-not-found=true || true
    
    # Delete ArgoCD
    kubectl delete -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml --ignore-not-found=true || true
    kubectl delete namespace argocd --ignore-not-found=true || true
    
    # Delete Tekton
    kubectl delete -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml --ignore-not-found=true || true
    
    # Delete CI/CD namespace
    kubectl delete namespace cicd --ignore-not-found=true || true
}

# Delete kind cluster
delete_cluster() {
    print_status "Deleting local Kubernetes cluster..."
    
    if kind get clusters | grep -q devops-ai-platform; then
        kind delete cluster --name devops-ai-platform
        print_status "Local Kubernetes cluster deleted"
    else
        print_warning "Local Kubernetes cluster not found"
    fi
}

# Cleanup Docker resources
cleanup_docker() {
    print_status "Cleaning up Docker resources..."
    
    # Remove local Docker images
    docker rmi devops-ai-platform:local --force 2>/dev/null || true
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
}

# Cleanup local files
cleanup_files() {
    print_status "Cleaning up local files..."
    
    # Remove PID files
    rm -f .argocd-pid .grafana-pid .app-pid
    
    # Remove temporary files
    rm -rf .pytest_cache/
    rm -rf __pycache__/
    rm -rf */__pycache__/
    rm -rf .coverage
    rm -rf htmlcov/
    
    # Remove logs
    rm -rf logs/
    
    print_status "Local files cleaned up"
}

# Main cleanup function
main() {
    print_status "Starting cleanup process..."
    
    cleanup_processes
    cleanup_kubernetes
    delete_cluster
    cleanup_docker
    cleanup_files
    
    print_status "🎉 Local DevOps AI Platform environment cleaned up successfully!"
}

# Run cleanup
main
