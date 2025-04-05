import os
from dotenv import load_dotenv
import openai
from newsapi import NewsApiClient

def test_environment_setup():
    # Load environment variables
    load_dotenv()
    
    # Test OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    assert openai_key is not None, "OpenAI API key not found in .env"
    openai.api_key = openai_key
    
    try:
        # Simple API call to verify OpenAI key
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=10
        )
        assert response is not None
        print("✓ OpenAI API key is valid")
    except Exception as e:
        print(f"✗ OpenAI API error: {str(e)}")
        assert False, "OpenAI API test failed"

    # Test News API key
    news_key = os.getenv('NEWS_API_KEY')
    assert news_key is not None, "News API key not found in .env"
    
    try:
        # Simple API call to verify News API key
        newsapi = NewsApiClient(api_key=news_key)
        response = newsapi.get_top_headlines(language='en', page_size=1)
        assert response is not None
        assert 'articles' in response
        print("✓ News API key is valid")
    except Exception as e:
        print(f"✗ News API error: {str(e)}")
        assert False, "News API test failed"

if __name__ == '__main__':
    test_environment_setup() 