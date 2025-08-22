"""
BurstPredictor Agent for DevOps AI Platform.

This agent analyzes traffic patterns and predicts potential traffic bursts,
providing proactive scaling recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from core.config import Settings


class BurstPredictorAgent(BaseAgent):
    """
    BurstPredictor agent for traffic prediction and scaling.
    
    This agent analyzes historical traffic patterns to predict potential
    traffic bursts and provides proactive scaling recommendations.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(AgentType.BURST_PREDICTOR, settings)
        self.prediction_window = 24  # hours
        self.confidence_threshold = 0.7
        self.scaling_threshold = 0.8
    
    def _get_description(self) -> str:
        """Get agent description."""
        return "Predicts traffic bursts and provides proactive scaling recommendations"
    
    async def analyze(self, context: AgentContext) -> AgentResult:
        """
        Analyze current traffic patterns and predict potential bursts.
        
        Args:
            context: Agent execution context
            
        Returns:
            Analysis result with traffic predictions
        """
        try:
            # Extract traffic metrics from context
            metrics_data = context.metrics_data
            traffic_data = metrics_data.get("traffic", {})
            
            if not traffic_data:
                return AgentResult(
                    success=False,
                    data={},
                    recommendations=[],
                    actions=[],
                    error_message="No traffic data available"
                )
            
            # Analyze traffic patterns
            analysis_result = self._analyze_traffic_patterns(traffic_data)
            
            # Predict potential bursts
            predictions = self._predict_traffic_bursts(traffic_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(predictions, analysis_result)
            
            return AgentResult(
                success=True,
                data={
                    "analysis": analysis_result,
                    "predictions": predictions,
                    "traffic_patterns": self._extract_patterns(traffic_data)
                },
                recommendations=recommendations,
                actions=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error in burst prediction analysis: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Analysis failed: {str(e)}"
            )
    
    async def optimize(self, context: AgentContext) -> AgentResult:
        """
        Generate optimization recommendations for scaling.
        
        Args:
            context: Agent execution context
            
        Returns:
            Optimization result with scaling actions
        """
        try:
            # Get current infrastructure state
            infrastructure_data = context.infrastructure_data
            current_scaling = infrastructure_data.get("scaling", {})
            
            # Analyze current scaling configuration
            scaling_analysis = self._analyze_scaling_config(current_scaling)
            
            # Generate optimization actions
            actions = self._generate_scaling_actions(scaling_analysis)
            
            return AgentResult(
                success=True,
                data={
                    "scaling_analysis": scaling_analysis,
                    "current_config": current_scaling
                },
                recommendations=[],
                actions=actions
            )
            
        except Exception as e:
            self.logger.error(f"Error in burst prediction optimization: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Optimization failed: {str(e)}"
            )
    
    def _analyze_traffic_patterns(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze traffic patterns for trends and seasonality."""
        try:
            # Convert traffic data to pandas DataFrame
            df = pd.DataFrame(traffic_data.get("time_series", []))
            
            if df.empty:
                return {"error": "No time series data available"}
            
            # Calculate basic statistics
            stats = {
                "mean": df["value"].mean(),
                "std": df["value"].std(),
                "min": df["value"].min(),
                "max": df["value"].max(),
                "trend": self._calculate_trend(df),
                "seasonality": self._detect_seasonality(df),
                "volatility": df["value"].std() / df["value"].mean() if df["value"].mean() > 0 else 0
            }
            
            # Detect patterns
            patterns = {
                "daily_pattern": self._extract_daily_pattern(df),
                "weekly_pattern": self._extract_weekly_pattern(df),
                "peak_hours": self._identify_peak_hours(df)
            }
            
            return {
                "statistics": stats,
                "patterns": patterns,
                "data_points": len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing traffic patterns: {e}")
            return {"error": str(e)}
    
    def _predict_traffic_bursts(self, traffic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict potential traffic bursts based on historical patterns."""
        try:
            predictions = []
            
            # Get historical data
            time_series = traffic_data.get("time_series", [])
            if not time_series:
                return predictions
            
            # Convert to DataFrame
            df = pd.DataFrame(time_series)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            
            # Simple prediction based on moving average and trend
            window_size = 24  # 24 hours
            if len(df) >= window_size:
                df["moving_avg"] = df["value"].rolling(window=window_size).mean()
                df["trend"] = df["value"].rolling(window=window_size).apply(
                    lambda x: np.polyfit(range(len(x)), x, 1)[0]
                )
                
                # Predict next 24 hours
                last_values = df["value"].tail(window_size).values
                last_trend = df["trend"].iloc[-1]
                
                for hour in range(1, 25):
                    predicted_value = last_values.mean() + (last_trend * hour)
                    confidence = self._calculate_prediction_confidence(df, predicted_value)
                    
                    if confidence > self.confidence_threshold:
                        predictions.append({
                            "timestamp": datetime.now() + timedelta(hours=hour),
                            "predicted_value": predicted_value,
                            "confidence": confidence,
                            "burst_probability": self._calculate_burst_probability(predicted_value, df),
                            "scaling_recommendation": self._get_scaling_recommendation(predicted_value, df)
                        })
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting traffic bursts: {e}")
            return []
    
    def _generate_recommendations(self, predictions: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on predictions and analysis."""
        recommendations = []
        
        # High burst probability recommendations
        high_burst_predictions = [p for p in predictions if p.get("burst_probability", 0) > self.scaling_threshold]
        
        if high_burst_predictions:
            recommendations.append({
                "title": "Proactive Scaling Recommended",
                "description": f"High probability of traffic burst detected in next {len(high_burst_predictions)} hours",
                "priority": "high",
                "impact": "prevent_outage",
                "actions": [
                    "Increase HPA minReplicas",
                    "Prepare additional capacity",
                    "Monitor closely"
                ]
            })
        
        # Pattern-based recommendations
        patterns = analysis.get("patterns", {})
        if patterns.get("daily_pattern"):
            recommendations.append({
                "title": "Daily Traffic Pattern Detected",
                "description": "Consider adjusting scaling based on daily traffic patterns",
                "priority": "normal",
                "impact": "cost_optimization",
                "actions": [
                    "Schedule scaling based on peak hours",
                    "Optimize resource allocation"
                ]
            })
        
        # Volatility recommendations
        stats = analysis.get("statistics", {})
        if stats.get("volatility", 0) > 0.5:
            recommendations.append({
                "title": "High Traffic Volatility",
                "description": "Traffic shows high volatility, consider more aggressive scaling",
                "priority": "medium",
                "impact": "performance_improvement",
                "actions": [
                    "Lower scaling thresholds",
                    "Increase buffer capacity"
                ]
            })
        
        return recommendations
    
    def _generate_scaling_actions(self, scaling_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific scaling actions."""
        actions = []
        
        current_config = scaling_analysis.get("current_config", {})
        recommendations = scaling_analysis.get("recommendations", [])
        
        for rec in recommendations:
            actions.append({
                "title": rec.get("title", "Scaling Action"),
                "description": rec.get("description", ""),
                "resource": "hpa",
                "change": rec.get("change", {}),
                "priority": rec.get("priority", "normal"),
                "estimated_impact": rec.get("impact", "unknown")
            })
        
        return actions
    
    def _calculate_trend(self, df: pd.DataFrame) -> float:
        """Calculate trend in traffic data."""
        if len(df) < 2:
            return 0.0
        
        x = np.arange(len(df))
        y = df["value"].values
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _detect_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonality in traffic data."""
        if len(df) < 24:
            return {"detected": False, "period": None}
        
        # Simple seasonality detection
        daily_avg = df.groupby(df["timestamp"].dt.hour)["value"].mean()
        
        return {
            "detected": daily_avg.std() > daily_avg.mean() * 0.2,
            "period": "daily",
            "strength": daily_avg.std() / daily_avg.mean() if daily_avg.mean() > 0 else 0
        }
    
    def _extract_daily_pattern(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract daily traffic pattern."""
        if len(df) < 24:
            return {}
        
        daily_avg = df.groupby(df["timestamp"].dt.hour)["value"].mean()
        return daily_avg.to_dict()
    
    def _extract_weekly_pattern(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract weekly traffic pattern."""
        if len(df) < 7 * 24:
            return {}
        
        weekly_avg = df.groupby(df["timestamp"].dt.dayofweek)["value"].mean()
        return weekly_avg.to_dict()
    
    def _identify_peak_hours(self, df: pd.DataFrame) -> List[int]:
        """Identify peak traffic hours."""
        if len(df) < 24:
            return []
        
        daily_avg = df.groupby(df["timestamp"].dt.hour)["value"].mean()
        threshold = daily_avg.mean() + daily_avg.std()
        peak_hours = daily_avg[daily_avg > threshold].index.tolist()
        
        return peak_hours
    
    def _extract_patterns(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract various patterns from traffic data."""
        return {
            "trend": "increasing",  # Simplified
            "seasonality": "daily",
            "volatility": "medium"
        }
    
    def _analyze_scaling_config(self, current_scaling: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current scaling configuration."""
        return {
            "current_config": current_scaling,
            "recommendations": [
                {
                    "title": "Optimize HPA Configuration",
                    "description": "Adjust scaling parameters based on traffic patterns",
                    "change": {
                        "minReplicas": "increase",
                        "maxReplicas": "adjust",
                        "targetCPUUtilizationPercentage": "decrease"
                    },
                    "priority": "medium",
                    "impact": "performance_improvement"
                }
            ]
        }
    
    def _calculate_prediction_confidence(self, df: pd.DataFrame, predicted_value: float) -> float:
        """Calculate confidence in prediction."""
        # Simple confidence calculation based on historical accuracy
        recent_std = df["value"].tail(24).std()
        mean_value = df["value"].mean()
        
        if mean_value == 0:
            return 0.5
        
        # Confidence decreases with higher volatility
        confidence = max(0.1, 1.0 - (recent_std / mean_value))
        return min(1.0, confidence)
    
    def _calculate_burst_probability(self, predicted_value: float, df: pd.DataFrame) -> float:
        """Calculate probability of traffic burst."""
        mean_value = df["value"].mean()
        std_value = df["value"].std()
        
        if std_value == 0:
            return 0.0
        
        # Calculate z-score
        z_score = (predicted_value - mean_value) / std_value
        
        # Convert to probability (simplified)
        if z_score > 2:
            return 0.9
        elif z_score > 1.5:
            return 0.7
        elif z_score > 1:
            return 0.5
        else:
            return 0.2
    
    def _get_scaling_recommendation(self, predicted_value: float, df: pd.DataFrame) -> Dict[str, Any]:
        """Get scaling recommendation based on predicted value."""
        mean_value = df["value"].mean()
        current_capacity = mean_value * 1.5  # Assume 50% buffer
        
        if predicted_value > current_capacity * 1.2:
            return {
                "action": "scale_up",
                "reason": "Predicted traffic exceeds current capacity",
                "urgency": "high"
            }
        elif predicted_value > current_capacity:
            return {
                "action": "monitor",
                "reason": "Predicted traffic near capacity limit",
                "urgency": "medium"
            }
        else:
            return {
                "action": "no_action",
                "reason": "Predicted traffic within capacity",
                "urgency": "low"
            }
