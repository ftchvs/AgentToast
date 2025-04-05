import pytest
import json
from pathlib import Path
from agenttoast.agents.analytics import (
    AnalyticsAgent,
    PerformanceMetrics,
    UserEngagement,
    SystemHealth
)

def test_analytics_initialization():
    """Test AnalyticsAgent initialization."""
    agent = AnalyticsAgent()
    assert agent is not None
    assert isinstance(agent, AnalyticsAgent)

def test_json_data_operations(test_output_dir):
    """Test JSON data loading and saving operations."""
    agent = AnalyticsAgent()
    test_data = {
        "metrics": {"api_latency": 100},
        "engagement": {"active_users": 10},
        "health": {"cpu_usage": 50}
    }
    
    # Test saving data
    test_file = Path(test_output_dir) / "test_analytics.json"
    agent._save_json_data(test_data, test_file)
    assert test_file.exists()
    
    # Test loading data
    loaded_data = agent._load_json_data(test_file)
    assert loaded_data == test_data

def test_performance_metrics_collection():
    """Test collection of performance metrics."""
    agent = AnalyticsAgent()
    metrics = agent.collect_performance_metrics()
    
    assert isinstance(metrics, PerformanceMetrics)
    assert hasattr(metrics, 'api_latency')
    assert hasattr(metrics, 'error_rate')
    assert hasattr(metrics, 'resource_usage')
    assert hasattr(metrics, 'cost_metrics')

def test_user_engagement_analysis():
    """Test user engagement analysis."""
    agent = AnalyticsAgent()
    engagement = agent.analyze_user_engagement()
    
    assert isinstance(engagement, UserEngagement)
    assert hasattr(engagement, 'delivery_success_rate')
    assert hasattr(engagement, 'active_users')
    assert 0.0 <= engagement.delivery_success_rate <= 1.0
    assert engagement.active_users >= 0

def test_system_health_check():
    """Test system health monitoring."""
    agent = AnalyticsAgent()
    health = agent.check_system_health()
    
    assert isinstance(health, SystemHealth)
    assert hasattr(health, 'cpu_usage')
    assert hasattr(health, 'memory_usage')
    assert hasattr(health, 'disk_usage')
    assert all(0.0 <= usage <= 100.0 for usage in [
        health.cpu_usage,
        health.memory_usage,
        health.disk_usage
    ])

def test_analytics_run():
    """Test complete analytics run."""
    agent = AnalyticsAgent()
    result = agent.run()
    
    assert isinstance(result, dict)
    assert 'performance' in result
    assert 'engagement' in result
    assert 'health' in result
    
    assert isinstance(result['performance'], PerformanceMetrics)
    assert isinstance(result['engagement'], UserEngagement)
    assert isinstance(result['health'], SystemHealth) 