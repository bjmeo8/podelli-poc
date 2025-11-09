"""
Voice Actor Agent - Generates TTS audio using OpenAI
"""

import time
from pathlib import Path
from openai import OpenAI


class VoiceActorAgent:
    """Generates audio using OpenAI TTS"""

    def __init__(self, api_key: str, storage_manager, voice_mapping: dict):
        self.name = "Voice Actor"
        self.client = OpenAI(api_key=api_key)
        self.storage = storage_manager
        self.voice_mapping = voice_mapping
        print(f" [{self.name}] Initialized with OpenAI TTS")

    def generate_dialogue_audio(
        self,
        text: str,
        character_id: str,
        episode_id: str,
        sequence_id: str,
        audio_type: str = "dialogue"
    ) -> dict:
        """Generate TTS audio for a dialogue line"""

        print(f"<™ [{self.name}] Generating audio: {text[:50]}...")

        # Get voice for character
        voice = self.voice_mapping.get(character_id, "alloy")

        # Adjust speed for voice spells
        speed = 0.85 if audio_type == "voice_spell" else 1.0

        try:
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=speed
            )

            # Save audio file
            filename = f"{episode_id}_{sequence_id}_{character_id}"
            category = "voice_spells" if audio_type == "voice_spell" else "dialogues"
            filepath = self.storage.get_asset_path(
                'audio', category, filename, 'mp3'
            )

            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Stream to file
            response.stream_to_file(str(filepath))

            # Save metadata
            asset_data = {
                "asset_id": self.storage.generate_asset_id("AUDIO", episode_id),
                "asset_type": "audio",
                "audio_type": audio_type,
                "character_id": character_id,
                "episode_id": episode_id,
                "sequence_id": sequence_id,
                "text": text,
                "voice_used": voice,
                "speed": speed,
                "file_path": str(filepath),
                "metadata": {
                    "format": "mp3",
                    "model": "tts-1-hd"
                }
            }

            self.storage.save_asset_metadata(asset_data)

            print(f" [{self.name}] Audio saved: {filepath}")

            return {
                "success": True,
                "file_path": str(filepath),
                "asset_data": asset_data
            }

        except Exception as e:
            print(f"L [{self.name}] Error generating audio: {str(e)}")
            return {"success": False, "error": str(e)}

    def generate_episode_audio(self, dialogue_lines: list, episode_id: str) -> dict:
        """Generate audio for all dialogue lines in an episode"""

        print(f"<™ [{self.name}] Generating audio for episode {episode_id}...")

        results = []
        for idx, line in enumerate(dialogue_lines):
            result = self.generate_dialogue_audio(
                text=line['text_fr'],
                character_id=line['speaker'],
                episode_id=episode_id,
                sequence_id=f"SEQ_{idx+1}",
                audio_type="dialogue"
            )
            results.append(result)
            time.sleep(1)  # Rate limiting

        successful = sum(1 for r in results if r.get('success'))
        print(f" [{self.name}] Generated {successful}/{len(dialogue_lines)} audio files")

        return {
            "success": successful == len(dialogue_lines),
            "results": results
        }
