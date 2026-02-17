# Design Decisions

This document captures key architectural and technical decisions made during the development of the DevOps AI Platform.

---

## 1. MCP (Model Context Protocol) for AI Agents

### Decision
Use MCP as the agent communication protocol instead of custom RPC or REST APIs.

### Context
Needed a standardized way for AI agents to exchange context, trigger actions, and coordinate without tight coupling.

### Alternatives Considered
- **Custom REST API**: More control but reinventing the wheel; no ecosystem support
- **gRPC**: High performance but complex for simple agent communication
- **Message queue (RabbitMQ/Kafka)**: Overkill for our scale; adds operational complexity

### Rationale
- MCP provides standardized schemas for agent communication
- Emerging standard in AI tooling (Claude, OpenAI adopting)
- Simpler than gRPC, more structured than REST
- Built-in context management and tool use patterns

### Trade-offs
- ✅ Standardization and ecosystem compatibility
- ✅ Reduced development time
- ❌ Limited community resources (still emerging)
- ❌ Some protocol overhead vs. custom solution

---

## 2. Human-in-the-Loop via GitHub PRs

### Decision
All infrastructure changes proposed by agents go through GitHub pull requests requiring human approval.

### Context
Autonomous agents making infrastructure changes can be risky. Need safety mechanism that:
- Provides audit trail
- Allows review before execution
- Enables rollback
- Integrates with existing workflows

### Alternatives Considered
- **Direct Terraform apply**: Fast but dangerous; no review mechanism
- **Approval UI in dashboard**: Custom solution; duplicates PR workflow
- **Email/Slack approval**: No code review; poor audit trail

### Rationale
- Teams already use GitHub for code review
- PRs provide diff view, discussion, and CI checks
- Natural rollback via revert commits
- Integrates with existing CI/CD (ArgoCD watches PRs)

### Trade-offs
- ✅ Safety and auditability
- ✅ Familiar workflow for teams
- ✅ Built-in rollback
- ❌ Latency (minutes vs. seconds for approval)
- ❌ GitHub dependency

### Implementation
```
Agent detects issue → Opens PR with fix → Bot notifies Telegram
→ Human reviews PR → Approves via bot → ArgoCD syncs changes
```

---

## 3. Bot Interface (Telegram/Slack) Over Web UI Only

### Decision
Primary interface is bot commands (Telegram/Slack), with web dashboard as secondary.

### Context
DevOps engineers live in chat tools. Context switching to web UI adds friction.

### Alternatives Considered
- **Web UI only**: Better for complex operations but requires switching tools
- **CLI only**: Powerful but not mobile-friendly; harder for team collaboration
- **API only**: Maximum flexibility but requires scripting knowledge

### Rationale
- Engineers already have Telegram/Slack open
- Mobile-friendly (approve PRs from phone)
- Natural for team notifications and collaboration
- Low barrier to entry (just chat commands)

### Trade-offs
- ✅ Low friction, always accessible
- ✅ Mobile-friendly
- ✅ Team collaboration in chat
- ❌ Limited UI for complex visualizations
- ❌ Command discoverability (help commands needed)

### Solution
**Hybrid approach:**
- Bot for common operations (`/status`, `/cost`, `/approve`)
- Web dashboard for detailed analysis and charts
- API for programmatic access

---

## 4. PostgreSQL + Redis + MongoDB (Polyglot Persistence)

### Decision
Use three databases for different data patterns:
- **PostgreSQL**: Relational data (users, configurations, audit logs)
- **Redis**: Cache and real-time data (agent state, metrics buffer)
- **MongoDB**: Time-series data (historical metrics, agent execution logs)

### Context
Different data has different access patterns and consistency requirements.

### Alternatives Considered
- **PostgreSQL only**: Simpler but slower for time-series and caching
- **TimescaleDB**: Better for time-series but adds complexity
- **Single NoSQL (MongoDB)**: Flexible but poor for relational data

### Rationale
- PostgreSQL: ACID guarantees for critical data (users, config)
- Redis: Sub-millisecond cache for agent coordination
- MongoDB: Flexible schema for evolving agent logs and metrics

### Trade-offs
- ✅ Optimized for each use case
- ✅ Proven technologies
- ❌ Operational complexity (3 databases to manage)
- ❌ No cross-database transactions

### Mitigation
- Docker Compose bundles all three for local dev
- Managed services (RDS, ElastiCache, DocumentDB) for production

---

## 5. Prometheus + Grafana Over Commercial Observability

### Decision
Use open-source Prometheus + Grafana instead of Datadog, New Relic, or Dynatrace.

### Context
Need comprehensive metrics, dashboards, and alerting without vendor lock-in.

### Alternatives Considered
- **Datadog**: Best-in-class but expensive ($15-31/host/month)
- **New Relic**: Powerful but complex pricing
- **AWS CloudWatch**: Native but limited query capabilities
- **Grafana Cloud**: Managed Prometheus but still paid

