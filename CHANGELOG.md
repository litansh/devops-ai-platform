# Changelog

All notable changes to the DevOps AI Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Bot gateway (Telegram/Slack) with interactive approval workflow
- PatchUpdater, DiskCleaner, PodRestarter, DBMaintainer agents
- SSL/TLS configuration with Let's Encrypt
- Automated backup and disaster recovery
- Multi-AZ high availability setup

## [0.2.0] - 2026-02-17

### Added
- Demo Flow section in README with 5-step value proof workflow
- Complete architecture documentation in docs/design.md
- Makefile with 30+ development commands
- CI workflow for lint, test, Docker, Terraform validation
- 3 Grafana dashboards (Overview, Agents, Infrastructure)
- Comprehensive .gitignore for secrets protection
- MIT License

### Changed
- README refactored to product-grade structure
- Reduced README length by 39% while improving clarity
- Updated agent count to accurate 8 (was claiming 12)
- Moved aspirational features to Phase 2 roadmap
- Docker Compose now primary quickstart path

### Fixed
- Corrected agent count in documentation
- Removed references to non-existent local-setup.sh
- Clarified which features are implemented vs planned

## [0.1.0] - 2026-01-15

### Added
- 8 core MCP agents:
  - BurstPredictor (traffic forecasting)
  - AutoScalerAdvisor (HPA optimization)
  - CostWatcher (spend analysis)
  - AnomalyDetector (deviation detection)
  - BottleneckScanner (performance analysis)
  - CapacityPlanner (resource forecasting)
  - SecurityResponder (incident triage)
  - LoadShifter (traffic distribution)
- Docker Compose stack with 8 services
- Prometheus + Grafana monitoring
- AlertManager for notifications
- Terraform templates for AWS EKS
- ArgoCD GitOps configuration
- React frontend dashboard
- FastAPI backend
- Polyglot persistence (PostgreSQL, Redis, MongoDB)

### Infrastructure
- Kubernetes deployment manifests
- Helm charts for monitoring stack
- GitHub Actions workflows
- Local kind cluster support

[Unreleased]: https://github.com/litansh/devops-ai-platform/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/litansh/devops-ai-platform/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/litansh/devops-ai-platform/releases/tag/v0.1.0
