# 📊 Monitoring & Observability Setup

This directory contains the monitoring and observability configuration for the DevOps AI Platform.

## 📁 Directory Structure

```
monitoring/
├── grafana/
│   ├── dashboards/                    # Grafana dashboard JSON files
│   │   ├── devops-ai-platform-overview.json
│   │   ├── agents-dashboard.json
│   │   └── infrastructure-dashboard.json
│   └── provisioning/                  # Grafana provisioning configuration
│       ├── datasources/              # Data source configurations
│       ├── dashboards/               # Dashboard provisioning
│       ├── notifiers/                # Notification channels
│       └── plugins/                  # Plugin installations
├── prometheus.yml                     # Prometheus configuration
├── alertmanager.yml                   # AlertManager configuration
└── README.md                         # This file
```

## 🎯 Grafana Provisioning

Grafana provisioning allows you to automatically configure data sources, dashboards, and notification channels when Grafana starts up. This ensures consistent configuration across all environments.

### 📊 Data Sources

The following data sources are automatically configured:

1. **Prometheus** (Default)
   - URL: `http://monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090`
   - Used for metrics collection and alerting

2. **Loki**
   - URL: `http://loki.monitoring.svc.cluster.local:3100`
   - Used for log aggregation and querying

3. **Elasticsearch**
   - URL: `http://elasticsearch.monitoring.svc.cluster.local:9200`
   - Used for advanced log analysis and search

### 📈 Dashboards

Three main dashboards are automatically provisioned:

1. **DevOps AI Platform Overview**
   - Platform health status
   - Request rates and response times
   - Error rates and success metrics
   - Resource usage monitoring

2. **Agents Dashboard**
   - Agent execution metrics
   - Success rates and error tracking
   - Performance metrics by agent type
   - Resource usage per agent

3. **Infrastructure Dashboard**
   - EKS cluster status
   - Database metrics (RDS, Redis, MongoDB)
   - AWS resource monitoring
   - Cost tracking and optimization

### 🔔 Notification Channels

The following notification channels are configured:

1. **Slack Alerts**
   - Channel: `#devops-alerts`
   - Mentions: `@here` for critical alerts

2. **Email Alerts**
   - Recipients: `devops-team@company.com`
   - Used for important system notifications

3. **Telegram Alerts**
   - Bot token and chat ID configuration
   - Real-time mobile notifications

### 🔌 Plugins

The following Grafana plugins are automatically installed:

- `grafana-piechart-panel` - For pie chart visualizations
- `grafana-worldmap-panel` - For geographical data
- `grafana-clock-panel` - For time-based displays
- `grafana-simple-json-datasource` - For custom data sources
- `grafana-azure-monitor-datasource` - For Azure monitoring
- `grafana-cloudwatch-datasource` - For AWS CloudWatch

## 🚀 Deployment

### Local Development

1. **Start the monitoring stack**:
   ```bash
   docker-compose up -d prometheus grafana alertmanager
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`

3. **Import dashboards**:
   - Navigate to Dashboards > Import
   - Upload the JSON files from `grafana/dashboards/`

### Kubernetes Deployment

1. **Install monitoring stack**:
   ```bash
   helm install monitoring prometheus-community/kube-prometheus-stack \
     --namespace monitoring \
     --create-namespace
   ```

2. **Apply Grafana configuration**:
   ```bash
   kubectl apply -f k8s/base/grafana-configmap.yaml
   ```

3. **Access Grafana**:
   ```bash
   kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
   ```

## 🔧 Configuration

### Customizing Data Sources

Edit `monitoring/grafana/provisioning/datasources/prometheus.yaml` to modify data source configurations:

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://your-prometheus-url:9090
    isDefault: true
```

### Adding New Dashboards

1. Create dashboard JSON file in `monitoring/grafana/dashboards/`
2. Update `monitoring/grafana/provisioning/dashboards/dashboards.yaml`
3. Restart Grafana to apply changes

### Configuring Notifications

Edit `monitoring/grafana/provisioning/notifiers/notifications.yaml` to configure notification channels:

```yaml
notifiers:
  - name: Slack Alerts
    type: slack
    settings:
      url: "https://hooks.slack.com/services/YOUR_WEBHOOK"
      recipient: "#your-channel"
```

## 📊 Metrics Collection

### Application Metrics

The DevOps AI Platform exposes the following metrics:

- `http_requests_total` - HTTP request counts
- `http_request_duration_seconds` - Request duration
- `agent_executions_total` - Agent execution counts
- `bot_interactions_total` - Bot interaction counts
- `database_connections_active` - Active database connections

### Infrastructure Metrics

Prometheus collects metrics from:

- Kubernetes cluster (nodes, pods, services)
- AWS resources (RDS, ElastiCache, EKS)
- Application containers
- System resources (CPU, memory, disk)

## 🚨 Alerting

### Alert Rules

Alert rules are defined in Prometheus configuration:

```yaml
groups:
  - name: devops-ai-platform
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
```

### Alert Routing

Alerts are routed through AlertManager to appropriate notification channels based on severity and labels.

## 🔍 Troubleshooting

### Common Issues

1. **Dashboards not loading**:
   - Check data source connectivity
   - Verify Prometheus is running
   - Check dashboard JSON syntax

2. **No metrics appearing**:
   - Verify application is exposing metrics
   - Check Prometheus scrape configuration
   - Validate service discovery

3. **Alerts not firing**:
   - Check alert rule syntax
   - Verify AlertManager configuration
   - Test notification channels

### Debug Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana health
curl http://localhost:3000/api/health

# Check AlertManager configuration
curl http://localhost:9093/api/v1/status
```

## 📚 Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-usage-monitoring/)
