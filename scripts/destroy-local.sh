#!/bin/bash

# DevOps AI Platform - Local Environment Destroyer
# This script completely destroys the local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  DevOps AI Platform - Local Environment"
echo "           DESTROY SCRIPT"
echo "=========================================="
echo ""

print_status "Starting local environment destruction..."

# Stop any running Python processes
print_status "Stopping Python processes..."
pkill -f "python main.py" || print_warning "No Python main.py processes found"
pkill -f "uvicorn" || print_warning "No uvicorn processes found"

# Stop React development server
print_status "Stopping React development server..."
pkill -f "react-scripts" || print_warning "No React development server found"
pkill -f "npm start" || print_warning "No npm start processes found"

# Stop Docker containers
print_status "Stopping Docker containers..."
docker stop $(docker ps -q --filter "name=devops-ai-platform") 2>/dev/null || print_warning "No devops-ai-platform containers found"
docker stop $(docker ps -q --filter "name=postgres") 2>/dev/null || print_warning "No postgres containers found"
docker stop $(docker ps -q --filter "name=redis") 2>/dev/null || print_warning "No redis containers found"
docker stop $(docker ps -q --filter "name=mongodb") 2>/dev/null || print_warning "No mongodb containers found"
docker stop $(docker ps -q --filter "name=grafana") 2>/dev/null || print_warning "No grafana containers found"
docker stop $(docker ps -q --filter "name=prometheus") 2>/dev/null || print_warning "No prometheus containers found"

# Remove Docker containers
print_status "Removing Docker containers..."
docker rm $(docker ps -aq --filter "name=devops-ai-platform") 2>/dev/null || print_warning "No devops-ai-platform containers to remove"
docker rm $(docker ps -aq --filter "name=postgres") 2>/dev/null || print_warning "No postgres containers to remove"
docker rm $(docker ps -aq --filter "name=redis") 2>/dev/null || print_warning "No redis containers to remove"
docker rm $(docker ps -aq --filter "name=mongodb") 2>/dev/null || print_warning "No mongodb containers to remove"
docker rm $(docker ps -aq --filter "name=grafana") 2>/dev/null || print_warning "No grafana containers to remove"
docker rm $(docker ps -aq --filter "name=prometheus") 2>/dev/null || print_warning "No prometheus containers to remove"

# Remove Docker images
print_status "Removing Docker images..."
docker rmi devops-ai-platform:latest 2>/dev/null || print_warning "No devops-ai-platform image found"
docker rmi postgres:15 2>/dev/null || print_warning "No postgres image found"
docker rmi redis:7-alpine 2>/dev/null || print_warning "No redis image found"
docker rmi mongo:6 2>/dev/null || print_warning "No mongo image found"
docker rmi grafana/grafana:latest 2>/dev/null || print_warning "No grafana image found"
docker rmi prom/prometheus:latest 2>/dev/null || print_warning "No prometheus image found"

# Delete Kind cluster
print_status "Deleting Kind cluster..."
kind delete cluster --name devops-ai-platform 2>/dev/null || print_warning "No Kind cluster found"

# Remove Docker volumes
print_status "Removing Docker volumes..."
docker volume rm devops-ai-platform-postgres-data 2>/dev/null || print_warning "No postgres volume found"
docker volume rm devops-ai-platform-redis-data 2>/dev/null || print_warning "No redis volume found"
docker volume rm devops-ai-platform-mongodb-data 2>/dev/null || print_warning "No mongodb volume found"
docker volume rm devops-ai-platform-grafana-data 2>/dev/null || print_warning "No grafana volume found"
docker volume rm devops-ai-platform-prometheus-data 2>/dev/null || print_warning "No prometheus volume found"

# Remove Docker networks
print_status "Removing Docker networks..."
docker network rm devops-ai-platform-network 2>/dev/null || print_warning "No devops-ai-platform network found"

# Clean up any remaining containers and images
print_status "Cleaning up remaining Docker resources..."
docker system prune -f --volumes 2>/dev/null || print_warning "No Docker resources to clean"

# Remove local files and directories
print_status "Removing local files and directories..."
rm -rf .env.local 2>/dev/null || print_warning "No .env.local file found"
rm -rf frontend/node_modules 2>/dev/null || print_warning "No frontend node_modules found"
rm -rf frontend/build 2>/dev/null || print_warning "No frontend build directory found"
rm -rf __pycache__ 2>/dev/null || print_warning "No Python cache found"
rm -rf .pytest_cache 2>/dev/null || print_warning "No pytest cache found"
rm -rf .coverage 2>/dev/null || print_warning "No coverage file found"

# Kill any processes using our ports
print_status "Killing processes using our ports..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || print_warning "No processes on port 8000"
lsof -ti:3000 | xargs kill -9 2>/dev/null || print_warning "No processes on port 3000"
lsof -ti:3001 | xargs kill -9 2>/dev/null || print_warning "No processes on port 3001"
lsof -ti:9091 | xargs kill -9 2>/dev/null || print_warning "No processes on port 9091"
lsof -ti:5432 | xargs kill -9 2>/dev/null || print_warning "No processes on port 5432"
lsof -ti:6379 | xargs kill -9 2>/dev/null || print_warning "No processes on port 6379"
lsof -ti:27017 | xargs kill -9 2>/dev/null || print_warning "No processes on port 27017"

# Remove any remaining temporary files
print_status "Cleaning up temporary files..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

print_success "Local environment destruction completed!"
echo ""
print_status "All local resources have been cleaned up:"
echo "  ✅ Python processes stopped"
echo "  ✅ React development server stopped"
echo "  ✅ Docker containers removed"
echo "  ✅ Docker images removed"
echo "  ✅ Kind cluster deleted"
echo "  ✅ Docker volumes removed"
echo "  ✅ Docker networks removed"
echo "  ✅ Port processes killed"
echo "  ✅ Temporary files cleaned"
echo ""
print_status "You can now run the bootstrap script to rebuild everything from scratch:"
echo "  ./scripts/bootstrap.py --env local"
echo ""
