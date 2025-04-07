#!/bin/bash
# Script to generate and visualize agent diagrams

echo "📊 AgentToast Agent Visualization Tool"
echo "======================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python to use this tool."
    exit 1
fi

# Check if generate_agent_diagram.py exists
if [ -f "generate_agent_diagram.py" ]; then
    echo "🔍 Analyzing agent code structure..."
    python generate_agent_diagram.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Error generating diagrams from code."
        echo "Continuing with existing diagrams..."
    else
        echo "✅ Generated detailed agent diagrams in agent_diagram_detailed.md"
    fi
else
    echo "ℹ️ Code analyzer not found, skipping automatic diagram generation."
fi

# Function to open a file in the default browser
open_browser() {
    if [ "$(uname)" == "Darwin" ]; then  # macOS
        open "$1"
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then  # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open "$1"
        else
            echo "❌ Could not open browser automatically. Please open $1 manually."
        fi
    elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then  # Windows
        start "$1"
    else
        echo "❌ Could not open browser automatically. Please open $1 manually."
    fi
}

echo ""
echo "📋 Available Diagram Options:"
echo "1) Interactive D3.js Visualization"
echo "2) Static Mermaid Diagrams"
echo "3) Auto-generated Detailed Diagrams (if available)"
echo "4) Exit"

read -p "Select option (1-4): " choice

case $choice in
    1)
        if [ -f "agent_diagram.html" ]; then
            echo "🌐 Opening interactive diagram in browser..."
            open_browser "agent_diagram.html"
        else
            echo "❌ Interactive diagram file not found."
        fi
        ;;
    2)
        if [ -f "agent_diagram.md" ]; then
            echo "📄 Opening Mermaid diagrams..."
            
            # Try to use VS Code if available (good Mermaid support)
            if command -v code &> /dev/null; then
                code "agent_diagram.md"
            else
                # Fallback to regular text editor
                if [ "$(uname)" == "Darwin" ]; then  # macOS
                    open "agent_diagram.md"
                elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then  # Linux
                    if command -v xdg-open &> /dev/null; then
                        xdg-open "agent_diagram.md"
                    else
                        echo "❌ Could not open editor automatically. Please open agent_diagram.md manually."
                    fi
                elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then  # Windows
                    start "agent_diagram.md"
                else
                    echo "❌ Could not open editor automatically. Please open agent_diagram.md manually."
                fi
            fi
        else
            echo "❌ Mermaid diagram file not found."
        fi
        ;;
    3)
        if [ -f "agent_diagram_detailed.md" ]; then
            echo "📄 Opening auto-generated diagrams..."
            
            # Try to use VS Code if available (good Mermaid support)
            if command -v code &> /dev/null; then
                code "agent_diagram_detailed.md"
            else
                # Fallback to regular text editor
                if [ "$(uname)" == "Darwin" ]; then  # macOS
                    open "agent_diagram_detailed.md"
                elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then  # Linux
                    if command -v xdg-open &> /dev/null; then
                        xdg-open "agent_diagram_detailed.md"
                    else
                        echo "❌ Could not open editor automatically. Please open agent_diagram_detailed.md manually."
                    fi
                elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ] || [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then  # Windows
                    start "agent_diagram_detailed.md"
                else
                    echo "❌ Could not open editor automatically. Please open agent_diagram_detailed.md manually."
                fi
            fi
        else
            echo "❌ Auto-generated diagram file not found. Try running the script with option 1 first."
        fi
        ;;
    4)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid option. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "🎉 Done! You can run this script again to view other diagram types." 