"""
Video Director Agent - Generates videos using Veo 3.1
Note: This is a simplified mock implementation for the POC
as Veo API may have limitations or require special access
"""

import time
from pathlib import Path


class VideoDirectorAgent:
    """Generates videos using Veo 3.1 (mock implementation for POC)"""

    def __init__(self, api_key: str, storage_manager):
        self.name = "Video Director"
        self.storage = storage_manager
        print(f" [{self.name}] Initialized (Note: Veo generation is mocked for this POC)")

    def generate_dialogue_video(
        self,
        dialogue_line: dict,
        character_ref_path: str,
        episode_id: str,
        sequence_id: str
    ) -> dict:
        """Generate a video for a dialogue line (mocked for POC)"""

        print(f"<¬ [{self.name}] [MOCK] Generating video: {dialogue_line['text_fr'][:50]}...")

        try:
            filename = f"{episode_id}_{sequence_id}"
            filepath = self.storage.get_asset_path(
                'videos', 'dialogues', filename, 'mp4'
            )

            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(f"Placeholder for video: {dialogue_line['text_fr']}")

            asset_data = {
                "asset_id": self.storage.generate_asset_id("VIDEO", episode_id),
                "asset_type": "video",
                "video_type": "dialogue_clip",
                "character_id": dialogue_line['speaker'],
                "episode_id": episode_id,
                "sequence_id": sequence_id,
                "dialogue_line": dialogue_line['text_fr'],
                "reference_character_path": character_ref_path,
                "file_path": str(filepath),
                "duration_seconds": 7,
                "metadata": {
                    "aspect_ratio": "9:16",
                    "resolution": "1080p",
                    "fps": 24,
                    "note": "Mock/placeholder for POC"
                }
            }

            self.storage.save_asset_metadata(asset_data)
            print(f" [{self.name}] [MOCK] Video metadata saved")

            return {
                "success": True,
                "file_path": str(filepath),
                "asset_data": asset_data,
                "is_mock": True
            }

        except Exception as e:
            print(f"L [{self.name}] Error: {str(e)}")
            return {"success": False, "error": str(e)}
