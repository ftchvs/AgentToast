#!/usr/bin/env python3
"""
AgentToast Test Script
This script runs a simple test of all agent components.
"""

import os
from pathlib import Path
from src.agents import (
    PlannerAgent,
    FetcherAgent,
    VerifierAgent,
    SummarizerAgent,
    AudioAgent,
    OrchestratorAgent
)

def test_planner():
    """Test the PlannerAgent."""
    print("\n=== Testing PlannerAgent ===")
    agent = PlannerAgent()
    task = {'count': 1, 'categories': ['technology']}
    result = agent.plan_and_act(task)
    print("Plan created:", bool(result.get('plan')))
    return bool(result.get('plan'))

def test_fetcher():
    """Test the FetcherAgent."""
    print("\n=== Testing FetcherAgent ===")
    agent = FetcherAgent()
    task = {'count': 1, 'categories': ['technology']}
    result = agent.plan_and_act(task)
    articles = result.get('articles', [])
    print("Articles fetched:", len(articles))
    return len(articles) > 0

def test_verifier():
    """Test the VerifierAgent."""
    print("\n=== Testing VerifierAgent ===")
    agent = VerifierAgent()
    article = {
        'title': 'Major Tech Company Announces Revolutionary AI Breakthrough',
        'description': 'A leading technology company has announced a significant breakthrough in artificial intelligence research. The new AI model demonstrates unprecedented capabilities in natural language understanding and generation, achieving state-of-the-art results on multiple benchmarks. Researchers say this development could have far-reaching implications for various industries.',
        'url': 'https://example.com/tech-news/ai-breakthrough'
    }
    result = agent.plan_and_act({'article': article})
    print("Verification score:", result.get('quality_score', 0))
    return result.get('is_valid', False)

def test_summarizer():
    """Test the SummarizerAgent."""
    print("\n=== Testing SummarizerAgent ===")
    agent = SummarizerAgent()
    article = {
        'title': 'Test Article',
        'description': 'This is a test article about technology.'
    }
    result = agent.plan_and_act({'article': article})
    print("Summary generated:", bool(result.get('summary')))
    return bool(result.get('summary'))

def test_audio():
    """Test the AudioAgent."""
    print("\n=== Testing AudioAgent ===")
    agent = AudioAgent()
    task = {
        'text': 'This is a test of the audio generation system.',
        'voice': 'alloy'
    }
    result = agent.plan_and_act(task)
    print("Audio generated:", bool(result.get('audio_data')))
    return bool(result.get('audio_data'))

def test_orchestrator():
    """Test the OrchestratorAgent."""
    print("\n=== Testing OrchestratorAgent ===")
    agent = OrchestratorAgent()
    task = {
        'count': 1,
        'categories': ['technology'],
        'voice': 'alloy'
    }
    result = agent.plan_and_act(task)
    success = result['status'] == 'success'
    print("Orchestration successful:", success)
    return success

def main():
    """Run all tests."""
    print("Starting AgentToast Component Tests")
    print("=" * 50)
    
    # Create test output directory
    test_output = Path("output/test")
    test_output.mkdir(parents=True, exist_ok=True)
    
    # Run component tests
    tests = [
        ("Planner", test_planner),
        ("Fetcher", test_fetcher),
        ("Verifier", test_verifier),
        ("Summarizer", test_summarizer),
        ("Audio", test_audio),
        ("Orchestrator", test_orchestrator)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"Error in {name} test:", str(e))
            results.append((name, False))
    
    # Print summary
    print("\nTest Results Summary")
    print("=" * 50)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:12} {status}")

if __name__ == "__main__":
    main() 