### Rationale
- Zero cost (open-source)
- No vendor lock-in
- Flexible querying (PromQL)
- Huge ecosystem (exporters, dashboards, integrations)
- Skills transferable across companies

### Trade-offs
- ✅ Zero licensing cost
- ✅ Full control and customization
- ✅ Industry standard
- ❌ Self-hosted (operational overhead)
- ❌ Limited AI/ML features (vs. Datadog APM)

### Implementation
- Prometheus scrapes metrics from app + exporters
- Grafana visualizes with pre-built dashboards
- AlertManager routes alerts to Telegram/Slack

---

## 6. Terraform Over Pulumi/CDK

### Decision
Use Terraform for infrastructure as code instead of Pulumi or AWS CDK.

### Context
Need IaC tool that's multi-cloud, widely adopted, and has large module ecosystem.

### Alternatives Considered
- **AWS CDK**: Programmatic but AWS-only; vendor lock-in
- **Pulumi**: Modern, multi-cloud, but smaller community
- **CloudFormation**: AWS-native but verbose and AWS-only

### Rationale
- Industry standard (most common in job descriptions)
- Huge module registry (Terraform Registry)
- Multi-cloud (AWS today, GCP tomorrow)
- Declarative (easier to reason about state)
- HCL is readable by non-developers

### Trade-offs
- ✅ Widest adoption and resources
- ✅ Proven at scale
- ✅ Multi-cloud by design
- ❌ Less expressive than Pulumi (no loops, limited logic)
- ❌ State management complexity

---

## 7. FastAPI Over Flask/Django

### Decision
Use FastAPI for the backend API framework.

### Context
Need modern Python framework with async support, auto-generated docs, and type safety.

### Alternatives Considered
- **Flask**: Simple but lacks async and auto-docs
- **Django**: Full-featured but overkill for API-only service
- **Tornado**: Async but older design patterns

### Rationale
- Native async/await (important for I/O-heavy agent coordination)
- Automatic OpenAPI docs (Swagger UI at `/docs`)
- Pydantic integration (type safety, validation)
- High performance (comparable to Node.js)
- Modern Python 3.9+ features

### Trade-offs
- ✅ Fast development with type hints
- ✅ Auto-generated API docs
- ✅ High performance
- ❌ Smaller ecosystem than Flask/Django
- ❌ Breaking changes in major versions

---

## 8. ArgoCD Over Flux/Spinnaker

### Decision
Use ArgoCD for GitOps continuous deployment.

### Context
Need Kubernetes-native CD tool that syncs from Git automatically.

### Alternatives Considered
- **Flux**: Lightweight but less mature UI
- **Spinnaker**: Enterprise-grade but complex setup
- **Jenkins X**: Opinionated but less flexible

### Rationale
- Beautiful UI for deployment visualization
- Git as single source of truth
- Auto-sync from Git repos (no manual triggers)
- Application-level abstractions (not just raw manifests)
- Strong RBAC and multi-tenancy

### Trade-offs
- ✅ Best-in-class GitOps experience
- ✅ Great UI and UX
- ✅ Active CNCF project
- ❌ More complex than Flux
- ❌ Requires Redis (dependency)

---

## 9. Kind for Local Dev Over Minikube/k3d

### Decision
Use kind (Kubernetes IN Docker) for local development clusters.

### Context
Need fast, disposable local Kubernetes for testing without VM overhead.

### Alternatives Considered
- **Minikube**: Standard but VM-based (slow startup)
- **k3d**: Lightweight but less feature parity with real clusters
- **Docker Desktop K8s**: Easy but limited configuration

### Rationale
- Fast startup (30-60 seconds)
- Multi-node clusters for testing
- Runs in Docker (no VM needed)
- Official Kubernetes SIG project
- Excellent for CI/CD testing

### Trade-offs
- ✅ Fast and lightweight
- ✅ True Kubernetes (not simplified)
- ✅ Multi-node support
- ❌ Docker required (not Podman)
- ❌ No persistent storage across restarts

---

## 10. Agent Execution Interval: 5 Minutes

### Decision
Agents run every 5 minutes by default (configurable via `AGENT_EXECUTION_INTERVAL`).

### Context
Need balance between responsiveness and cost (API calls to OpenAI, AWS).

### Alternatives Considered
- **1 minute**: More responsive but 5x API costs
- **15 minutes**: Cheaper but delayed issue detection
- **Event-driven**: Ideal but complex to implement for all triggers

### Rationale
- 5 minutes is fast enough for most issues (not critical systems)
- Keeps API costs reasonable (288 runs/day per agent)
- Allows manual override for urgent analysis (`/agent analyze now`)

### Trade-offs
- ✅ Balanced cost vs. responsiveness
- ✅ Configurable per deployment
- ❌ Not real-time (5-min lag)
- ❌ Potential for duplicate work (if issue spans multiple intervals)

### Future
- Event-driven triggers for critical metrics (e.g., cost spike)
- Adaptive intervals (slow down if no issues, speed up if problems)

---

## 11. OpenAI API Over Anthropic/Local Models

