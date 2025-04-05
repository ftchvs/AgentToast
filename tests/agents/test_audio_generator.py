"""Tests for AudioGeneratorAgent."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from agenttoast.agents.audio_generator import AudioGeneratorAgent
from agenttoast.db.models import Summary, Article

@pytest.fixture
def audio_generator(mock_settings):
    """Fixture for AudioGeneratorAgent with mocked OpenAI client."""
    agent = AudioGeneratorAgent()
    agent.client.audio.speech.create = MagicMock()
    agent.client.audio.speech.create.return_value.content = b"test_audio_content"
    return agent

@pytest.fixture
def test_summary(test_article):
    """Fixture for a test summary."""
    return Summary(
        article=test_article,
        content="This is a test summary of the article.",
        tokens=20,
        cost=0.002
    )

@pytest.mark.asyncio
async def test_generate_audio_success(audio_generator, test_summary, mock_settings):
    """Test successful audio generation from a summary."""
    audio_path = await audio_generator.generate_audio(test_summary)
    
    assert audio_path is not None
    assert isinstance(audio_path, Path)
    assert audio_path.exists()
    assert audio_path.stat().st_size > 0
    
    # Verify OpenAI API was called correctly
    audio_generator.client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice="alloy",
        input=test_summary.content
    )

@pytest.mark.asyncio
async def test_generate_audio_error(audio_generator, test_summary):
    """Test error handling during audio generation."""
    # Simulate API error
    audio_generator.client.audio.speech.create.side_effect = Exception("API Error")
    
    audio_path = await audio_generator.generate_audio(test_summary)
    assert audio_path is None

@pytest.mark.asyncio
async def test_run_with_multiple_summaries(audio_generator, test_summary):
    """Test audio generation for multiple summaries."""
    summaries = [test_summary, test_summary]  # Use the same summary twice for testing
    audio_paths = await audio_generator.run(summaries)
    
    assert len(audio_paths) == 2
    for path in audio_paths:
        assert path is not None
        assert isinstance(path, Path)
        assert path.exists()
        assert path.stat().st_size > 0

@pytest.mark.asyncio
async def test_run_with_empty_list(audio_generator):
    """Test behavior when no summaries are provided."""
    audio_paths = await audio_generator.run([])
    assert len(audio_paths) == 0

@pytest.mark.asyncio
async def test_run_with_partial_failures(audio_generator, test_summary):
    """Test handling of partial failures during audio generation."""
    # Create two summaries, make the second one fail
    summaries = [test_summary, test_summary]
    
    def mock_generate(*args, **kwargs):
        # Fail on second call
        if mock_generate.calls == 0:
            mock_generate.calls += 1
            return b"test_audio_content"
        raise Exception("API Error")
    
    mock_generate.calls = 0
    audio_generator.client.audio.speech.create.side_effect = mock_generate
    
    audio_paths = await audio_generator.run(summaries)
    
    # Should have one successful path and one None
    assert len(audio_paths) == 2
    assert audio_paths[0] is not None
    assert audio_paths[1] is None

@pytest.mark.asyncio
async def test_custom_voice_setting(audio_generator, test_summary, mock_settings):
    """Test audio generation with custom voice setting."""
    custom_voice = "nova"
    audio_generator.voice = custom_voice
    
    await audio_generator.generate_audio(test_summary)
    
    # Verify the custom voice was used
    audio_generator.client.audio.speech.create.assert_called_once_with(
        model="tts-1",
        voice=custom_voice,
        input=test_summary.content
    ) 