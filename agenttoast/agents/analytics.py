"""Analytics agent for tracking system performance and user engagement."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

import openai
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logger import logger
from ..core.storage import get_storage_size
from .delivery import DeliveryStatus
from ..core.agent import Agent

settings = get_settings()

class PerformanceMetrics(BaseModel):
    """Performance metrics data model."""
    api_latency: Dict[str, float] = {}  # Average latency per API
    error_rates: Dict[str, float] = {}  # Error rates per component
    resource_usage: Dict[str, float] = {}  # CPU, memory, storage usage
    cost_metrics: Dict[str, float] = {}  # Cost per component
    timestamp: datetime = datetime.now()

class UserEngagement(BaseModel):
    """User engagement data model."""
    delivery_success_rate: float = 0.0
    average_digest_duration: float = 0.0
    categories_distribution: Dict[str, int] = {}
    sources_distribution: Dict[str, int] = {}
    active_users: int = 0
    timestamp: datetime = datetime.now()

class SystemHealth(BaseModel):
    """System health data model."""
    status: str = "healthy"  # healthy, degraded, critical
    components_status: Dict[str, str] = {}
    alerts: List[str] = []
    timestamp: datetime = datetime.now()

class AnalyticsAgent(Agent):
    """Agent for collecting and analyzing system metrics."""

    def __init__(self):
        super().__init__()
        self.analytics_dir = Path(settings.analytics_path)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.performance_file = self.analytics_dir / "performance.json"
        self.engagement_file = self.analytics_dir / "engagement.json"
        self.health_file = self.analytics_dir / "health.json"

    def _load_json_data(self, file_path: Path, default: Dict = None) -> Dict:
        """Load JSON data from file."""
        if default is None:
            default = {}
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.error(f"Error loading analytics data: {str(e)}")
            return default

    def _save_json_data(self, file_path: Path, data: Dict) -> None:
        """Save JSON data to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, default=str)
        except Exception as e:
            logger.error(f"Error saving analytics data: {str(e)}")

    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics."""
        metrics = PerformanceMetrics()
        
        # Collect API latencies from logs
        api_calls = self._load_json_data(self.analytics_dir / "api_calls.json", {"calls": []})
        for api, calls in api_calls.items():
            if calls:
                metrics.api_latency[api] = sum(c['latency'] for c in calls) / len(calls)
        
        # Calculate error rates
        error_logs = self._load_json_data(self.analytics_dir / "error_logs.json", {"errors": []})
        total_ops = self._load_json_data(self.analytics_dir / "operations.json", {"ops": []})
        
        for component in ['news_scraper', 'summarizer', 'audio_gen', 'delivery']:
            component_errors = sum(1 for e in error_logs.get('errors', [])
                                 if e['component'] == component)
            component_ops = sum(1 for o in total_ops.get('ops', [])
                              if o['component'] == component)
            if component_ops > 0:
                metrics.error_rates[component] = component_errors / component_ops
        
        # Collect resource usage
        metrics.resource_usage = {
            'storage': get_storage_size(Path(settings.storage_path)) / (1024 * 1024),  # MB
            'audio_storage': get_storage_size(Path(settings.audio_path)) / (1024 * 1024),
            'summaries_storage': get_storage_size(Path(settings.summaries_path)) / (1024 * 1024)
        }
        
        # Calculate costs
        cost_data = self._load_json_data(self.analytics_dir / "costs.json", {"costs": []})
        for component, costs in cost_data.items():
            if costs:
                metrics.cost_metrics[component] = sum(c['amount'] for c in costs)
        
        return metrics

    async def analyze_user_engagement(self, delivery_statuses: List[DeliveryStatus]) -> UserEngagement:
        """Analyze user engagement metrics."""
        engagement = UserEngagement()
        
        if delivery_statuses:
            # Calculate delivery success rate
            successful = sum(1 for s in delivery_statuses if s.status == 'delivered')
            engagement.delivery_success_rate = successful / len(delivery_statuses)
        
        # Load digest data
        digest_data = self._load_json_data(self.analytics_dir / "digests.json", {"digests": []})
        if digest_data.get('digests'):
            # Calculate average digest duration
            durations = [d.get('duration', 0) for d in digest_data['digests']]
            if durations:
                engagement.average_digest_duration = sum(durations) / len(durations)
            
            # Analyze content distribution
            for digest in digest_data['digests']:
                for story in digest.get('stories', []):
                    engagement.categories_distribution[story['category']] = \
                        engagement.categories_distribution.get(story['category'], 0) + 1
                    engagement.sources_distribution[story['source']] = \
                        engagement.sources_distribution.get(story['source'], 0) + 1
        
        # Count active users (users with successful delivery in last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        active_users = set()
        for status in delivery_statuses:
            if status.status == 'delivered' and status.timestamp >= week_ago:
                active_users.add(status.user_id)
        engagement.active_users = len(active_users)
        
        return engagement

    async def check_system_health(self, performance: PerformanceMetrics) -> SystemHealth:
        """Check overall system health."""
        health = SystemHealth()
        alerts = []
        
        # Check component status based on error rates
        for component, error_rate in performance.error_rates.items():
            if error_rate > 0.5:  # 50% error rate
                health.components_status[component] = "critical"
                alerts.append(f"Critical error rate in {component}: {error_rate:.2%}")
            elif error_rate > 0.2:  # 20% error rate
                health.components_status[component] = "degraded"
                alerts.append(f"High error rate in {component}: {error_rate:.2%}")
            else:
                health.components_status[component] = "healthy"
        
        # Check API latencies
        for api, latency in performance.api_latency.items():
            if latency > 5.0:  # 5 seconds
                health.components_status[f"{api}_latency"] = "critical"
                alerts.append(f"High latency in {api}: {latency:.2f}s")
            elif latency > 2.0:  # 2 seconds
                health.components_status[f"{api}_latency"] = "degraded"
                alerts.append(f"Elevated latency in {api}: {latency:.2f}s")
        
        # Check storage usage
        storage_usage = performance.resource_usage.get('storage', 0)
        if storage_usage > settings.storage_alert_threshold:
            health.components_status['storage'] = "critical"
            alerts.append(f"Storage usage critical: {storage_usage:.2f}MB")
        
        # Set overall system status
        if any(status == "critical" for status in health.components_status.values()):
            health.status = "critical"
        elif any(status == "degraded" for status in health.components_status.values()):
            health.status = "degraded"
        
        health.alerts = alerts
        return health

    async def run(self, delivery_statuses: List[DeliveryStatus]) -> Dict:
        """Run the analytics agent.
        
        Args:
            delivery_statuses: List of recent delivery statuses
        
        Returns:
            Dict: Collected analytics data
        """
        logger.info("Starting analytics collection")
        
        # Collect all metrics
        performance = await self.collect_performance_metrics()
        engagement = await self.analyze_user_engagement(delivery_statuses)
        health = await self.check_system_health(performance)
        
        # Save metrics to files
        self._save_json_data(
            self.performance_file,
            performance.model_dump()
        )
        self._save_json_data(
            self.engagement_file,
            engagement.model_dump()
        )
        self._save_json_data(
            self.health_file,
            health.model_dump()
        )
        
        # Log analytics summary
        logger.info(
            "Analytics collection completed",
            extra={
                "system_status": health.status,
                "active_users": engagement.active_users,
                "delivery_success_rate": engagement.delivery_success_rate,
                "alerts": len(health.alerts)
            }
        )
        
        return {
            "performance": performance.model_dump(),
            "engagement": engagement.model_dump(),
            "health": health.model_dump()
        } 