### Decision
Default to OpenAI API (GPT-4) for agent reasoning, with Anthropic as alternative.

### Context
Agents need LLM for decision-making, code generation, and natural language understanding.

### Alternatives Considered
- **Anthropic Claude**: Excellent but newer API
- **Local models (Llama, Mistral)**: Free but lower quality and infrastructure overhead
- **AWS Bedrock**: Vendor integration but limited model selection

### Rationale
- OpenAI has most mature API and tooling
- GPT-4 Turbo performs best for structured output (JSON mode)
- Function calling is critical for agent actions
- Embeddings API for semantic search (job scoring, log analysis)

### Trade-offs
- ✅ Best performance and developer experience
- ✅ Function calling and structured output
- ❌ Cost ($0.01/1K tokens for GPT-4 Turbo)
- ❌ Vendor dependency

### Mitigation
- Support both OpenAI and Anthropic (via `MODEL_PROVIDER` env var)
- Future: Local model support for cost-sensitive deployments

---

## 12. No Frontend Framework Lock-in (React Preferred)

### Decision
Build dashboard in React but keep backend API generic (no SSR, no framework-specific routes).

### Context
Want flexibility to rebuild frontend without touching backend.

### Alternatives Considered
- **Next.js SSR**: Great DX but couples frontend and backend
- **Django templates**: Simple but not modern SPA experience
- **Vue/Svelte**: Valid choices but React has largest ecosystem

### Rationale
- React has largest talent pool and component library
- Backend is pure API (FastAPI) with no view logic
- Frontend can be swapped for Vue, Svelte, or CLI without API changes

### Trade-offs
- ✅ Full separation of concerns
- ✅ Easy to rebuild frontend
- ❌ No SSR (SEO not critical for internal tools)
- ❌ Separate deployment (two services)

---

## 13. MIT License

### Decision
Release under MIT License (permissive open source).

### Context
Want to maximize adoption and allow commercial use.

### Alternatives Considered
- **Apache 2.0**: More explicit patent protection
- **GPL**: Copyleft but limits commercial adoption
- **AGPL**: Strongest copyleft but reduces contributions

### Rationale
- Maximum adoption (no legal review needed)
- Portfolio project (permissive helps job search)
- Allows forks for proprietary use

### Trade-offs
- ✅ Maximum freedom for users
- ✅ Encourages adoption
- ❌ No patent protection
- ❌ Can be relicensed by others

---

## 14. AWS-First, GCP-Compatible Design

### Decision
Build for AWS first, design abstractions for future GCP support.

### Context
Need to ship fast but avoid AWS lock-in for future multi-cloud.

### Alternatives Considered
- **Multi-cloud from day one**: Slows development significantly
- **AWS-only**: Fastest but limits portability
- **GCP-first**: Smaller market share for portfolio

### Rationale
- AWS has 32% market share (most job opportunities)
- EKS Free Tier (vs. GKE charges for control plane)
- Design with abstractions (e.g., `CloudProvider` interface)

### Trade-offs
- ✅ Ship faster (single cloud)
- ✅ Most relevant for jobs
- ✅ Future-proofed with abstractions
- ❌ GCP support is theoretical (not tested)

### Implementation
- Abstract cloud operations behind interfaces
- Use Terraform for portability
- Document GCP equivalents in roadmap

---

## 15. No Custom CI/CD Runner (Use GitHub Actions)

### Decision
Use GitHub Actions for CI/CD instead of self-hosted Jenkins/GitLab.

### Context
Need CI/CD for testing and automation without infrastructure overhead.

### Alternatives Considered
- **Self-hosted Jenkins**: Full control but operational overhead
- **GitLab CI**: Great but requires migrating from GitHub
- **CircleCI/Travis**: Paid tiers required for private repos

### Rationale
- Free for public repos (3,000 minutes/month for private)
- No infrastructure to maintain
- Native GitHub integration (PRs, releases, secrets)
- Huge marketplace of actions

### Trade-offs
- ✅ Zero operational overhead
- ✅ Free tier generous
- ✅ Largest ecosystem
- ❌ Vendor lock-in (GitHub)
- ❌ Less control than self-hosted

---

## Future Decisions to Make

### 1. Multi-Tenancy Architecture
**When:** Phase 4 (Q3 2026)
**Question:** Namespace-based isolation or separate clusters per tenant?

### 2. Auto-Remediation Without Approval
**When:** Phase 3 (Q2 2026)
**Question:** Which agent actions are safe to auto-execute (e.g., disk cleanup)?

### 3. GCP Support Implementation
**When:** Phase 4 (Q3 2026)
**Question:** Use Terraform modules or Pulumi for better GCP abstraction?

### 4. Local LLM Support
**When:** TBD (cost optimization for large deployments)
**Question:** Llama 3, Mistral, or wait for better open models?

---

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [GitOps Principles](https://opengitops.dev/)
- [Prometheus Naming Conventions](https://prometheus.io/docs/practices/naming/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Last Updated:** February 17, 2026
**Maintained By:** Platform Team
