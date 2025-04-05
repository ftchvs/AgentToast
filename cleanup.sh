#!/bin/bash
# Cleanup script to remove files that are no longer needed
# Run this after testing confirms the new implementation works correctly

echo "WARNING: This will remove files that are no longer needed."
echo "Make sure you have tested the new implementation first!"
read -p "Are you sure you want to proceed? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Removing old agent files..."
    
    # Remove old agent files that are no longer needed
    rm -f src/agents/orchestrator_agent.py
    rm -f src/agents/summarizer_agent.py
    rm -f src/agents/audio_agent.py
    rm -f src/agents/verifier_agent.py
    rm -f src/agents/fetcher_agent.py
    
    # Clean up __pycache__ directories
    find src -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
    
    echo "Done!"
else
    echo "Cleanup cancelled."
fi 