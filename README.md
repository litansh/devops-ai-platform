# DevOps AI Platform

**Autonomous infrastructure management powered by 12 AI agents with human-in-the-loop safety.**

---

## 🎯 Why It Exists

**Problem:** DevOps teams spend 60-80% of their time on reactive operations—manual scaling, cost overruns, incident response, and repetitive maintenance tasks. Traditional automation is brittle and requires constant tuning.

**Solution:** AI agents that predict infrastructure needs, detect anomalies, optimize costs, and propose changes via pull requests—all while keeping humans in control through a bot-driven approval workflow.

---

## 🚀 What It Does

- **Predictive Scaling:** BurstPredictor and AutoScalerAdvisor analyze traffic patterns and recommend HPA configurations before traffic spikes hit
- **Cost Optimization:** CostWatcher identifies waste (idle resources, oversized instances) and proposes right-sizing changes saving 30%+ on cloud spend
- **Anomaly Detection:** AnomalyDetector monitors metrics and alerts on deviations before they become incidents
- **Automated Maintenance:** PatchUpdater, DiskCleaner, PodRestarter, and DBMaintainer handle routine operations
- **Security Response:** SecurityResponder triages alerts and suggests remediation
- **Interactive Control:** Telegram/Slack bot interface for real-time analysis and approvals (`/status`, `/cost`, `/approve pr-123`)
- **Full Observability:** Prometheus + Grafana + AlertManager with 3 pre-built dashboards
- **GitOps Safety:** All infrastructure changes go through GitHub PRs with rollback triggers on performance degradation

---

## 🏗️ Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│  User Interface                                         │
│  ├─ Telegram Bot (interactive commands)                │
│  ├─ Slack Bot (team notifications)                     │
│  └─ React Dashboard (visual monitoring)                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Bot Gateway & Approval Engine                         │
│  ├─ Command routing and parsing                        │
│  ├─ PR-based approval workflow                         │
│  └─ Risk assessment and rollback triggers              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  AI Agent Layer (12 MCP Agents)                        │
│  ├─ BurstPredictor (traffic forecasting)               │
│  ├─ AutoScalerAdvisor (HPA optimization)               │
│  ├─ CostWatcher (spend analysis)                       │
│  ├─ AnomalyDetector (deviation detection)              │
│  ├─ BottleneckScanner (performance analysis)           │
│  ├─ CapacityPlanner (resource forecasting)             │
│  ├─ SecurityResponder (incident triage)                │
│  ├─ LoadShifter (traffic distribution)                 │
│  ├─ PatchUpdater (security patching)                   │
│  ├─ DiskCleaner (storage optimization)                 │
│  ├─ PodRestarter (health management)                   │
│  └─ DBMaintainer (database ops)                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Infrastructure Layer                                   │
│  ├─ Kubernetes (EKS) - orchestration                   │
│  ├─ Terraform - IaC provisioning                       │
│  ├─ ArgoCD - GitOps deployments                        │
│  ├─ Prometheus - metrics collection                    │
│  └─ AWS Services (EC2, RDS, S3, Lambda)                │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Agents analyze** infrastructure metrics every 5 minutes
2. **Issues detected** → Agent opens GitHub PR with proposed fix
3. **Bot notifies** → Telegram/Slack message with `/approve` command
4. **Human reviews** → Approves or rejects via bot
5. **Auto-deploy** → ArgoCD applies changes if approved
6. **Monitoring** → Rollback triggered if performance degrades

---

## 🏃 Quickstart

### Option 1: Local Development (Recommended)

**One-command setup** with local kind cluster:

```bash
git clone https://github.com/litansh/devops-ai-platform.git
cd devops-ai-platform
./scripts/local-setup.sh
```

**Includes:**
- kind cluster with Kubernetes v1.28
- ArgoCD with GitOps automation
- Prometheus + Grafana monitoring stack
- Sample workloads for agent testing

**Access:**
- API: http://localhost:8000
- Grafana: http://localhost:3001 (admin/admin)
- ArgoCD: https://localhost:8080 (admin/admin)
- Prometheus: http://localhost:9090

**Time:** < 5 minutes

---

### Option 2: Docker Compose (Fastest)

