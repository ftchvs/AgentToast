# AgentToast

AgentToast is a Python application that converts daily news into audio summaries using OpenAI's GPT and Text-to-Speech capabilities, along with the NEWS API.

## Features

- Fetches top 5 news articles daily using NEWS API
- Generates concise summaries using OpenAI GPT
- Converts summaries to audio using OpenAI Text-to-Speech
- Saves audio files organized by date

## Prerequisites

- Python 3.8 or higher
- NEWS API key (get it from [newsapi.org](https://newsapi.org))
- OpenAI API key (get it from [platform.openai.com](https://platform.openai.com))

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AgentToast.git
   cd AgentToast
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   NEWS_API_KEY=your_news_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

Run the main script to fetch news and generate audio summaries:

```bash
python src/main.py
```

Audio files will be saved in the `output/YYYY-MM-DD/` directory, organized by date.

## Testing

Run the tests using pytest:

```bash
pytest tests/
```

## Project Structure

```
AgentToast/
├── src/
│   ├── agents/
│   │   └── news_agent.py
│   └── main.py
├── tests/
│   └── test_news_agent.py
├── output/
│   └── YYYY-MM-DD/
├── requirements.txt
├── README.md
└── .env
```

## Limitations

- English language news only
- Limited to top 5 news stories
- Basic audio features

## Future Improvements

- Support for more news stories
- Category selection
- Multiple voice options
- Custom news sources

## License

MIT 