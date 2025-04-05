# AgentToast

An AI-driven solution that delivers personalized audio digests of daily news using OpenAI's Agent SDK and text-to-speech capabilities.

## Features

- Automated news scraping from reliable sources
- AI-powered summarization of news articles
- High-quality text-to-speech conversion
- Personalized news selection
- Local storage of audio files and summaries in markdown format

## Project Structure

```
agenttoast/
├── agents/                 # OpenAI Agent implementations
│   ├── news_scraper.py    # News scraping agent
│   ├── summarizer.py      # Text summarization agent
│   └── audio_gen.py       # Audio generation agent
├── api/                   # FastAPI application
│   ├── routes/           # API endpoints
│   └── models/           # Pydantic models
├── core/                  # Core application logic
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging configuration
│   └── storage.py        # Local storage management
├── tasks/                # Celery tasks
│   ├── celery.py        # Celery configuration
│   └── workers.py       # Task workers
├── tests/               # Test suite
└── utils/               # Utility functions

storage/                 # Local storage directory
├── audio/              # Generated audio files
└── summaries/          # Markdown summaries
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agenttoast.git
   cd agenttoast
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. Create storage directories:
   ```bash
   mkdir -p storage/audio storage/summaries
   ```

6. Start the development server:
   ```bash
   uvicorn agenttoast.api.main:app --reload
   ```

7. Start Celery worker (in a new terminal):
   ```bash
   celery -A agenttoast.tasks.workers worker --loglevel=info
   ```

8. Start Celery beat (in a new terminal):
   ```bash
   celery -A agenttoast.tasks.workers beat --loglevel=info
   ```

## Storage Structure

- Audio files are stored in `storage/audio/` with the format: `{user_id}_{timestamp}.mp3`
- Audio metadata is stored alongside audio files as JSON: `{audio_file}.json`
- Summaries are stored in `storage/summaries/` as markdown files: `{user_id}_{timestamp}.md`

## Development

- Code formatting: `black .`
- Import sorting: `isort .`
- Type checking: `mypy .`
- Run tests: `pytest`
- Run test coverage: `pytest --cov=.`

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 