**All services in containers** (no Kubernetes required):

```bash
git clone https://github.com/litansh/devops-ai-platform.git
cd devops-ai-platform

# Copy and configure environment
cp config.env.example .env
# Edit .env with your API keys (OpenAI, Telegram, etc.)

# Start all services
docker-compose up -d
```

**Includes:**
- FastAPI backend (port 8000)
- PostgreSQL, Redis, MongoDB
- Prometheus (port 9090)
- Grafana (port 3001)
- AlertManager (port 9093)

**Time:** < 2 minutes

---

### Option 3: Production AWS Deployment

**Full Terraform deployment** to AWS EKS:

```bash
cd terraform
terraform init
terraform plan
terraform apply

# Deploy applications via ArgoCD
kubectl apply -f k8s/argocd/applications/prod-application.yaml
```

**See:** `DEPLOYMENT.md` for detailed production setup

---

## ⚙️ Configuration

### Environment Variables

Create `.env` from `config.env.example`:

```bash
# Required: Platform basics
PLATFORM_ENV=development          # development|staging|production
LOG_LEVEL=INFO                    # DEBUG|INFO|WARN|ERROR

# Required: Cloud credentials (at least one)
AWS_ACCESS_KEY_ID=xxx             # AWS access key
AWS_SECRET_ACCESS_KEY=xxx         # AWS secret key
AWS_REGION=us-west-2              # AWS region

# Required: AI/ML APIs (choose provider)
OPENAI_API_KEY=sk-xxx             # OpenAI for embeddings and LLM
MODEL_PROVIDER=openai             # openai|anthropic

# Optional: Bot interfaces
TELEGRAM_BOT_TOKEN=123:xxx        # Get from @BotFather
TELEGRAM_CHAT_ID=123456789        # Your Telegram user ID
SLACK_BOT_TOKEN=xoxb-xxx          # Slack bot token
SLACK_SIGNING_SECRET=xxx          # Slack signing secret

# Optional: Databases (auto-configured in docker-compose)
DATABASE_URL=postgresql://user:pass@localhost:5432/devops
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/devops

# Optional: GitHub integration (for PR workflow)
GITHUB_TOKEN=ghp_xxx              # GitHub personal access token
GITHUB_REPO=your-org/your-repo    # Target repo for PRs

# Optional: Cost alerts
AWS_COST_ALERT_THRESHOLD=100      # Daily cost alert threshold (USD)
BUDGET_ALERT_EMAIL=you@example.com

# Optional: Agent tuning
AGENT_EXECUTION_INTERVAL=300      # Seconds between agent runs (default: 5min)
MAX_CONCURRENT_AGENTS=10          # Max parallel agent executions
```

### Key Configuration Notes

**Minimum viable config** (local testing):
- `OPENAI_API_KEY` only - everything else has defaults

**Production config** requires:
- Cloud credentials (AWS or GCP)
- Bot tokens (Telegram or Slack)
- GitHub token (for PR workflow)
- Cost alert thresholds

**Bot setup:**
1. Create Telegram bot via [@BotFather](https://t.me/botfather)
2. Get token and chat ID
3. Add to `.env`
4. Test: `/start` in Telegram

---

## 📊 Observability

### Metrics (Prometheus)

**Exposed at:** http://localhost:9090

**Key metrics:**
- `agent_execution_duration_seconds` - Agent runtime
- `agent_success_total` - Successful agent runs
- `agent_failure_total` - Failed agent runs
- `cost_optimization_savings_usd` - Money saved by CostWatcher
- `anomaly_detection_count` - Anomalies detected
- `pr_approval_latency_seconds` - Time to approve PRs
- `infrastructure_cost_daily_usd` - Daily cloud spend

**Scrape targets:**
- Application: http://devops-ai-platform:8000/metrics
- Node exporter: http://node-exporter:9100/metrics
- Kubernetes: http://kubernetes:443/metrics

---

### Dashboards (Grafana)

**Access at:** http://localhost:3001 (admin/admin)

**3 pre-built dashboards:**

1. **DevOps AI Platform Overview**
   - Platform health gauge
   - Agent status grid
   - Cost analysis charts
   - Alert timeline

2. **AI Agents Performance**
   - Per-agent execution times
   - Success/failure rates
   - Resource utilization
   - Anomaly detection heatmap

3. **Infrastructure Monitoring**
   - Kubernetes cluster metrics
   - Node health and capacity
   - Pod resource usage
   - Network traffic

**Dashboards location:** `monitoring/grafana/dashboards/`

---

### Logs (Structured JSON)

**Log output:** `logs/platform.log` (volume-mounted in Docker)

**Log format:**
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "level": "INFO",
  "agent": "CostWatcher",
  "message": "Detected idle RDS instance",
  "details": {
    "instance_id": "db-prod-123",
    "idle_days": 7,
    "monthly_cost": 450.00,
    "recommendation": "stop_or_downsize"
  }
}
```

**Log levels:** DEBUG, INFO, WARN, ERROR, CRITICAL

**Query logs:**
```bash
# Docker Compose
docker-compose logs -f devops-ai-platform

