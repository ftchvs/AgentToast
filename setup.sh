#!/bin/bash

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p config/users
mkdir -p data/audio
mkdir -p data/summaries

# Create example .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
OPENAI_API_KEY=your_openai_api_key
NEWS_API_KEY=your_newsapi_key
EOL
    echo "Please edit .env file with your API keys"
fi

echo "Setup complete! To start the system:"
echo "1. Edit .env with your API keys"
echo "2. Run './start.sh' to start the services"
echo "3. Use './run.sh' to interact with the system" 