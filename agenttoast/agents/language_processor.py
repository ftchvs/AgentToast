"""Language processing agent for handling multi-language support."""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

import openai
from pydantic import BaseModel
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator
from iso639_lang import Language

from ..core.config import get_settings
from ..core.logger import logger
from ..models.article import Article
from ..core.agent import Agent
from ..models.summary import Summary

settings = get_settings()

class TranslationResult(BaseModel):
    """Translation result data model."""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = 0.0
    cultural_notes: Optional[List[str]] = None

class LanguagePreference(BaseModel):
    """User language preference data model."""
    primary_language: str
    secondary_languages: List[str] = []
    regional_preferences: Dict[str, str] = {}  # region: language
    translation_enabled: bool = True

class LanguageProcessingAgent(Agent):
    """Agent for handling multi-language content processing."""

    def __init__(self):
        super().__init__()
        self.supported_languages = {
            'en': 'english',
            'es': 'spanish',
            'fr': 'french',
            'de': 'german',
            'it': 'italian',
            'pt': 'portuguese',
            'nl': 'dutch',
            'ru': 'russian',
            'ja': 'japanese',
            'ko': 'korean',
            'zh': 'chinese'
        }
        self.default_language = 'en'
        self.translator = GoogleTranslator(source='auto', target=self.default_language)

    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect the language of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple[str, float]: Language code and confidence score
        """
        try:
            # Get language detection with confidence scores
            langs = detect_langs(text)
            if langs:
                # Return the most probable language and its confidence
                return langs[0].lang, langs[0].prob
            return self.default_language, 0.0
        except LangDetectException as e:
            logger.error(f"Language detection error: {str(e)}")
            return self.default_language, 0.0

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        preserve_formatting: bool = True
    ) -> TranslationResult:
        """Translate text to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code
            preserve_formatting: Whether to preserve text formatting
            
        Returns:
            TranslationResult: Translation result with metadata
        """
        try:
            # Detect source language
            source_lang, confidence = self.detect_language(text)
            
            # Skip translation if already in target language
            if source_lang == target_lang:
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    confidence=confidence
                )
            
            # Set up translator for target language
            self.translator.target = target_lang
            
            # Translate text
            translated_text = self.translator.translate(text)
            
            # Get cultural context notes using OpenAI
            cultural_notes = await self._get_cultural_context(
                text, source_lang, target_lang
            ) if confidence > 0.8 else None
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=confidence,
                cultural_notes=cultural_notes
            )
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_lang=self.default_language,
                target_lang=target_lang,
                confidence=0.0
            )

    async def _get_cultural_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """Get cultural context notes for translation.
        
        Args:
            text: Original text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List[str]: Cultural context notes
        """
        try:
            # Use OpenAI to analyze cultural context
            response = await openai.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cultural context analyzer. Identify important "
                            "cultural elements, idioms, or references that might need "
                            "explanation when translating between languages."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Analyze this text for cultural context when translating "
                            f"from {source_lang} to {target_lang}:\n\n{text}"
                        )
                    }
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            # Extract and return cultural notes
            if response.choices:
                notes = response.choices[0].message.content.split('\n')
                return [note.strip() for note in notes if note.strip()]
            return []
            
        except Exception as e:
            logger.error(f"Cultural context analysis error: {str(e)}")
            return []

    async def adapt_content(
        self,
        article: Article,
        target_lang: str
    ) -> Article:
        """Adapt article content for target language and region.
        
        Args:
            article: Article to adapt
            target_lang: Target language code
            
        Returns:
            Article: Adapted article
        """
        # Translate title
        title_translation = await self.translate_text(
            article.title,
            target_lang
        )
        
        # Translate content
        content_translation = await self.translate_text(
            article.content,
            target_lang
        )
        
        # Create adapted article
        adapted_article = Article(
            title=title_translation.translated_text,
            content=content_translation.translated_text,
            url=article.url,
            source=article.source,
            category=article.category,
            published_at=article.published_at,
            metadata={
                "original_language": title_translation.source_lang,
                "translation_confidence": title_translation.confidence,
                "cultural_notes": content_translation.cultural_notes
            }
        )
        
        return adapted_article

    async def adapt_summary(
        self,
        summary: Summary,
        target_lang: str
    ) -> Summary:
        """Adapt summary for target language and region.
        
        Args:
            summary: Summary to adapt
            target_lang: Target language code
            
        Returns:
            Summary: Adapted summary
        """
        # Translate summary text
        translation = await self.translate_text(
            summary.text,
            target_lang
        )
        
        # Create adapted summary
        adapted_summary = Summary(
            text=translation.translated_text,
            article_id=summary.article_id,
            metadata={
                "original_language": translation.source_lang,
                "translation_confidence": translation.confidence,
                "cultural_notes": translation.cultural_notes
            }
        )
        
        return adapted_summary

    async def run(
        self,
        content: List[Article | Summary],
        language_preferences: LanguagePreference
    ) -> List[Article | Summary]:
        """Run the language processing agent.
        
        Args:
            content: List of articles or summaries to process
            language_preferences: User's language preferences
            
        Returns:
            List[Article | Summary]: Processed content in target language
        """
        if not content or not language_preferences.translation_enabled:
            return content
            
        logger.info(
            "Starting language processing",
            extra={
                "items": len(content),
                "target_language": language_preferences.primary_language
            }
        )
        
        processed_content = []
        
        for item in content:
            try:
                if isinstance(item, Article):
                    processed_item = await self.adapt_content(
                        item,
                        language_preferences.primary_language
                    )
                elif isinstance(item, Summary):
                    processed_item = await self.adapt_summary(
                        item,
                        language_preferences.primary_language
                    )
                else:
                    logger.warning(f"Unsupported content type: {type(item)}")
                    continue
                    
                processed_content.append(processed_item)
                
            except Exception as e:
                logger.error(
                    f"Error processing content: {str(e)}",
                    extra={"item_id": getattr(item, 'id', None)}
                )
                processed_content.append(item)  # Keep original on error
        
        logger.info(
            "Language processing completed",
            extra={"processed_items": len(processed_content)}
        )
        
        return processed_content 