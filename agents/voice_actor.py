"""
VOICE ACTOR AGENT
Generates dialogue audio using GPT-4o-mini-tts
"""
import time
import json
from typing import Dict, Any, List
from loguru import logger
from openai import OpenAI
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import settings


class VoiceActorAgent(BaseAgent):
    """
    Generates speech audio using OpenAI GPT-4o-mini-tts
    Creates natural-sounding dialogue in the target language
    """

    def __init__(self):
        super().__init__("VOICE_ACTOR")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.tts_model = settings.OPENAI_TTS_MODEL

        # Voice mapping for characters
        self.voice_options = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]
        self.default_voice = "nova"

        logger.info(f"🎤 Voice Actor initialized with {self.tts_model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate dialogue audio for all sequences

        Input:
            - translated_script: Translated script with dialogues
            - target_language: Target language code
            - episode_id: Episode ID

        Output:
            - audio_files: Dict mapping sequence_id/dialogue_index to audio file paths
        """
        start_time = time.time()

        try:
            translated_script = input_data["translated_script"]
            target_language = input_data["target_language"]
            episode_id = input_data["episode_id"]

            logger.info(f"🎤 Generating audio for {episode_id} in {target_language}...")

            audio_files = {}

            # Assign voices to characters
            character_voices = self._assign_character_voices(translated_script["characters"])

            # Generate audio for each dialogue line
            for sequence in translated_script["sequences"]:
                sequence_id = sequence["sequence_id"]
                logger.info(f"  → Generating dialogue audio for {sequence_id}")

                for idx, dialogue_line in enumerate(sequence["dialogue"]):
                    character_id = dialogue_line["character_id"]
                    text = dialogue_line["text"]
                    voice = character_voices.get(character_id, self.default_voice)

                    audio_path = await self._generate_dialogue_audio(
                        text=text,
                        voice=voice,
                        episode_id=episode_id,
                        sequence_id=sequence_id,
                        dialogue_index=idx,
                        language=target_language
                    )

                    audio_key = f"{sequence_id}_dialogue_{idx}"
                    audio_files[audio_key] = audio_path

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Generated {len(audio_files)} audio files in {duration:.2f}s")

            return {
                "success": True,
                "audio_files": audio_files,
                "character_voices": character_voices,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Voice Actor error: {str(e)}")
            raise

    def _assign_character_voices(self, characters: List[Dict[str, Any]]) -> Dict[str, str]:
        """Assign distinct voices to characters"""
        character_voices = {}

        for idx, character in enumerate(characters):
            character_id = character["character_id"]
            # Rotate through available voices
            voice = self.voice_options[idx % len(self.voice_options)]
            character_voices[character_id] = voice

        return character_voices

    async def _generate_dialogue_audio(
        self,
        text: str,
        voice: str,
        episode_id: str,
        sequence_id: str,
        dialogue_index: int,
        language: str
    ) -> str:
        """Generate single dialogue audio file using GPT-4o-mini-tts"""
        
        # Call OpenAI TTS API
        response = self.client.audio.speech.create(
            model=self.tts_model,
            voice=voice,
            input=text,
            response_format="mp3"
        )

        # Save audio file
        output_dir = settings.OUTPUT_DIR / "audio" / "dialogues" / language / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_path = output_dir / f"{sequence_id}_dialogue_{dialogue_index}.mp3"

        # Save audio data
        response.stream_to_file(str(audio_path))

        logger.info(f"    💾 Saved audio → {audio_path}")
        return str(audio_path)
