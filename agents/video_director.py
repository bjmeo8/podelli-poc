"""
VIDEO DIRECTOR AGENT
Generates dialogue videos using Veo 3.1
"""
import time
import json
from typing import Dict, Any
from loguru import logger
from google import genai
from google.genai import types
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import settings


class VideoDirectorAgent(BaseAgent):
    """
    Generates videos using Google Veo 3.1
    Creates dialogue scenes with character consistency
    """

    def __init__(self):
        super().__init__("VIDEO_DIRECTOR")

        # Initialize Gemini client for Veo
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.video_model = settings.VEO_FAST_MODEL  # Use fast model for POC

        logger.info(f"🎬 Video Director initialized with {self.video_model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate dialogue videos for sequences

        Input:
            - translated_script: Translated script
            - character_images: Character reference images
            - scene_backgrounds: Scene background images
            - audio_files: Generated audio files
            - episode_id: Episode ID

        Output:
            - video_files: Dict mapping sequence_id to video file paths
        """
        start_time = time.time()

        try:
            translated_script = input_data["translated_script"]
            character_images = input_data["character_images"]
            scene_backgrounds = input_data["scene_backgrounds"]
            episode_id = input_data["episode_id"]

            logger.info(f"🎬 Generating videos for {episode_id}...")

            video_files = {}

            # Generate video for each sequence
            for sequence in translated_script["sequences"]:
                sequence_id = sequence["sequence_id"]
                logger.info(f"  → Generating video for {sequence_id}")

                video_path = await self._generate_sequence_video(
                    sequence=sequence,
                    character_images=character_images,
                    scene_background=scene_backgrounds.get(sequence_id),
                    episode_id=episode_id
                )

                video_files[sequence_id] = video_path

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Generated {len(video_files)} videos in {duration:.2f}s")

            return {
                "success": True,
                "video_files": video_files,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Video Director error: {str(e)}")
            raise

    async def _generate_sequence_video(
        self,
        sequence: Dict[str, Any],
        character_images: Dict[str, str],
        scene_background: str,
        episode_id: str
    ) -> str:
        """Generate video for a single sequence using Veo 3.1"""
        sequence_id = sequence["sequence_id"]

        # Build video generation prompt
        prompt = self._create_video_prompt(sequence)

        # Load reference images
        reference_images = []

        # Add scene background
        if scene_background:
            with open(scene_background, 'rb') as f:
                reference_images.append(types.Part.from_bytes(
                    data=f.read(),
                    mime_type="image/png"
                ))

        # Add character images
        for dialogue_line in sequence["dialogue"]:
            character_id = dialogue_line["character_id"]
            if character_id in character_images:
                char_img_path = character_images[character_id]
                with open(char_img_path, 'rb') as f:
                    img_data = f.read()
                    # Only add if not already added
                    if not any(img for img in reference_images if len(img.inline_data.data) == len(img_data)):
                        reference_images.append(types.Part.from_bytes(
                            data=img_data,
                            mime_type="image/png"
                        ))

        # Generate video using Veo 3.1
        logger.info(f"    📹 Calling Veo 3.1 for {sequence_id}...")

        operation = self.client.models.generate_videos(
            model=self.video_model,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                reference_images=reference_images[:3] if len(reference_images) > 0 else None,
                duration=8,  # 8 seconds
                aspect_ratio="9:16",
                generate_native_audio=True
            )
        )

        # Wait for video generation to complete
        logger.info(f"    ⏳ Waiting for video generation...")
        operation.result()

        # Get video data
        video_data = None
        if operation.done() and operation.response.generated_videos:
            video_data = operation.response.generated_videos[0].video.data

        if not video_data:
            raise Exception(f"Failed to generate video for {sequence_id}")

        # Save video
        output_dir = settings.OUTPUT_DIR / "videos" / "sequences" / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)

        video_path = output_dir / f"{sequence_id}.mp4"

        with open(video_path, 'wb') as f:
            f.write(video_data)

        logger.info(f"    💾 Saved video → {video_path}")
        return str(video_path)

    def _create_video_prompt(self, sequence: Dict[str, Any]) -> str:
        """Create video generation prompt for Veo"""
        scene_desc = sequence["scene_description"]

        # Build dialogue text for context
        dialogue_text = "\n".join([
            f"- {line.get('character_id', 'Speaker')}: {line['text']}"
            for line in sequence["dialogue"]
        ])

        prompt = f"""Create a realistic dialogue scene for language learning.

Setting: {scene_desc}

Dialogue:
{dialogue_text}

Style:
- Cinematic, realistic portrayal
- Natural character expressions and gestures
- Characters speaking the dialogue naturally
- Vertical 9:16 mobile format
- Soft, natural lighting
- Camera focuses on characters during dialogue
- Appropriate for educational context

Duration: 8 seconds
With synchronized character lip movements and natural audio."""

        return prompt
