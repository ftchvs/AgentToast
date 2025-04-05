import pytest
from agenttoast.agents.language_processor import (
    LanguageProcessingAgent,
    TranslationResult,
    LanguagePreference
)

def test_language_processor_initialization():
    """Test LanguageProcessingAgent initialization."""
    agent = LanguageProcessingAgent()
    assert agent is not None
    assert isinstance(agent, LanguageProcessingAgent)

def test_language_detection():
    """Test language detection functionality."""
    agent = LanguageProcessingAgent()
    
    # Test English text
    text = "This is a test sentence in English."
    lang, confidence = agent.detect_language(text)
    assert lang == "en"
    assert 0.0 <= confidence <= 1.0
    
    # Test Spanish text
    text = "Esta es una frase de prueba en español."
    lang, confidence = agent.detect_language(text)
    assert lang == "es"
    assert 0.0 <= confidence <= 1.0

def test_text_translation():
    """Test text translation functionality."""
    agent = LanguageProcessingAgent()
    text = "Hello, this is a test message."
    
    result = agent.translate_text(
        text=text,
        source_lang="en",
        target_lang="es"
    )
    assert isinstance(result, TranslationResult)
    assert result.original_text == text
    assert result.translated_text != text
    assert result.source_lang == "en"
    assert result.target_lang == "es"
    assert result.confidence > 0.0

def test_cultural_context():
    """Test cultural context analysis."""
    agent = LanguageProcessingAgent()
    text = "The football match was excellent."
    
    context = agent._get_cultural_context(
        text=text,
        source_lang="en",
        target_lang="es"
    )
    assert isinstance(context, dict)
    assert "notes" in context
    assert len(context["notes"]) > 0

def test_content_adaptation(sample_article):
    """Test content adaptation for different languages."""
    agent = LanguageProcessingAgent()
    preference = LanguagePreference(
        user_id="test_user",
        preferred_language="es"
    )
    
    adapted_article = agent.adapt_content(
        article=sample_article,
        language_pref=preference
    )
    
    assert isinstance(adapted_article, dict)
    assert "title" in adapted_article
    assert "content" in adapted_article
    assert adapted_article["title"] != sample_article["title"]
    assert adapted_article["content"] != sample_article["content"]
    assert "translation_metadata" in adapted_article

def test_summary_adaptation(sample_article):
    """Test summary adaptation for different languages."""
    agent = LanguageProcessingAgent()
    preference = LanguagePreference(
        user_id="test_user",
        preferred_language="fr"
    )
    
    summary = "This is a test summary of the article."
    adapted_summary = agent.adapt_summary(
        summary=summary,
        language_pref=preference
    )
    
    assert isinstance(adapted_summary, dict)
    assert "text" in adapted_summary
    assert adapted_summary["text"] != summary
    assert "translation_metadata" in adapted_summary

def test_run_language_processing(sample_articles):
    """Test complete language processing pipeline."""
    agent = LanguageProcessingAgent()
    preferences = [
        LanguagePreference(user_id=f"user_{i}", preferred_language=lang)
        for i, lang in enumerate(["es", "fr", "de"])
    ]
    
    processed_content = agent.run(
        articles=sample_articles,
        language_preferences=preferences
    )
    
    assert isinstance(processed_content, dict)
    assert all(pref.user_id in processed_content for pref in preferences)
    for user_content in processed_content.values():
        assert isinstance(user_content, list)
        assert len(user_content) == len(sample_articles)
        assert all("translation_metadata" in article for article in user_content) 