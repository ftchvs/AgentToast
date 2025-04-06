# AgentToast

A powerful multi-agent AI framework built on the OpenAI Agents SDK for comprehensive news analysis.

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key and News API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   NEWS_API_KEY=your_news_api_key_here
   ```
   Get a News API key from [newsapi.org](https://newsapi.org/)

## Usage

### Interactive CLI

The easiest way to use AgentToast is through the interactive CLI:

```bash
python cli.py
```

This will guide you through selecting news categories, agent modes, and various configuration options with a user-friendly interface.

### Running with Command Line Arguments

Alternatively, you can run the multi-agent system with command line arguments:

```bash
python run_agent.py --agent coordinator --category technology --count 3 --model gpt-4
```

#### Basic Options
- `--agent`: The agent to run (`news`, `planner`, `coordinator`, or `all`)
- `--category`: News category (general, business, technology, sports, etc.)
- `--count`: Number of articles to fetch (1-10)
- `--model`: Model to use (gpt-3.5-turbo, gpt-4, etc.)
- `--temperature`: Model temperature (0.0-1.0)
- `--verbose`: Enable verbose output
- `--trace`: Enable tracing

#### Audio Options
- `--voice`: Voice to use for audio output (alloy, echo, fable, onyx, nova, shimmer)
- `--no-audio`: Disable audio generation
- `--play-audio`: Play the audio file immediately
- `--output-dir`: Directory for saving output files
- `--summary-style`: Style of the audio summary (formal, conversational, brief)

#### Analysis Options
- `--analysis-depth`: Depth of analysis (basic, moderate, deep)
- `--no-fact-check`: Disable fact checking
- `--no-trend-analysis`: Disable trend analysis
- `--max-fact-claims`: Maximum number of fact claims to check (default: 5)

#### Output Options
- `--save-markdown`: Save the generated news summary as a Markdown file
- `--save-analysis`: Save the analysis as a separate file
- `--full-report`: Generate a comprehensive report with all agent outputs

#### Advanced News API Options
- `--country`: Two-letter country code (e.g., us, gb)
- `--sources`: Comma-separated list of news sources (e.g., bbc-news,cnn)
- `--query`: Keywords or phrase to search for
- `--page`: Page number for paginated results

### Example Commands

Run a full multi-agent analysis on technology news:
```bash
python run_agent.py --agent coordinator --category technology --count 3 --analysis-depth deep --full-report
```

Get business news with fact checking but without trend analysis:
```bash
python run_agent.py --agent coordinator --category business --no-trend-analysis
```

Get science news with a formal summary style and play the audio:
```bash
python run_agent.py --agent coordinator --category science --summary-style formal --play-audio
```

Save comprehensive analysis as separate files:
```bash
python run_agent.py --agent coordinator --category politics --save-markdown --save-analysis
```

## Features

- **Interactive CLI**: User-friendly command line interface for easy configuration
- **Multi-Agent Architecture**: Specialized agents work together for comprehensive news analysis:
  - **NewsAgent**: Fetches and processes articles from various sources
  - **AnalystAgent**: Provides deeper insights and analysis of the news
  - **FactCheckerAgent**: Verifies key claims in the articles
  - **TrendAgent**: Identifies patterns and trends across articles
  - **WriterAgent**: Creates concise, engaging summaries for audio
  - **CoordinatorAgent**: Orchestrates the entire workflow
- **Parallel Processing**: Agents run concurrently for efficient analysis
- **Intelligent Audio Summaries**: Generates accurate audio summaries that reflect the actual content of news articles
- **Customizable Analysis**: Control analysis depth and focus areas
- **Fact Checking**: Verification of key claims in news articles
- **Trend Detection**: Identification of patterns across multiple articles
- **Multiple Summary Styles**: Choose between formal, conversational, or brief summary styles
- **Markdown Formatting**: Well-structured outputs with proper formatting
- **Text-to-Speech**: Converts summaries to audio using OpenAI's TTS API
- **Multiple Voice Options**: Choose from different voices for audio output
- **Comprehensive Reports**: Generate detailed reports combining all agent outputs

## Project Structure

- `src/`: Core source code
  - `agents/`: Contains agent implementations
    - `base_agent.py`: Base agent class with tracing and common functionality
    - `example_agent.py`: News agent implementation
    - `writer_agent.py`: Writer agent for concise summaries
    - `analyst_agent.py`: Analysis agent for deeper insights
    - `fact_checker_agent.py`: Fact checking agent for verification
    - `trend_agent.py`: Trend detection agent for patterns
    - `coordinator_agent.py`: Multi-agent coordinator
    - `planner_agent.py`: Planning agent for workflow orchestration
  - `tools/`: Contains tool implementations
    - `news_tool.py`: Tool for fetching news from NewsAPI
    - `sentiment_tool.py`: Tool for sentiment analysis of news content
  - `utils/`: Utility functions and helpers
    - `tts.py`: Text-to-speech utilities for audio generation
    - `tracing.py`: Utilities for tracing agent execution
  - `config.py`: Configuration settings for the application
  - `main.py`: Main entry point for the application
- `run_agent.py`: Command-line entry point for running agents
- `cli.py`: Interactive CLI interface for easy configuration
- `output/`: Directory where output files are saved
- `tests/`: Unit tests for the application
- `requirements.txt`: Dependencies for the project

## Development

### Adding New Agents

1. Create a new file in `src/agents/` with your agent class
2. Extend the `BaseAgent` class
3. Implement the required methods
4. Update the coordinator to use your new agent

### System Architecture

The system uses a team of specialized agents coordinated by a central coordinator:

1. **NewsAgent**: Fetches articles and creates initial summary
2. **AnalystAgent**, **FactCheckerAgent**, and **TrendAgent** run in parallel:
   - **AnalystAgent**: Analyzes the news for insights and implications
   - **FactCheckerAgent**: Verifies key claims in the articles
   - **TrendAgent**: Identifies patterns and connections
3. **WriterAgent**: Creates a concise summary for audio output that accurately reflects the news content
4. **CoordinatorAgent**: Orchestrates the workflow and consolidates results

### Testing

The project includes a unit test suite in the `tests/` directory. To run the tests:

```bash
pytest
```

### Key Features

- **Enhanced Audio Summaries**: Audio summaries accurately reflect the actual content of the news articles
- **Context-Aware Writer**: The WriterAgent uses additional context from analysis and fact-checking to create more informative summaries
- **Parallel Processing**: Analysis, fact-checking, and trend detection run simultaneously for efficiency
- **Flexible Output Options**: Generate everything from brief audio summaries to comprehensive written reports
- **Custom Summary Styles**: Choose between formal, conversational, or brief summary styles to match your preference 