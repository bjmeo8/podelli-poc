"""
ART DIRECTOR AGENT
Generates character images and scene backgrounds using Nano Banana (gemini-2.5-flash-image)
"""
import time
import json
from typing import Dict, Any, List
from loguru import logger
from google import genai
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import settings


class ArtDirectorAgent(BaseAgent):
    """
    Generates visual assets using Nano Banana (Gemini 2.5 Flash Image)
    Ensures character consistency across scenes
    """

    def __init__(self):
        super().__init__("ART_DIRECTOR")

        # Initialize Gemini for image generation (Nano Banana)
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.image_model = settings.NANO_BANANA_MODEL

        logger.info(f"🎨 Art Director initialized with {self.image_model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate character images and scene backgrounds

        Input:
            - script: English script with character descriptions
            - translated_script: Translated script
            - episode_id: Episode ID

        Output:
            - character_images: Dict mapping character_id to image path
            - scene_backgrounds: Dict mapping sequence_id to background image path
        """
        start_time = time.time()

        try:
            script = input_data["script"]
            episode_id = input_data["episode_id"]

            logger.info(f"🎨 Generating visual assets for {episode_id}...")

            character_images = {}
            scene_backgrounds = {}

            # 1. Generate character images (for consistency)
            for character in script["characters"]:
                character_id = character["character_id"]
                logger.info(f"  → Generating character: {character_id}")

                image_path = await self._generate_character_image(
                    character,
                    episode_id
                )
                character_images[character_id] = image_path

            # 2. Generate scene backgrounds
            for sequence in script["sequences"]:
                sequence_id = sequence["sequence_id"]
                logger.info(f"  → Generating scene: {sequence_id}")

                background_path = await self._generate_scene_background(
                    sequence,
                    episode_id
                )
                scene_backgrounds[sequence_id] = background_path

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Generated {len(character_images)} characters and {len(scene_backgrounds)} scenes in {duration:.2f}s")

            return {
                "success": True,
                "character_images": character_images,
                "scene_backgrounds": scene_backgrounds,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Art Director error: {str(e)}")
            raise

    async def _generate_character_image(
        self,
        character: Dict[str, Any],
        episode_id: str
    ) -> str:
        """Generate character portrait using Nano Banana"""
        character_id = character["character_id"]
        visual_desc = character["visual_description"]

        # Create prompt for character portrait
        prompt = f"""Portrait of {character['role']}: {visual_desc}

Style: Realistic, friendly, educational illustration
Format: Portrait 9:16 aspect ratio
Lighting: Soft, natural lighting
Background: Simple, neutral background that doesn't distract from the character
Expression: Friendly and welcoming
Quality: High detail, professional character design suitable for language learning"""

        # Generate image using Nano Banana
        response = self.client.models.generate_images(
            model=self.image_model,
            prompt=prompt,
            config=genai.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high"
            )
        )

        # Save image
        output_dir = settings.OUTPUT_DIR / "images" / "characters" / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)

        image_path = output_dir / f"{character_id}.png"

        # Get image data and save
        if response.generated_images:
            image_data = response.generated_images[0].image.data
            with open(image_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"    💾 Saved {character_id} → {image_path}")
            return str(image_path)
        else:
            raise Exception(f"No image generated for {character_id}")

    async def _generate_scene_background(
        self,
        sequence: Dict[str, Any],
        episode_id: str
    ) -> str:
        """Generate scene background using Nano Banana"""
        sequence_id = sequence["sequence_id"]
        scene_visual = sequence["scene_visual"]

        # Create prompt for scene background
        prompt = f"""Scene background: {scene_visual}

Style: Realistic, immersive environment for language learning
Format: Vertical 9:16 aspect ratio suitable for mobile
Atmosphere: {sequence.get('scene_description', '')}
Quality: High detail, professional background illustration
Focus: Clear, uncluttered composition that works as a video background"""

        # Generate image using Nano Banana
        response = self.client.models.generate_images(
            model=self.image_model,
            prompt=prompt,
            config=genai.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high"
            )
        )

        # Save image
        output_dir = settings.OUTPUT_DIR / "images" / "scenes" / episode_id
        output_dir.mkdir(parents=True, exist_ok=True)

        image_path = output_dir / f"{sequence_id}_background.png"

        # Get image data and save
        if response.generated_images:
            image_data = response.generated_images[0].image.data
            with open(image_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"    💾 Saved {sequence_id} background → {image_path}")
            return str(image_path)
        else:
            raise Exception(f"No background generated for {sequence_id}")
