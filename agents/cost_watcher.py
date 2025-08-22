"""
CostWatcher Agent for DevOps AI Platform.

This agent monitors cloud costs and provides optimization recommendations
to reduce infrastructure spending.
"""

import boto3
from typing import Dict, Any, List
from datetime import datetime, timedelta

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from core.config import Settings


class CostWatcherAgent(BaseAgent):
    """
    CostWatcher agent for cost monitoring and optimization.
    
    This agent analyzes cloud spending patterns and provides recommendations
    for cost optimization and budget management.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(AgentType.COST_WATCHER, settings)
        self.cost_threshold = settings.aws_cost_alert_threshold
        self.optimization_threshold = 0.1  # 10% potential savings
    
    def _get_description(self) -> str:
        """Get agent description."""
        return "Monitors cloud costs and provides optimization recommendations"
    
    async def analyze(self, context: AgentContext) -> AgentResult:
        """
        Analyze current cost patterns and identify optimization opportunities.
        
        Args:
            context: Agent execution context
            
        Returns:
            Analysis result with cost insights
        """
        try:
            # Extract cost data from context
            cost_data = context.cost_data
            
            if not cost_data:
                # Try to fetch cost data from AWS
                cost_data = await self._fetch_aws_cost_data()
            
            if not cost_data:
                return AgentResult(
                    success=False,
                    data={},
                    recommendations=[],
                    actions=[],
                    error_message="No cost data available"
                )
            
            # Analyze cost patterns
            cost_analysis = self._analyze_cost_patterns(cost_data)
            
            # Identify optimization opportunities
            optimization_opportunities = self._identify_optimization_opportunities(cost_data)
            
            # Generate recommendations
            recommendations = self._generate_cost_recommendations(cost_analysis, optimization_opportunities)
            
            return AgentResult(
                success=True,
                data={
                    "cost_analysis": cost_analysis,
                    "optimization_opportunities": optimization_opportunities,
                    "current_spending": self._get_current_spending(cost_data)
                },
                recommendations=recommendations,
                actions=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error in cost analysis: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Cost analysis failed: {str(e)}"
            )
    
    async def optimize(self, context: AgentContext) -> AgentResult:
        """
        Generate cost optimization actions.
        
        Args:
            context: Agent execution context
            
        Returns:
            Optimization result with cost-saving actions
        """
        try:
            # Get current infrastructure state
            infrastructure_data = context.infrastructure_data
            current_resources = infrastructure_data.get("resources", {})
            
            # Analyze resource utilization
            utilization_analysis = self._analyze_resource_utilization(current_resources)
            
            # Generate optimization actions
            actions = self._generate_optimization_actions(utilization_analysis)
            
            return AgentResult(
                success=True,
                data={
                    "utilization_analysis": utilization_analysis,
                    "current_resources": current_resources
                },
                recommendations=[],
                actions=actions
            )
            
        except Exception as e:
            self.logger.error(f"Error in cost optimization: {e}")
            return AgentResult(
                success=False,
                data={},
                recommendations=[],
                actions=[],
                error_message=f"Cost optimization failed: {str(e)}"
            )
    
    async def _fetch_aws_cost_data(self) -> Dict[str, Any]:
        """Fetch cost data from AWS Cost Explorer."""
        try:
            if not self.settings.aws_access_key_id:
                return {}
            
            # Initialize AWS Cost Explorer client
            ce_client = boto3.client(
                'ce',
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region
            )
            
            # Get cost data for the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )
            
            return self._process_cost_data(response)
            
        except Exception as e:
            self.logger.error(f"Error fetching AWS cost data: {e}")
            return {}
    
    def _process_cost_data(self, cost_response: Dict[str, Any]) -> Dict[str, Any]:
        """Process AWS Cost Explorer response."""
        processed_data = {
            "total_cost": 0.0,
            "daily_costs": [],
            "service_costs": {},
            "usage_costs": {}
        }
        
        try:
            for result in cost_response.get('ResultsByTime', []):
                day_cost = float(result['Total']['UnblendedCost']['Amount'])
                processed_data["total_cost"] += day_cost
                processed_data["daily_costs"].append({
                    "date": result['TimePeriod']['Start'],
                    "cost": day_cost
                })
                
                # Process service costs
                for group in result.get('Groups', []):
                    keys = group['Keys']
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if len(keys) >= 2:
                        service = keys[0]
                        usage_type = keys[1]
                        
                        if service not in processed_data["service_costs"]:
                            processed_data["service_costs"][service] = 0.0
                        processed_data["service_costs"][service] += cost
                        
                        if usage_type not in processed_data["usage_costs"]:
                            processed_data["usage_costs"][usage_type] = 0.0
                        processed_data["usage_costs"][usage_type] += cost
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error processing cost data: {e}")
            return processed_data
    
    def _analyze_cost_patterns(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost patterns and trends."""
        try:
            total_cost = cost_data.get("total_cost", 0.0)
            daily_costs = cost_data.get("daily_costs", [])
            service_costs = cost_data.get("service_costs", {})
            
            # Calculate basic statistics
            if daily_costs:
                costs = [day["cost"] for day in daily_costs]
                avg_daily_cost = sum(costs) / len(costs)
                max_daily_cost = max(costs)
                min_daily_cost = min(costs)
            else:
                avg_daily_cost = max_daily_cost = min_daily_cost = 0.0
            
            # Identify top spending services
            top_services = sorted(
                service_costs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Calculate cost trends
            trend = self._calculate_cost_trend(daily_costs)
            
            return {
                "total_cost": total_cost,
                "avg_daily_cost": avg_daily_cost,
                "max_daily_cost": max_daily_cost,
                "min_daily_cost": min_daily_cost,
                "top_services": top_services,
                "trend": trend,
                "budget_status": self._check_budget_status(total_cost)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cost patterns: {e}")
            return {"error": str(e)}
    
    def _identify_optimization_opportunities(self, cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify cost optimization opportunities."""
        opportunities = []
        
        try:
            service_costs = cost_data.get("service_costs", {})
            usage_costs = cost_data.get("usage_costs", {})
            
            # Check for idle resources
            if "AmazonEC2" in service_costs:
                ec2_cost = service_costs["AmazonEC2"]
                if ec2_cost > self.cost_threshold * 0.3:  # 30% of threshold
                    opportunities.append({
                        "type": "idle_resources",
                        "service": "EC2",
                        "current_cost": ec2_cost,
                        "potential_savings": ec2_cost * 0.2,  # 20% potential savings
                        "description": "Consider stopping idle EC2 instances",
                        "priority": "medium"
                    })
            
            # Check for storage optimization
            if "AmazonS3" in service_costs:
                s3_cost = service_costs["AmazonS3"]
                if s3_cost > self.cost_threshold * 0.2:  # 20% of threshold
                    opportunities.append({
                        "type": "storage_optimization",
                        "service": "S3",
                        "current_cost": s3_cost,
                        "potential_savings": s3_cost * 0.15,  # 15% potential savings
                        "description": "Consider S3 lifecycle policies and storage class optimization",
                        "priority": "low"
                    })
            
            # Check for database optimization
            if "AmazonRDS" in service_costs:
                rds_cost = service_costs["AmazonRDS"]
                if rds_cost > self.cost_threshold * 0.25:  # 25% of threshold
                    opportunities.append({
                        "type": "database_optimization",
                        "service": "RDS",
                        "current_cost": rds_cost,
                        "potential_savings": rds_cost * 0.25,  # 25% potential savings
                        "description": "Consider RDS instance optimization and reserved instances",
                        "priority": "medium"
                    })
            
            # Check for data transfer costs
            if "AWS Data Transfer" in service_costs:
                transfer_cost = service_costs["AWS Data Transfer"]
                if transfer_cost > self.cost_threshold * 0.1:  # 10% of threshold
                    opportunities.append({
                        "type": "data_transfer_optimization",
                        "service": "Data Transfer",
                        "current_cost": transfer_cost,
                        "potential_savings": transfer_cost * 0.3,  # 30% potential savings
                        "description": "Optimize data transfer patterns and use CloudFront",
                        "priority": "high"
                    })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error identifying optimization opportunities: {e}")
            return []
    
    def _generate_cost_recommendations(self, cost_analysis: Dict[str, Any], opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Budget alert recommendations
        budget_status = cost_analysis.get("budget_status", {})
        if budget_status.get("exceeded", False):
            recommendations.append({
                "title": "Budget Exceeded",
                "description": f"Current spending (${cost_analysis.get('total_cost', 0):.2f}) exceeds budget threshold",
                "priority": "high",
                "impact": "cost_reduction",
                "actions": [
                    "Review and stop unnecessary resources",
                    "Implement cost alerts",
                    "Consider reserved instances"
                ]
            })
        
        # High spending recommendations
        total_cost = cost_analysis.get("total_cost", 0.0)
        if total_cost > self.cost_threshold:
            recommendations.append({
                "title": "High Spending Alert",
                "description": f"Current spending (${total_cost:.2f}) is above threshold (${self.cost_threshold})",
                "priority": "medium",
                "impact": "cost_reduction",
                "actions": [
                    "Analyze spending patterns",
                    "Identify optimization opportunities",
                    "Implement cost controls"
                ]
            })
        
        # Optimization opportunities
        significant_opportunities = [
            opp for opp in opportunities 
            if opp.get("potential_savings", 0) > self.optimization_threshold * total_cost
        ]
        
        for opportunity in significant_opportunities:
            recommendations.append({
                "title": f"{opportunity['type'].title()} Opportunity",
                "description": opportunity["description"],
                "priority": opportunity["priority"],
                "impact": "cost_reduction",
                "actions": [
                    f"Review {opportunity['service']} usage",
                    "Implement optimization strategies",
                    f"Potential savings: ${opportunity['potential_savings']:.2f}"
                ]
            })
        
        # Trend-based recommendations
        trend = cost_analysis.get("trend", "stable")
        if trend == "increasing":
            recommendations.append({
                "title": "Increasing Cost Trend",
                "description": "Costs are trending upward, consider proactive optimization",
                "priority": "medium",
                "impact": "cost_control",
                "actions": [
                    "Monitor cost trends",
                    "Implement cost controls",
                    "Review resource usage"
                ]
            })
        
        return recommendations
    
    def _analyze_resource_utilization(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource utilization for cost optimization."""
        utilization = {
            "ec2_instances": [],
            "rds_instances": [],
            "s3_buckets": [],
            "overall_utilization": 0.0
        }
        
        try:
            # Analyze EC2 instances
            ec2_instances = resources.get("ec2", [])
            for instance in ec2_instances:
                cpu_util = instance.get("cpu_utilization", 0.0)
                memory_util = instance.get("memory_utilization", 0.0)
                
                utilization["ec2_instances"].append({
                    "instance_id": instance.get("id", "unknown"),
                    "instance_type": instance.get("type", "unknown"),
                    "cpu_utilization": cpu_util,
                    "memory_utilization": memory_util,
                    "cost": instance.get("cost", 0.0),
                    "optimization_potential": self._calculate_optimization_potential(cpu_util, memory_util)
                })
            
            # Analyze RDS instances
            rds_instances = resources.get("rds", [])
            for instance in rds_instances:
                cpu_util = instance.get("cpu_utilization", 0.0)
                storage_util = instance.get("storage_utilization", 0.0)
                
                utilization["rds_instances"].append({
                    "instance_id": instance.get("id", "unknown"),
                    "instance_type": instance.get("type", "unknown"),
                    "cpu_utilization": cpu_util,
                    "storage_utilization": storage_util,
                    "cost": instance.get("cost", 0.0),
                    "optimization_potential": self._calculate_optimization_potential(cpu_util, storage_util)
                })
            
            # Calculate overall utilization
            all_utils = []
            for ec2 in utilization["ec2_instances"]:
                all_utils.extend([ec2["cpu_utilization"], ec2["memory_utilization"]])
            for rds in utilization["rds_instances"]:
                all_utils.extend([rds["cpu_utilization"], rds["storage_utilization"]])
            
            if all_utils:
                utilization["overall_utilization"] = sum(all_utils) / len(all_utils)
            
            return utilization
            
        except Exception as e:
            self.logger.error(f"Error analyzing resource utilization: {e}")
            return utilization
    
    def _generate_optimization_actions(self, utilization_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific optimization actions."""
        actions = []
        
        # EC2 optimization actions
        for instance in utilization_analysis.get("ec2_instances", []):
            if instance["optimization_potential"] > 0.3:  # 30% optimization potential
                actions.append({
                    "title": f"Optimize EC2 Instance {instance['instance_id']}",
                    "description": f"Instance has low utilization (CPU: {instance['cpu_utilization']:.1%}, Memory: {instance['memory_utilization']:.1%})",
                    "resource": "ec2",
                    "change": {
                        "action": "downsize",
                        "instance_id": instance["instance_id"],
                        "current_type": instance["instance_type"],
                        "suggested_type": self._suggest_instance_type(instance["instance_type"], instance["cpu_utilization"])
                    },
                    "priority": "medium",
                    "estimated_impact": f"Potential savings: ${instance['cost'] * 0.3:.2f}/month"
                })
        
        # RDS optimization actions
        for instance in utilization_analysis.get("rds_instances", []):
            if instance["optimization_potential"] > 0.3:
                actions.append({
                    "title": f"Optimize RDS Instance {instance['instance_id']}",
                    "description": f"Database has low utilization (CPU: {instance['cpu_utilization']:.1%}, Storage: {instance['storage_utilization']:.1%})",
                    "resource": "rds",
                    "change": {
                        "action": "downsize",
                        "instance_id": instance["instance_id"],
                        "current_type": instance["instance_type"],
                        "suggested_type": self._suggest_rds_instance_type(instance["instance_type"], instance["cpu_utilization"])
                    },
                    "priority": "medium",
                    "estimated_impact": f"Potential savings: ${instance['cost'] * 0.25:.2f}/month"
                })
        
        return actions
    
    def _get_current_spending(self, cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get current spending summary."""
        return {
            "total_cost": cost_data.get("total_cost", 0.0),
            "top_services": cost_data.get("service_costs", {}),
            "daily_average": sum(day["cost"] for day in cost_data.get("daily_costs", [])) / max(len(cost_data.get("daily_costs", [])), 1)
        }
    
    def _calculate_cost_trend(self, daily_costs: List[Dict[str, Any]]) -> str:
        """Calculate cost trend from daily costs."""
        if len(daily_costs) < 7:
            return "insufficient_data"
        
        recent_costs = [day["cost"] for day in daily_costs[-7:]]
        earlier_costs = [day["cost"] for day in daily_costs[-14:-7]]
        
        if not earlier_costs:
            return "stable"
        
        recent_avg = sum(recent_costs) / len(recent_costs)
        earlier_avg = sum(earlier_costs) / len(earlier_costs)
        
        if recent_avg > earlier_avg * 1.1:
            return "increasing"
        elif recent_avg < earlier_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _check_budget_status(self, total_cost: float) -> Dict[str, Any]:
        """Check if spending is within budget."""
        return {
            "exceeded": total_cost > self.cost_threshold,
            "threshold": self.cost_threshold,
            "current": total_cost,
            "percentage": (total_cost / self.cost_threshold) * 100 if self.cost_threshold > 0 else 0
        }
    
    def _calculate_optimization_potential(self, cpu_util: float, memory_util: float) -> float:
        """Calculate optimization potential based on utilization."""
        avg_util = (cpu_util + memory_util) / 2
        if avg_util < 0.2:
            return 0.8  # High optimization potential
        elif avg_util < 0.4:
            return 0.5  # Medium optimization potential
        else:
            return 0.1  # Low optimization potential
    
    def _suggest_instance_type(self, current_type: str, cpu_util: float) -> str:
        """Suggest a smaller instance type based on utilization."""
        # Simplified instance type suggestions
        if cpu_util < 0.2:
            return "t3.micro" if "t3" not in current_type else current_type
        elif cpu_util < 0.4:
            return "t3.small" if "t3" not in current_type else current_type
        else:
            return current_type
    
    def _suggest_rds_instance_type(self, current_type: str, cpu_util: float) -> str:
        """Suggest a smaller RDS instance type based on utilization."""
        # Simplified RDS instance type suggestions
        if cpu_util < 0.2:
            return "db.t3.micro" if "t3" not in current_type else current_type
        elif cpu_util < 0.4:
            return "db.t3.small" if "t3" not in current_type else current_type
        else:
            return current_type
