"""
TRANSLATOR AGENT
Translates episode scripts to target languages while maintaining pedagogical intent
"""
import time
import json
from typing import Dict, Any
from loguru import logger
from google import genai

from agents.base_agent import BaseAgent
from config.settings import settings


class TranslatorAgent(BaseAgent):
    """
    Translates scripts from English (master) to target languages
    Uses Gemini 2.5 Pro for high-quality, context-aware translation
    """

    def __init__(self):
        super().__init__("TRANSLATOR")

        # Initialize Gemini for translation
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GEMINI_TEXT_MODEL

        # Language names for better prompts
        self.language_names = {
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese (Portugal)",
            "pt-br": "Portuguese (Brazil)",
            "en": "English"
        }

        logger.info(f"🌍 Translator initialized with {self.model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate script to target language

        Input:
            - script: English script from Storyteller
            - target_language: Target language code (e.g., "fr")

        Output:
            - translated_script: Script with all text translated
        """
        start_time = time.time()

        try:
            script = input_data["script"]
            target_language = input_data["target_language"]
            language_name = self.language_names.get(target_language, target_language)

            logger.info(f"🌍 Translating to {language_name}...")

            # Create translation prompt
            prompt = self._create_translation_prompt(script, language_name, target_language)

            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more accurate translation
                    top_p=0.95,
                    response_mime_type="application/json"
                )
            )

            # Parse response
            translated_script = json.loads(response.text)

            # Save for reference
            self.save_output(
                translated_script,
                f"translated_{script['episode_id']}_{target_language}.json",
                "translations"
            )

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Translation complete in {duration:.2f}s")

            return {
                "success": True,
                "translated_script": translated_script,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Translator error: {str(e)}")
            raise

    def _create_translation_prompt(
        self,
        script: Dict[str, Any],
        language_name: str,
        language_code: str
    ) -> str:
        """Create translation prompt"""
        script_json = json.dumps(script, ensure_ascii=False, indent=2)

        prompt = f"""You are a professional translator specializing in educational content for language learning.

# Task
Translate the following English episode script to {language_name}.

# Translation Guidelines
1. **Pedagogical Adaptation**: Translate for language learners at the specified CEFR level
2. **Natural Expression**: Use natural, everyday {language_name} that native speakers would actually use
3. **Cultural Context**: Adapt cultural references appropriately for {language_name} speakers
4. **Vocabulary Level**: Maintain appropriate complexity for the learner level
5. **Preserve Structure**: Keep the same JSON structure and all IDs unchanged
6. **Character Names**: Keep character roles but adapt names if culturally appropriate
7. **Teaching Notes**: Translate teaching notes and explain language-specific features

# Input Script (English)
{script_json}

# Output Requirements
Return the complete script with ALL text fields translated to {language_name}.
Keep the exact same JSON structure. Only translate text content, NOT field names or IDs.

Output the translated script in valid JSON format."""

        return prompt
