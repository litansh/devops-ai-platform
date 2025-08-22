"""
AnomalyDetector Agent for DevOps AI Platform.

This agent detects anomalies in infrastructure metrics and provides
alerts and recommendations for unusual patterns.
"""

import numpy as np
from typing import Dict, Any, List

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from core.config import Settings


class AnomalyDetectorAgent(BaseAgent):
    """
    AnomalyDetector agent for detecting infrastructure anomalies.
    
    This agent uses statistical methods to detect unusual patterns in
    metrics and provides alerts and recommendations.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(AgentType.ANOMALY_DETECTOR, settings)
        self.anomaly_threshold = 2.0  # Standard deviations
        self.confidence_threshold = 0.8
    
    def _get_description(self) -> str:
        """Get agent description."""
        return "Detects anomalies in infrastructure metrics and provides alerts"
    
    async def analyze(self, context: AgentContext) -> AgentResult:
        """Analyze metrics for anomalies."""
        try:
            metrics_data = context.metrics_data
            
            if not metrics_data:
                return AgentResult(
                    success=False,
                    data={},
                    recommendations=[],
                    actions=[],
                    error_message="No metrics data available"
                )
            
            # Detect anomalies in different metric types
            anomalies = self._detect_anomalies(metrics_data)
            
            # Generate recommendations
            recommendations = self._generate_anomaly_recommendations(anomalies)
            
            return AgentResult(
                success=True,
                data={
                    "anomalies": anomalies,
                    "metrics_analyzed": len(metrics_data)
                },
                recommendations=recommendations,
                actions=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Anomaly detection failed: {str(e)}"
            )
    
    async def optimize(self, context: AgentContext) -> AgentResult:
        """Generate optimization recommendations for anomaly handling."""
        try:
            # Get current alerting configuration
            infrastructure_data = context.infrastructure_data
            alerting_config = infrastructure_data.get("alerting", {})
            
            # Analyze alerting effectiveness
            alerting_analysis = self._analyze_alerting_config(alerting_config)
            
            # Generate optimization actions
            actions = self._generate_alerting_actions(alerting_analysis)
            
            return AgentResult(
                success=True,
                data={
                    "alerting_analysis": alerting_analysis,
                    "current_config": alerting_config
                },
                recommendations=[],
                actions=actions
            )
            
        except Exception as e:
            self.logger.error(f"Error in anomaly optimization: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Anomaly optimization failed: {str(e)}"
            )
    
    def _detect_anomalies(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics data."""
        anomalies = []
        
        for metric_name, metric_values in metrics_data.items():
            if isinstance(metric_values, list) and len(metric_values) > 10:
                values = [v.get("value", 0) for v in metric_values if isinstance(v, dict)]
                
                if values:
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    
                    if std_val > 0:
                        # Check for anomalies
                        for i, value in enumerate(values):
                            z_score = abs((value - mean_val) / std_val)
                            
                            if z_score > self.anomaly_threshold:
                                anomalies.append({
                                    "metric": metric_name,
                                    "value": value,
                                    "expected_range": [mean_val - 2*std_val, mean_val + 2*std_val],
                                    "z_score": z_score,
                                    "severity": "high" if z_score > 3 else "medium",
                                    "timestamp": metric_values[i].get("timestamp") if i < len(metric_values) else None
                                })
        
        return anomalies
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on detected anomalies."""
        recommendations = []
        
        if anomalies:
            high_severity = [a for a in anomalies if a["severity"] == "high"]
            medium_severity = [a for a in anomalies if a["severity"] == "medium"]
            
            if high_severity:
                recommendations.append({
                    "title": "High Severity Anomalies Detected",
                    "description": f"Found {len(high_severity)} high-severity anomalies requiring immediate attention",
                    "priority": "high",
                    "impact": "performance_degradation",
                    "actions": [
                        "Investigate root cause immediately",
                        "Check system health",
                        "Review recent changes"
                    ]
                })
            
            if medium_severity:
                recommendations.append({
                    "title": "Medium Severity Anomalies Detected",
                    "description": f"Found {len(medium_severity)} medium-severity anomalies to monitor",
                    "priority": "medium",
                    "impact": "monitoring_required",
                    "actions": [
                        "Monitor trends",
                        "Check for patterns",
                        "Update alerting thresholds"
                    ]
                })
        
        return recommendations
    
    def _analyze_alerting_config(self, alerting_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current alerting configuration."""
        return {
            "current_config": alerting_config,
            "recommendations": [
                {
                    "title": "Optimize Alerting Thresholds",
                    "description": "Adjust thresholds based on anomaly patterns",
                    "priority": "medium",
                    "impact": "reduced_false_positives"
                }
            ]
        }
    
    def _generate_alerting_actions(self, alerting_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerting optimization actions."""
        return [
            {
                "title": "Update Alerting Configuration",
                "description": "Optimize alerting thresholds and rules",
                "resource": "alertmanager",
                "change": {
                    "action": "update_thresholds",
                    "severity": "medium"
                },
                "priority": "medium",
                "estimated_impact": "reduced_false_positives"
            }
        ]
