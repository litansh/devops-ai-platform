#!/bin/bash

# DevOps AI Platform - Frontend Dashboard Startup Script

set -e

echo "🚀 Starting DevOps AI Platform Frontend Dashboard..."

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

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        print_status "Visit: https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js version 16+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) is installed"
}

# Check if npm is installed
check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    print_success "npm $(npm --version) is installed"
}

# Navigate to frontend directory
navigate_to_frontend() {
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found. Please run this script from the project root."
        exit 1
    fi
    
    cd frontend
    print_status "Navigated to frontend directory"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ -f "package-lock.json" ]; then
        npm ci
    else
        npm install
    fi
    
    print_success "Dependencies installed successfully"
}

# Check if backend is running
check_backend() {
    print_status "Checking backend connection..."
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend is running on http://localhost:8000"
    else
        print_warning "Backend is not running on http://localhost:8000"
        print_status "Please start the backend first: python main.py"
        print_status "The frontend will still start but may not connect to the backend"
    fi
}

# Create environment file if it doesn't exist
create_env_file() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
EOF
        print_success ".env file created"
    else
        print_status ".env file already exists"
    fi
}

# Start the development server
start_dev_server() {
    print_status "Starting development server..."
    print_status "Dashboard will be available at: http://localhost:3000"
    print_status "Press Ctrl+C to stop the server"
    
    npm start
}

# Main execution
main() {
    echo "=========================================="
    echo "  DevOps AI Platform - Frontend Dashboard"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_node
    check_npm
    
    # Navigate to frontend directory
    navigate_to_frontend
    
    # Install dependencies
    install_dependencies
    
    # Create environment file
    create_env_file
    
    # Check backend
    check_backend
    
    echo ""
    print_success "Frontend setup complete!"
    echo ""
    
    # Start development server
    start_dev_server
}

# Run main function
main "$@"
