#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Function to show help
show_help() {
    echo "AgentToast CLI Helper"
    echo
    echo "Usage:"
    echo "  ./run.sh [command]"
    echo
    echo "Commands:"
    echo "  create <name>          Create a new user"
    echo "  show <user_id>         Show user details"
    echo "  update <user_id>       Update user preferences"
    echo "  generate <user_id>     Generate digest for user"
    echo "  list <user_id>         List user's digests"
    echo "  help                   Show this help message"
    echo
    echo "Examples:"
    echo "  ./run.sh create 'John Doe'"
    echo "  ./run.sh update abc123 --categories technology,science"
}

# Check if help is requested
if [ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ -z "$1" ]; then
    show_help
    exit 0
fi

# Execute the command
python -m agenttoast.cli "$@" 