# Kubernetes
kubectl logs -f deployment/devops-ai-platform -n devops-ai-platform
```

---

### Alerts (AlertManager)

**Access at:** http://localhost:9093

**Alert rules configured:**
- Agent failure rate > 20%
- Cost spike > $100/day
- API response time > 2s
- Database connection errors
- High memory usage (>90%)

**Alert routing:**
- Critical → Telegram + Slack + Email
- Warning → Slack only
- Info → Log only

**Config:** `monitoring/alertmanager.yml`

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Complete)
- [x] 12 MCP agents implemented and tested
- [x] Bot gateway (Telegram/Slack) with approval workflow
- [x] Local development environment (kind cluster)
- [x] Docker Compose for rapid testing
- [x] Complete observability stack (Prometheus/Grafana)
- [x] Terraform infrastructure for AWS EKS

### 🔄 Phase 2: Production Hardening (In Progress)
- [ ] SSL/TLS configuration with Let's Encrypt
- [ ] Automated backup and disaster recovery
- [ ] Performance optimization and load testing
- [ ] Multi-AZ high availability setup
- [ ] Advanced cost optimization algorithms
- [ ] Security scanning integration (Trivy, Falco)

### 📋 Phase 3: Advanced AI Features (Q2 2026)
- [ ] Deep learning models for pattern recognition
- [ ] Predictive maintenance (MTBF forecasting)
- [ ] Auto-remediation without human approval (for low-risk tasks)
- [ ] Multi-cluster management and cross-cloud orchestration
- [ ] Natural language query interface ("Show me expensive pods")

### 🚀 Phase 4: Multi-Cloud & Enterprise (Q3 2026)
- [ ] Full GCP support (GKE, Cloud Run, BigQuery)
- [ ] Azure support (AKS, App Service)
- [ ] Multi-tenant architecture with RBAC
- [ ] SSO integration (Okta, Auth0)
- [ ] Advanced compliance reporting (SOC2, GDPR, HIPAA)
- [ ] Marketplace distribution (AWS Marketplace, GCP Marketplace)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

Copyright (c) 2026 Litan Shamir

---

## ⚠️ Disclaimer

**Production Use:** This platform is in active development. While the core functionality is production-ready, we recommend:
- Testing thoroughly in dev/staging environments first
- Starting with manual approval for all agent actions
- Gradually increasing automation as you build confidence
- Monitoring costs closely during initial deployment

**Security:**
- Always use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Never commit `.env` files with real credentials
- Rotate API keys and tokens regularly
- Review all agent-generated PRs before approval

**Cost:**
- AWS Free Tier covers local testing and small workloads
- Production EKS clusters typically cost $50-200/month depending on size
- Monitor `AWS_COST_ALERT_THRESHOLD` to prevent runaway spending

**Support:**
- Open issues on GitHub for bugs or questions
- See `docs/design.md` for architectural decisions
- Pull requests welcome following contribution guidelines

---

## 📚 Additional Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) - React dashboard setup
- [docs/design.md](docs/design.md) - Architecture and design decisions
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

---

**Built with:** Python 3.9+ | FastAPI | Kubernetes | Terraform | OpenAI | Prometheus | Grafana | AWS
