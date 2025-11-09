"""
Podelli POC - Main Orchestrator
Generates learning content for one mission with 4 episodes
"""

import json
import os
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import validate_config, GOOGLE_API_KEY, OPENAI_API_KEY, VOICE_MAPPING
from tools.storage_tool import StorageManager
from tools.prompt_loader import PromptLoader
from agents.art_director import ArtDirectorAgent
from agents.voice_actor import VoiceActorAgent
from agents.video_director import VideoDirectorAgent


class PodelliOrchestrator:
    """Main orchestrator for Podelli content generation"""

    def __init__(self):
        print("=" * 70)
        print("<“ PODELLI POC - AGENT SYSTEM TEST")
        print("=" * 70)

        # Validate configuration
        if not validate_config():
            print("\nL Please configure your API keys in the .env file")
            sys.exit(1)

        # Initialize components
        self.storage = StorageManager("output")
        self.prompt_loader = PromptLoader("prompts")

        # Initialize agents
        print("\n=æ Initializing agents...")
        self.art_director = ArtDirectorAgent(GOOGLE_API_KEY, self.storage)
        self.voice_actor = VoiceActorAgent(OPENAI_API_KEY, self.storage, VOICE_MAPPING)
        self.video_director = VideoDirectorAgent(GOOGLE_API_KEY, self.storage)

        # Load universe data
        self.universe_data = self.load_universe_master()

        print("\n Orchestrator initialized successfully")

    def load_universe_master(self) -> dict:
        """Load the universe master JSON"""
        universe_file = Path("data/universe_master.json")

        if not universe_file.exists():
            print(f"L Universe file not found: {universe_file}")
            sys.exit(1)

        with open(universe_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f" Loaded universe: {data['universe_title']}")
        return data

    def generate_character_references(self) -> dict:
        """Generate reference images for all main characters"""
        print("\n" + "=" * 70)
        print("<¨ STEP 1: GENERATING CHARACTER REFERENCES")
        print("=" * 70)

        characters = self.universe_data['main_characters']['characters']

        # Check if already generated
        existing_refs = self.storage.get_character_references()

        if len(existing_refs) >= len(characters):
            print(f" Character references already generated ({len(existing_refs)} found)")
            return existing_refs

        # Generate characters
        result = self.art_director.generate_all_characters(characters)

        # Get updated references
        char_refs = self.storage.get_character_references()

        print(f"\n Step 1 completed: {len(char_refs)} character references ready")
        return char_refs

    def generate_episode_content(self, episode_data: dict, episode_number: int) -> dict:
        """Generate all content for one episode"""

        episode_id = episode_data['master_id']

        print("\n" + "=" * 70)
        print(f"=Ú EPISODE {episode_number}: {episode_data['title']}")
        print(f"   {episode_data['objective']}")
        print("=" * 70)

        # Get dialogue lines
        dialogue_lines = episode_data['reference_dialogue']['lines']

        # Generate audio for all dialogues
        print(f"\n<™ Generating audio for {len(dialogue_lines)} dialogue lines...")
        audio_result = self.voice_actor.generate_episode_audio(dialogue_lines, episode_id)

        # Generate videos
        print(f"\n<¬ Generating videos for {len(dialogue_lines)} dialogue lines...")
        char_refs = self.storage.get_character_references()
        video_result = self.video_director.generate_episode_videos(
            dialogue_lines,
            char_refs,
            episode_id
        )

        # Compile episode data
        episode_complete = {
            "episode_id": episode_id,
            "title": episode_data['title'],
            "title_fr": episode_data['title_fr'],
            "objective": episode_data['objective'],
            "objective_fr": episode_data['objective_fr'],
            "dialogue_lines": dialogue_lines,
            "audio_generated": audio_result['success'],
            "videos_generated": video_result['success'],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save episode data
        self.storage.save_episode_data(episode_id, episode_complete)

        print(f"\n Episode {episode_number} completed!")
        return episode_complete

    def run(self):
        """Run the complete generation pipeline"""

        start_time = time.time()

        try:
            # Step 1: Generate character references
            char_refs = self.generate_character_references()

            # Step 2: Process each episode
            mission = self.universe_data['missions'][0]
            episodes_data = []

            for idx, episode in enumerate(mission['episodes'], 1):
                episode_result = self.generate_episode_content(episode, idx)
                episodes_data.append(episode_result)

            # Final summary
            print("\n" + "=" * 70)
            print("<‰ GENERATION COMPLETE!")
            print("=" * 70)

            stats = self.storage.get_storage_stats()
            print(f"\n=Ê Statistics:")
            print(f"   Characters: {len(char_refs)}")
            print(f"   Episodes processed: {len(episodes_data)}")
            print(f"   Total images: {stats['images']}")
            print(f"   Total audio files: {stats['audios']}")
            print(f"   Total video entries: {stats['videos']}")

            duration = time.time() - start_time
            print(f"\nñ  Total generation time: {duration:.2f} seconds")

            print(f"\n=Á Output directory: ./output/")
            print(f"   - Images: ./output/images/")
            print(f"   - Audio: ./output/audio/")
            print(f"   - Videos: ./output/videos/ (mocked)")
            print(f"   - Episode data: ./output/episodes/")

            print("\n You can now view the results in the web interface")
            print("   Run: python server.py")
            print("   Then open: http://localhost:5000")

            print("\n" + "=" * 70)

        except KeyboardInterrupt:
            print("\n\n   Generation interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\nL Error during generation: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    orchestrator = PodelliOrchestrator()
    orchestrator.run()
