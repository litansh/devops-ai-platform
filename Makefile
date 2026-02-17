.PHONY: help install test lint format run-local run-frontend clean docker-build docker-run setup-local cleanup-local

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "DevOps AI Platform - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install Python dependencies
	pip install -r requirements.txt

install-dev: ## Install dev dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black pylint

test: ## Run tests
	pytest tests/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

lint: ## Run linters
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

format: ## Format code with Black
	black .

format-check: ## Check code formatting
	black --check .

run-local: ## Start local kind cluster with full stack
	./scripts/local-setup.sh

cleanup-local: ## Clean up local kind cluster
	./scripts/local-cleanup.sh

run-frontend: ## Start React dashboard (development)
	cd frontend && npm install && npm start

run-api: ## Start FastAPI backend (development)
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker build -t devops-ai-platform:latest .

docker-run: ## Run Docker container
	docker run -d -p 8000:8000 --name devops-ai-platform devops-ai-platform:latest

docker-stop: ## Stop Docker container
	docker stop devops-ai-platform || true
	docker rm devops-ai-platform || true

compose-up: ## Start all services with docker-compose
	docker-compose up -d

compose-down: ## Stop all services
	docker-compose down

compose-logs: ## View docker-compose logs
	docker-compose logs -f

terraform-init: ## Initialize Terraform
	cd terraform && terraform init

terraform-plan: ## Run Terraform plan
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	cd terraform && terraform apply

terraform-destroy: ## Destroy Terraform infrastructure
	cd terraform && terraform destroy

k8s-deploy-dev: ## Deploy to dev environment
	kubectl apply -k k8s/base

k8s-deploy-prod: ## Deploy to prod environment
	kubectl apply -f k8s/argocd/applications/prod-application.yaml

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods,svc,deploy -n devops-ai-platform

argocd-install: ## Install ArgoCD in local cluster
	kubectl create namespace argocd || true
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

argocd-password: ## Get ArgoCD admin password
	kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

prometheus-port-forward: ## Forward Prometheus port
	kubectl port-forward -n monitoring svc/prometheus 9090:9090

grafana-port-forward: ## Forward Grafana port
	kubectl port-forward -n monitoring svc/grafana 3001:3000

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

all: install lint test ## Run install, lint, and test

quickstart: ## Quick start for new users (local setup + frontend)
	@echo "🚀 Starting DevOps AI Platform..."
	@echo "Step 1/2: Setting up local infrastructure..."
	./scripts/local-setup.sh
	@echo ""
	@echo "Step 2/2: Starting frontend dashboard..."
	@echo "Run in a new terminal: make run-frontend"
	@echo ""
	@echo "✅ Setup complete!"
	@echo "Access the dashboard at: http://localhost:3000"
	@echo "Access the API at: http://localhost:8000"
