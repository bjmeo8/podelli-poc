"""
PHONETICS AGENT
Generates Voice Spell content with phonetic transcriptions
"""
import time
import json
from typing import Dict, Any, List
from loguru import logger
from google import genai
from openai import OpenAI
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import settings


class PhoneticsAgent(BaseAgent):
    """
    Creates Voice Spell videos with intuitive phonetic transcriptions
    """

    def __init__(self):
        super().__init__("PHONETICS")

        # Initialize clients
        self.genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        logger.info(f"🗣️ Phonetics Agent initialized")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Voice Spell content

        Input:
            - translated_script: Translated script
            - target_language: Target language code
            - episode_id: Episode ID

        Output:
            - voice_spells: List of Voice Spell actions with phonetics and audio
        """
        start_time = time.time()

        try:
            translated_script = input_data["translated_script"]
            target_language = input_data["target_language"]
            episode_id = input_data["episode_id"]

            logger.info(f"🗣️ Generating Voice Spell content for {episode_id}...")

            voice_spells = []

            # Extract key phrases from each sequence
            for sequence in translated_script["sequences"]:
                key_phrases = self._extract_key_phrases(sequence)

                for phrase_data in key_phrases:
                    # Generate phonetic transcription
                    phonetics = await self._generate_phonetics(
                        phrase_data["text"],
                        target_language
                    )

                    # Generate slow audio
                    audio_path = await self._generate_slow_audio(
                        phrase_data["text"],
                        target_language,
                        episode_id
                    )

                    voice_spell = {
                        "action_type": "VOICE_SPELL",
                        "sequence_id": sequence["sequence_id"],
                        "phrase": phrase_data["text"],
                        "phonetic_transcription": phonetics,
                        "translation": phrase_data.get("translation", ""),
                        "slow_audio": audio_path,
                        "teaching_note": phrase_data.get("teaching_note", "")
                    }

                    voice_spells.append(voice_spell)

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Generated {len(voice_spells)} Voice Spells in {duration:.2f}s")

            return {
                "success": True,
                "voice_spells": voice_spells,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Phonetics error: {str(e)}")
            raise

    def _extract_key_phrases(self, sequence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract 2-3 key phrases from the sequence for Voice Spells"""
        key_phrases = []

        # Get vocabulary-focused phrases
        for dialogue_line in sequence["dialogue"][:3]:  # Max 3 per sequence
            key_phrases.append({
                "text": dialogue_line["text"],
                "teaching_note": dialogue_line.get("teaching_note", "")
            })

        return key_phrases

    async def _generate_phonetics(self, text: str, language: str) -> str:
        """Generate intuitive phonetic transcription using Gemini"""
        
        prompt = f"""Generate an intuitive phonetic transcription for this {language} phrase.

Phrase: "{text}"

Create a phonetic guide that helps English speakers pronounce this correctly.
Use simple English-like spelling that shows how to pronounce each word.

Example (French):
Input: "Bonjour, comment allez-vous?"
Output: "bon-ZHOOR, koh-MAWN tah-lay-VOO"

Return ONLY the phonetic transcription, nothing else."""

        response = self.genai_client.models.generate_content(
            model=settings.GEMINI_TEXT_MODEL_FAST,
            contents=prompt,
            config=genai.GenerateContentConfig(temperature=0.3)
        )

        return response.text.strip()

    async def _generate_slow_audio(
        self,
        text: str,
        language: str,
        episode_id: str
    ) -> str:
        """Generate slow, clear audio for pronunciation practice"""
        
        # Use TTS with specific instructions for slow, clear speech
        response = self.openai_client.audio.speech.create(
            model=settings.OPENAI_TTS_MODEL,
            voice="nova",  # Clear, neutral voice
            input=text,
            speed=0.75  # Slower for learning
        )

        # Save audio
        output_dir = settings.OUTPUT_DIR / "audio" / "voice_spells" / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create unique filename
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_path = output_dir / f"spell_{text_hash}.mp3"

        response.stream_to_file(str(audio_path))

        logger.info(f"    💾 Saved Voice Spell audio → {audio_path}")
        return str(audio_path)
