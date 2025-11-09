"""
ORCHESTRATOR AGENT
Coordinates all agents to generate complete episode content
"""
import json
import time
from typing import Dict, Any, List
from loguru import logger
from pathlib import Path

from agents.storyteller import StorytellerAgent
from agents.translator import TranslatorAgent
from agents.art_director import ArtDirectorAgent
from agents.voice_actor import VoiceActorAgent
from agents.video_director import VideoDirectorAgent
from agents.phonetics import PhoneticsAgent
from agents.quiz_master import QuizMasterAgent
from config.settings import settings


class OrchestratorAgent:
    """
    Main orchestrator that coordinates all specialized agents
    to generate complete episode content
    """

    def __init__(self):
        self.agent_name = "ORCHESTRATOR"
        logger.info("<¯ Initializing Orchestrator Agent...")

        # Initialize all specialized agents
        self.storyteller = StorytellerAgent()
        self.translator = TranslatorAgent()
        self.art_director = ArtDirectorAgent()
        self.voice_actor = VoiceActorAgent()
        self.video_director = VideoDirectorAgent()
        self.phonetics = PhoneticsAgent()
        self.quiz_master = QuizMasterAgent()

        # Load universe master
        self.universe_data = self._load_universe_master()

        logger.success(" Orchestrator initialized with all agents")

    def _load_universe_master(self) -> Dict[str, Any]:
        """Load the universe master JSON"""
        with open(settings.UNIVERSE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def generate_episode(
        self,
        mission_id: str,
        episode_id: str,
        target_language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Generate complete episode content for a specific language

        Args:
            mission_id: ID of the mission (e.g., "M1_AIRPORT")
            episode_id: ID of the episode (e.g., "M1_E1_PASSPORT")
            target_language: Target language code (e.g., "fr")

        Returns:
            Complete episode data with all generated content
        """
        start_time = time.time()
        logger.info(f"\n{'='*80}")
        logger.info(f"=€ STARTING EPISODE GENERATION")
        logger.info(f"   Mission: {mission_id}")
        logger.info(f"   Episode: {episode_id}")
        logger.info(f"   Language: {target_language}")
        logger.info(f"{'='*80}\n")

        try:
            # 1. FIND EPISODE IN MASTER JSON
            mission_data, episode_data = self._find_episode(mission_id, episode_id)

            # 2. STORYTELLER: Generate complete script in English
            logger.info("\n=Ö STEP 1: Generating episode script (English)...")
            script_result = await self.storyteller.process({
                "mission": mission_data,
                "episode": episode_data,
                "cefr_level": mission_data["cefr_level"]
            })
            script = script_result["script"]

            # 3. TRANSLATOR: Translate to target language
            logger.info(f"\n< STEP 2: Translating script to {target_language}...")
            translation_result = await self.translator.process({
                "script": script,
                "target_language": target_language
            })
            translated_script = translation_result["translated_script"]

            # 4. ART DIRECTOR: Generate character images and scene backgrounds
            logger.info("\n<¨ STEP 3: Generating character images and scenes...")
            art_result = await self.art_director.process({
                "script": script,
                "translated_script": translated_script,
                "episode_id": episode_id
            })
            character_images = art_result["character_images"]
            scene_backgrounds = art_result["scene_backgrounds"]

            # 5. VOICE ACTOR: Generate dialogue audio
            logger.info(f"\n<¤ STEP 4: Generating dialogue audio ({target_language})...")
            voice_result = await self.voice_actor.process({
                "translated_script": translated_script,
                "target_language": target_language,
                "episode_id": episode_id
            })
            audio_files = voice_result["audio_files"]

            # 6. VIDEO DIRECTOR: Generate dialogue videos
            logger.info("\n<¬ STEP 5: Generating dialogue videos...")
            video_result = await self.video_director.process({
                "translated_script": translated_script,
                "character_images": character_images,
                "scene_backgrounds": scene_backgrounds,
                "audio_files": audio_files,
                "episode_id": episode_id
            })
            video_files = video_result["video_files"]

            # 7. PHONETICS: Generate Voice Spell videos
            logger.info("\n=ã STEP 6: Generating Voice Spell content...")
            phonetics_result = await self.phonetics.process({
                "translated_script": translated_script,
                "target_language": target_language,
                "episode_id": episode_id
            })
            voice_spells = phonetics_result["voice_spells"]

            # 8. QUIZ MASTER: Generate quiz actions
            logger.info("\n=Ý STEP 7: Generating quiz content...")
            quiz_result = await self.quiz_master.process({
                "script": script,
                "translated_script": translated_script,
                "video_files": video_files,
                "audio_files": audio_files,
                "episode_id": episode_id
            })
            quiz_actions = quiz_result["quiz_actions"]

            # 9. COMPILE FINAL EPISODE DATA
            episode_output = {
                "episode_id": episode_id,
                "mission_id": mission_id,
                "language": target_language,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "script": {
                    "english": script,
                    "translated": translated_script
                },
                "characters": character_images,
                "scenes": scene_backgrounds,
                "sequences": [
                    {
                        "sequence_id": seq["sequence_id"],
                        "video": video_files.get(seq["sequence_id"]),
                        "audio": audio_files.get(seq["sequence_id"]),
                        "dialogue": seq["dialogue"],
                        "actions": [
                            action for action in quiz_actions
                            if action["sequence_id"] == seq["sequence_id"]
                        ]
                    }
                    for seq in translated_script["sequences"]
                ],
                "voice_spells": voice_spells
            }

            # Save complete episode
            self._save_episode(episode_output, episode_id, target_language)

            duration = time.time() - start_time
            logger.success(f"\n{'='*80}")
            logger.success(f" EPISODE GENERATION COMPLETE!")
            logger.success(f"   Total time: {duration:.2f}s")
            logger.success(f"   Episode: {episode_id}")
            logger.success(f"   Language: {target_language}")
            logger.success(f"{'='*80}\n")

            return {
                "success": True,
                "episode": episode_output,
                "generation_time": duration
            }

        except Exception as e:
            logger.error(f"L Error in orchestrator: {str(e)}")
            raise

    def _find_episode(self, mission_id: str, episode_id: str) -> tuple:
        """Find mission and episode data in universe master"""
        for mission in self.universe_data["missions"]:
            if mission["master_id"] == mission_id:
                for episode in mission["episodes"]:
                    if episode["master_id"] == episode_id:
                        return mission, episode
        raise ValueError(f"Episode {episode_id} not found in mission {mission_id}")

    def _save_episode(self, episode_data: Dict[str, Any], episode_id: str, language: str):
        """Save complete episode data"""
        output_dir = settings.OUTPUT_DIR / "episodes" / language
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{episode_id}_complete.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

        logger.info(f"=¾ Saved complete episode to {output_file}")

    async def generate_mission(
        self,
        mission_id: str,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """Generate all episodes for a mission in multiple languages"""
        if languages is None:
            languages = ["fr"]  # Default to French

        # Find mission
        mission_data = None
        for mission in self.universe_data["missions"]:
            if mission["master_id"] == mission_id:
                mission_data = mission
                break

        if not mission_data:
            raise ValueError(f"Mission {mission_id} not found")

        results = {
            "mission_id": mission_id,
            "languages": {},
            "total_episodes": len(mission_data["episodes"])
        }

        # Generate each episode for each language
        for language in languages:
            logger.info(f"\n< Generating mission {mission_id} for language: {language}")
            results["languages"][language] = []

            for episode in mission_data["episodes"]:
                episode_id = episode["master_id"]
                episode_result = await self.generate_episode(
                    mission_id,
                    episode_id,
                    language
                )
                results["languages"][language].append({
                    "episode_id": episode_id,
                    "success": episode_result["success"],
                    "generation_time": episode_result["generation_time"]
                })

        return results
