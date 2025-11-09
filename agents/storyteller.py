"""
AGENT 1: STORYTELLER (SCENARIST)
Génère le script complet d'un épisode en JSON
"""
import time
from typing import Dict, Any
from loguru import logger
import google.generativeai as genai

from agents.base_agent import BaseAgent
from config.settings import settings

class StorytellerAgent(BaseAgent):
    """Agent de génération de scripts d'épisodes"""
    
    def __init__(self):
        super().__init__("STORYTELLER")
        
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": 0.8,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
        )
        
        logger.info(f"🎭 Storyteller initialized with model {settings.GEMINI_MODEL}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un script d'épisode complet
        
        Input:
            - mission_context: dict avec universe, mission data
            - episode_template: dict avec episode data du JSON master
            - main_characters: list des personnages principaux
        
        Output:
            - episode_script: dict avec le script complet
        """
        start_time = time.time()
        
        try:
            mission_context = input_data["mission_context"]
            episode_template = input_data["episode_template"]
            main_characters = input_data.get("main_characters", [])
            
            # Construction des variables pour le prompt
            main_chars_info = "\n".join([
                f"- {char['name']} ({char['id']}) - seed {char['visual_consistency_seed']} - {char['description']}"
                for char in main_characters
            ])
            
            user_variables = {
                "universe_title": mission_context["universe_title"],
                "city_name": mission_context["city"],
                "mission_title": mission_context["mission_title"],
                "mission_theme": mission_context["mission_theme"],
                "mission_objective": mission_context["mission_objective"],
                "episode_id": episode_template["episode_id"],
                "episode_title": episode_template["title"],
                "episode_description": episode_template["description"],
                "episode_objective": episode_template["objective"],
                "target_vocabulary": ", ".join(episode_template["target_vocabulary"]),
                "cefr_level": "A1-A2",
                "main_characters_info": main_chars_info
            }
            
            # Charger les prompts
            prompts = self.load_prompts(user_variables)
            
            logger.info(f"📝 Generating episode script: {episode_template['title']}")
            
            # Appel à Gemini
            response = self.model.generate_content(
                [prompts["system"], prompts["user"]],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse JSON response
            import json
            episode_script = json.loads(response.text)
            
            # Sauvegarde
            filename = f"episode_{episode_template['episode_id']}_script.json"
            self.save_output(episode_script, filename, "episodes")
            
            duration = time.time() - start_time
            self.log_call(duration, success=True)
            
            logger.success(f"✅ Episode script generated in {duration:.2f}s")
            
            return {
                "success": True,
                "episode_script": episode_script,
                "generation_time": duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Error generating script: {str(e)}")
            raise