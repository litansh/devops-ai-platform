#!/bin/bash

set -e

echo "🚀 Setting up local DevOps AI Platform development environment..."

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check kind
    if ! command -v kind &> /dev/null; then
        print_warning "kind is not installed. Installing kind..."
        go install sigs.k8s.io/kind@latest
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        print_warning "helm is not installed. Installing helm..."
        curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
        sudo mv linux-amd64/helm /usr/local/bin/
    fi
    
    print_status "All prerequisites are satisfied!"
}

# Create local Kubernetes cluster
create_local_cluster() {
    print_status "Creating local Kubernetes cluster with kind..."
    
    # Create kind cluster
    kind create cluster --name devops-ai-platform --config - <<EOF
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
EOF
    
    print_status "Local Kubernetes cluster created successfully!"
}

# Install ArgoCD
install_argocd() {
    print_status "Installing ArgoCD..."
    
    # Create namespace
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
    
    # Install ArgoCD
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD to be ready
    print_status "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
    
    # Get ArgoCD admin password
    ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    print_status "ArgoCD admin password: $ARGOCD_PASSWORD"
    
    # Port forward ArgoCD UI
    print_status "Starting ArgoCD UI port forward..."
    kubectl port-forward svc/argocd-server -n argocd 8080:443 &
    ARGOCD_PID=$!
    echo $ARGOCD_PID > .argocd-pid
    
    print_status "ArgoCD UI available at: https://localhost:8080"
    print_status "Username: admin"
    print_status "Password: $ARGOCD_PASSWORD"
}

# Install monitoring stack
install_monitoring() {
    print_status "Installing monitoring stack..."
    
    # Add Prometheus Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install Prometheus and Grafana
    helm install monitoring prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set grafana.enabled=true \
        --set prometheus.enabled=true \
        --set alertmanager.enabled=true
    
    # Wait for monitoring to be ready
    print_status "Waiting for monitoring stack to be ready..."
    kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=300s
    
    # Get Grafana admin password
    GRAFANA_PASSWORD=$(kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d)
    print_status "Grafana admin password: $GRAFANA_PASSWORD"
    
    # Port forward Grafana
    print_status "Starting Grafana port forward..."
    kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80 &
    GRAFANA_PID=$!
    echo $GRAFANA_PID > .grafana-pid
    
    print_status "Grafana available at: http://localhost:3000"
    print_status "Username: admin"
    print_status "Password: $GRAFANA_PASSWORD"
}

# Setup local CI/CD
setup_local_cicd() {
    print_status "Setting up local CI/CD..."
    
    # Create local CI/CD namespace
    kubectl create namespace cicd --dry-run=client -o yaml | kubectl apply -f -
    
    # Install Tekton (for local CI/CD)
    kubectl apply -f https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
    
    # Wait for Tekton to be ready
    print_status "Waiting for Tekton to be ready..."
    kubectl wait --for=condition=ready pod -l app=tekton-pipelines-controller -n tekton-pipelines --timeout=300s
    
    print_status "Local CI/CD setup completed!"
}

# Build and deploy application
build_and_deploy() {
    print_status "Building and deploying application..."
    
    # Build Docker image
    docker build -t devops-ai-platform:local .
    
    # Load image into kind cluster
    kind load docker-image devops-ai-platform:local --name devops-ai-platform
    
    # Deploy application
    kubectl apply -f k8s/base/
    
    # Wait for application to be ready
    print_status "Waiting for application to be ready..."
    kubectl wait --for=condition=ready pod -l app=devops-ai-platform --timeout=300s
    
    # Port forward application
    print_status "Starting application port forward..."
    kubectl port-forward svc/devops-ai-platform 8000:8000 &
    APP_PID=$!
    echo $APP_PID > .app-pid
    
    print_status "Application available at: http://localhost:8000"
}

# Setup development environment
setup_dev_env() {
    print_status "Setting up development environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cp config.env.example .env
        print_warning "Created .env file from template. Please update with your configuration."
    fi
    
    # Install Python dependencies
    pip install -r requirements.txt
    
    # Run tests
    print_status "Running tests..."
    python -m pytest tests/ -v
    
    print_status "Development environment setup completed!"
}

# Main setup function
main() {
    print_status "Starting local DevOps AI Platform setup..."
    
    check_prerequisites
    create_local_cluster
    install_argocd
    install_monitoring
    setup_local_cicd
    setup_dev_env
    build_and_deploy
    
    print_status "🎉 Local DevOps AI Platform setup completed!"
    print_status ""
    print_status "Access URLs:"
    print_status "  - Application: http://localhost:8000"
    print_status "  - ArgoCD UI: https://localhost:8080"
    print_status "  - Grafana: http://localhost:3000"
    print_status ""
    print_status "To stop the services, run: ./scripts/local-cleanup.sh"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up local environment..."
    
    # Kill background processes
    if [ -f .argocd-pid ]; then
        kill $(cat .argocd-pid) 2>/dev/null || true
        rm .argocd-pid
    fi
    
    if [ -f .grafana-pid ]; then
        kill $(cat .grafana-pid) 2>/dev/null || true
        rm .grafana-pid
    fi
    
    if [ -f .app-pid ]; then
        kill $(cat .app-pid) 2>/dev/null || true
        rm .app-pid
    fi
    
    # Delete kind cluster
    kind delete cluster --name devops-ai-platform
    
    print_status "Local environment cleaned up!"
}

# Handle command line arguments
case "${1:-setup}" in
    setup)
        main
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {setup|cleanup}"
        exit 1
        ;;
esac
