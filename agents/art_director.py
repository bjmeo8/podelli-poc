"""
Art Director Agent - Generates images using Imagen 3
"""

import time
import os
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO


class ArtDirectorAgent:
    """Generates visual assets using Imagen 3"""

    def __init__(self, api_key: str, storage_manager):
        self.name = "Art Director"
        self.client = genai.Client(api_key=api_key)
        self.storage = storage_manager
        print(f" [{self.name}] Initialized with Imagen 3")

    def generate_character_reference(self, character_data: dict) -> dict:
        """Generate a reference image for a character"""
        print(f"<¨ [{self.name}] Generating character: {character_data['name']}")

        prompt = character_data.get('visual_prompt', '')

        try:
            # Generate image with Imagen 3
            response = self.client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    aspect_ratio='9:16',
                    number_of_images=1
                )
            )

            # Save image
            for generated_image in response.generated_images:
                image = Image.open(BytesIO(generated_image.image.image_bytes))

                # Save to file
                filename = f"{character_data['id']}.png"
                filepath = self.storage.get_asset_path(
                    'images', 'characters', character_data['id'], 'png'
                )

                filepath.parent.mkdir(parents=True, exist_ok=True)
                image.save(filepath)

                # Save metadata
                asset_data = {
                    "asset_id": self.storage.generate_asset_id("IMAGE", character_data['id']),
                    "asset_type": "image",
                    "category": "character_reference",
                    "character_id": character_data['id'],
                    "file_path": str(filepath),
                    "prompt_used": prompt,
                    "metadata": {
                        "aspect_ratio": "9:16",
                        "character_name": character_data['name']
                    }
                }

                self.storage.save_asset_metadata(asset_data)

                print(f" [{self.name}] Character saved: {filepath}")

                return {
                    "success": True,
                    "character_id": character_data['id'],
                    "file_path": str(filepath),
                    "asset_data": asset_data
                }

        except Exception as e:
            print(f"L [{self.name}] Error generating character: {str(e)}")
            return {"success": False, "error": str(e)}

    def generate_all_characters(self, characters_list: list) -> dict:
        """Generate all character references"""
        print(f"<¨ [{self.name}] Generating {len(characters_list)} characters...")

        results = []
        for character in characters_list:
            result = self.generate_character_reference(character)
            results.append(result)
            time.sleep(2)  # Rate limiting

        successful = sum(1 for r in results if r.get('success'))
        print(f" [{self.name}] Generated {successful}/{len(characters_list)} characters")

        return {
            "success": successful == len(characters_list),
            "results": results,
            "characters_generated": successful
        }
