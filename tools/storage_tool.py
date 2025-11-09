"""
Storage Tool for Podelli POC
Manages file storage for generated media assets
"""

import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class StorageManager:
    """Manages storage of generated assets and metadata"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.setup_directories()
        self.metadata_file = self.output_dir / "assets_metadata.json"
        self.metadata = self.load_metadata()

    def setup_directories(self):
        """Create necessary output directories"""
        directories = [
            self.output_dir / "images" / "characters",
            self.output_dir / "images" / "scenes",
            self.output_dir / "images" / "objects",
            self.output_dir / "videos" / "dialogues",
            self.output_dir / "videos" / "scenes",
            self.output_dir / "audio" / "dialogues",
            self.output_dir / "audio" / "voice_spells",
            self.output_dir / "audio" / "announcements",
            self.output_dir / "episodes"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        print(f" Storage directories created at: {self.output_dir}")

    def load_metadata(self) -> Dict[str, Any]:
        """Load existing metadata or create new"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"assets": [], "generation_sessions": []}

    def save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def generate_asset_id(self, asset_type: str, episode_id: Optional[str] = None) -> str:
        """Generate a unique asset ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        if episode_id:
            return f"{asset_type}_{episode_id}_{timestamp}_{unique_id}"
        return f"{asset_type}_{timestamp}_{unique_id}"

    def get_asset_path(
        self,
        asset_type: str,
        category: str,
        filename: str,
        extension: str
    ) -> Path:
        """
        Get the path for an asset

        Args:
            asset_type: 'images', 'videos', or 'audio'
            category: Subcategory (e.g., 'characters', 'dialogues')
            filename: Base filename
            extension: File extension (e.g., 'png', 'mp4', 'mp3')

        Returns:
            Full path for the asset
        """
        return self.output_dir / asset_type / category / f"{filename}.{extension}"

    def save_asset_metadata(self, asset_data: Dict[str, Any]):
        """Save metadata for a generated asset"""
        asset_data['saved_at'] = datetime.now().isoformat()
        self.metadata['assets'].append(asset_data)
        self.save_metadata()
        print(f" Saved metadata for asset: {asset_data.get('asset_id')}")

    def get_assets_by_episode(self, episode_id: str) -> List[Dict[str, Any]]:
        """Get all assets for a specific episode"""
        return [
            asset for asset in self.metadata['assets']
            if asset.get('episode_id') == episode_id
        ]

    def get_character_references(self) -> Dict[str, str]:
        """Get all character reference image paths"""
        character_assets = [
            asset for asset in self.metadata['assets']
            if asset.get('category') == 'character_reference'
        ]
        return {
            asset['character_id']: asset['file_path']
            for asset in character_assets
        }

    def save_episode_data(self, episode_id: str, episode_data: Dict[str, Any]):
        """Save complete episode data as JSON"""
        filename = f"{episode_id}_complete.json"
        filepath = self.output_dir / "episodes" / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False)
        print(f" Saved episode data: {filepath}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        assets = self.metadata['assets']
        return {
            "total_assets": len(assets),
            "images": len([a for a in assets if a.get('asset_type') == 'image']),
            "videos": len([a for a in assets if a.get('asset_type') == 'video']),
            "audios": len([a for a in assets if a.get('asset_type') == 'audio']),
        }
