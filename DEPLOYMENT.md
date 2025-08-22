# 🚀 DevOps AI Platform - Deployment Guide

This guide covers deployment options for the DevOps AI Platform, including local development, cloud deployment, and production setup.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Cloud Deployment](#cloud-deployment)
- [Production Setup](#production-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Tools
- **Docker & Docker Compose**: For containerization
- **kubectl**: Kubernetes command-line tool
- **helm**: Kubernetes package manager
- **terraform**: Infrastructure as Code
- **git**: Version control

### Optional Tools (for local development)
- **kind**: Local Kubernetes cluster
- **minikube**: Alternative local Kubernetes
- **atlantis**: Terraform automation

### Cloud Prerequisites
- **AWS Account**: For production deployment
- **AWS CLI**: Configured with appropriate credentials
- **Domain Name**: For production (optional)

## 🏠 Local Development Setup

### Quick Start (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/devops-ai-platform.git
   cd devops-ai-platform
   ```

2. **Run the local setup script**:
   ```bash
   ./scripts/local-setup.sh
   ```

   This script will:
   - Create a local Kubernetes cluster with kind
   - Install ArgoCD for GitOps
   - Install monitoring stack (Prometheus + Grafana)
   - Setup local CI/CD with Tekton
   - Build and deploy the application
   - Configure port forwarding for all services

3. **Access the services**:
   - **Application**: http://localhost:8000
   - **ArgoCD UI**: https://localhost:8080 (admin/admin)
   - **Grafana**: http://localhost:3000 (admin/admin)

4. **Cleanup when done**:
   ```bash
   ./scripts/local-cleanup.sh
   ```

### Manual Local Setup

If you prefer manual setup:

1. **Setup environment**:
   ```bash
   cp config.env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

4. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## ☁️ Cloud Deployment

### AWS Infrastructure Setup

1. **Initialize Terraform**:
   ```bash
   cd terraform
   terraform init
   ```

2. **Configure variables**:
   ```bash
   # Create terraform.tfvars
   cat > terraform.tfvars <<EOF
   aws_region = "us-west-2"
   environment = "prod"
   project_name = "devops-ai-platform"
   domain_name = "your-domain.com"
   EOF
   ```

3. **Plan and apply infrastructure**:
   ```bash
   terraform plan
   terraform apply
   ```

4. **Configure kubectl for EKS**:
   ```bash
   aws eks update-kubeconfig --region us-west-2 --name devops-ai-platform-prod
   ```

### Install ArgoCD on EKS

1. **Install ArgoCD**:
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

2. **Get ArgoCD admin password**:
   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

3. **Port forward ArgoCD UI**:
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

4. **Create ArgoCD applications**:
   ```bash
   kubectl apply -f k8s/argocd/applications/
   ```

### Install Monitoring Stack

1. **Add Helm repositories**:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   ```

2. **Install Prometheus + Grafana**:
   ```bash
   helm install monitoring prometheus-community/kube-prometheus-stack \
     --namespace monitoring \
     --create-namespace \
     --set grafana.enabled=true \
     --set prometheus.enabled=true \
     --set alertmanager.enabled=true
   ```

3. **Import Grafana dashboards**:
   ```bash
   # Import the provided dashboard JSON files
   kubectl apply -f monitoring/grafana/dashboards/
   ```

## 🏭 Production Setup

### High Availability Configuration

1. **Multi-AZ EKS Cluster**:
   ```hcl
   # In terraform/main.tf
   eks_managed_node_groups = {
     general = {
       desired_capacity = 3
       max_capacity     = 10
       min_capacity     = 2
       instance_types   = ["t3.medium"]
       capacity_type    = "ON_DEMAND"
     }
   }
   ```

2. **Database High Availability**:
   ```hcl
   # RDS with Multi-AZ
   module "rds" {
     multi_az = true
     backup_retention_period = 30
     deletion_protection = true
   }
   ```

3. **Redis Cluster**:
   ```hcl
   # ElastiCache with replication
   resource "aws_elasticache_replication_group" "redis" {
     automatic_failover_enabled = true
     num_cache_clusters         = 2
   }
   ```

### Security Configuration

1. **Network Security**:
   - VPC with private subnets
   - Security groups limiting access
   - Network ACLs

2. **IAM Roles and Policies**:
   - Least privilege access
   - Service accounts for pods
   - Cross-account access if needed

3. **Secrets Management**:
   ```bash
   # Store secrets in AWS Secrets Manager
   aws secretsmanager create-secret \
     --name devops-ai-platform/prod \
     --description "DevOps AI Platform Production Secrets" \
     --secret-string '{"database_url":"...","redis_url":"..."}'
   ```

### SSL/TLS Configuration

1. **Request SSL Certificate**:
   ```bash
   aws acm request-certificate \
     --domain-name your-domain.com \
     --validation-method DNS
   ```

2. **Configure Ingress with SSL**:
   ```yaml
   # In k8s/base/ingress.yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt-prod
   spec:
     tls:
     - hosts:
       - your-domain.com
       secretName: devops-ai-platform-tls
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline is configured in `.github/workflows/ci-cd.yml` and includes:

1. **Testing Phase**:
   - Unit tests with pytest
   - Code coverage reporting
   - Linting with flake8, black, mypy
   - Security scanning with Trivy

2. **Build Phase**:
   - Docker image building
   - Container registry push
   - Image vulnerability scanning

3. **Deploy Phase**:
   - Development deployment (develop branch)
   - Production deployment (main branch)
   - Infrastructure deployment with Terraform

### ArgoCD GitOps

1. **Application Configuration**:
   - `k8s/argocd/applications/dev-application.yaml`
   - `k8s/argocd/applications/prod-application.yaml`

2. **Kustomize Overlays**:
   - `k8s/overlays/dev/` - Development configuration
   - `k8s/overlays/prod/` - Production configuration

3. **Automated Sync**:
   - ArgoCD automatically syncs when Git changes
   - Self-healing capabilities
   - Rollback functionality

### Atlantis for Terraform

1. **Installation**:
   ```bash
   # Deploy Atlantis to Kubernetes
   kubectl apply -f https://raw.githubusercontent.com/runatlantis/atlantis/master/k8s/atlantis.yaml
   ```

2. **Configuration**:
   - `atlantis.yaml` defines projects and workflows
   - Automated plan on PR creation
   - Manual apply with approval

## 📊 Monitoring & Observability

### Grafana Dashboards

Three main dashboards are provided:

1. **Platform Overview** (`monitoring/grafana/dashboards/devops-ai-platform-overview.json`):
   - Platform health status
   - Request rates and response times
   - Error rates and success metrics
   - Resource usage

2. **Agents Dashboard** (`monitoring/grafana/dashboards/agents-dashboard.json`):
   - Agent execution metrics
   - Success rates and error tracking
   - Performance metrics by agent type
   - Resource usage per agent

3. **Infrastructure Dashboard** (`monitoring/grafana/dashboards/infrastructure-dashboard.json`):
   - EKS cluster status
   - Database metrics (RDS, Redis, MongoDB)
   - AWS resource monitoring
   - Cost tracking

### Alerting Configuration

1. **Prometheus Alert Rules**:
   ```yaml
   # monitoring/prometheus/alerts.yaml
   groups:
   - name: devops-ai-platform
     rules:
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
       for: 2m
       labels:
         severity: critical
       annotations:
         summary: High error rate detected
   ```

2. **AlertManager Configuration**:
   ```yaml
   # monitoring/alertmanager/config.yaml
   route:
     group_by: ['alertname']
     group_wait: 30s
     group_interval: 5m
     repeat_interval: 12h
     receiver: 'slack-notifications'
   ```

### Logging

1. **Structured Logging**:
   - JSON format logs
   - Correlation IDs
   - Log levels and context

2. **Log Aggregation**:
   - Fluentd for log collection
   - Elasticsearch for storage
   - Kibana for visualization

## 🔧 Troubleshooting

### Common Issues

1. **ArgoCD Sync Issues**:
   ```bash
   # Check application status
   kubectl get applications -n argocd
   
   # Check sync status
   kubectl describe application devops-ai-platform-prod -n argocd
   
   # Force sync
   kubectl patch application devops-ai-platform-prod -n argocd --type='merge' -p='{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}'
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database connectivity
   kubectl exec -it deployment/devops-ai-platform -- nc -zv <db-host> <db-port>
   
   # Check database logs
   kubectl logs -l app=devops-ai-platform -c devops-ai-platform
   ```

3. **Monitoring Issues**:
   ```bash
   # Check Prometheus targets
   kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring
   
   # Check Grafana connectivity
   kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
   ```

### Performance Optimization

1. **Resource Limits**:
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "250m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

2. **Horizontal Pod Autoscaling**:
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   spec:
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

3. **Database Optimization**:
   - Connection pooling
   - Query optimization
   - Index management

### Backup and Recovery

1. **Database Backups**:
   ```bash
   # RDS automated backups
   aws rds describe-db-instances --db-instance-identifier devops-ai-platform-prod
   
   # Manual backup
   kubectl exec -it deployment/devops-ai-platform -- pg_dump $DATABASE_URL > backup.sql
   ```

2. **Configuration Backups**:
   ```bash
   # Backup Kubernetes resources
   kubectl get all -o yaml > k8s-backup.yaml
   
   # Backup Terraform state
   terraform state pull > terraform-state.json
   ```

## 📚 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/)

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs and monitoring dashboards
3. Create an issue in the GitHub repository
4. Contact the development team
