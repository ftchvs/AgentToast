import pytest
from agenttoast.agents.content_filter import ContentFilterAgent, ContentQuality

def test_content_filter_initialization():
    """Test ContentFilterAgent initialization."""
    agent = ContentFilterAgent()
    assert agent is not None
    assert isinstance(agent, ContentFilterAgent)

def test_duplicate_detection(sample_articles):
    """Test duplicate content detection."""
    agent = ContentFilterAgent()
    
    # Test with identical articles
    duplicate_articles = sample_articles + [sample_articles[0]]  # Add a duplicate
    quality = agent.check_duplicates(duplicate_articles[0], duplicate_articles)
    assert quality < 1.0, "Should detect duplicate article"
    
    # Test with unique articles
    quality = agent.check_duplicates(sample_articles[0], [sample_articles[1]])
    assert quality == 1.0, "Should not detect duplicate for unique articles"

def test_sentiment_analysis(sample_article):
    """Test sentiment analysis functionality."""
    agent = ContentFilterAgent()
    sentiment_score = agent.analyze_sentiment(sample_article["content"])
    assert -1.0 <= sentiment_score <= 1.0, "Sentiment score should be between -1 and 1"

def test_nsfw_content_check(sample_article):
    """Test NSFW content detection."""
    agent = ContentFilterAgent()
    nsfw_score = agent.check_nsfw_content(sample_article["content"])
    assert 0.0 <= nsfw_score <= 1.0, "NSFW score should be between 0 and 1"

def test_category_verification(sample_article):
    """Test category verification."""
    agent = ContentFilterAgent()
    category_confidence = agent.verify_category(
        sample_article["content"],
        expected_category="technology"
    )
    assert 0.0 <= category_confidence <= 1.0, "Category confidence should be between 0 and 1"

def test_bias_analysis(sample_article):
    """Test bias detection in content."""
    agent = ContentFilterAgent()
    bias_score = agent.analyze_bias(sample_article["content"])
    assert 0.0 <= bias_score <= 1.0, "Bias score should be between 0 and 1"

def test_quality_score_calculation(sample_article):
    """Test overall quality score calculation."""
    agent = ContentFilterAgent()
    quality_score = agent.calculate_quality_score(ContentQuality(
        duplicate_score=1.0,
        sentiment_score=0.5,
        nsfw_score=0.1,
        category_confidence=0.8,
        bias_score=0.3
    ))
    assert 0.0 <= quality_score <= 1.0, "Quality score should be between 0 and 1"

def test_article_assessment(sample_article):
    """Test complete article assessment."""
    agent = ContentFilterAgent()
    quality = agent.assess_article(sample_article, expected_category="technology")
    assert isinstance(quality, ContentQuality)
    assert hasattr(quality, 'overall_score')
    assert 0.0 <= quality.overall_score <= 1.0

def test_filter_articles(sample_articles):
    """Test filtering of multiple articles."""
    agent = ContentFilterAgent()
    filtered_articles = agent.run(sample_articles, expected_category="technology")
    assert isinstance(filtered_articles, list)
    assert len(filtered_articles) <= len(sample_articles) 