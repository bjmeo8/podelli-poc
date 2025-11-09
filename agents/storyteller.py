"""
STORYTELLER AGENT
Generates complete episode scripts dynamically based on episode objectives
"""
import time
import json
from typing import Dict, Any
from loguru import logger
from google import genai

from agents.base_agent import BaseAgent
from config.settings import settings


class StorytellerAgent(BaseAgent):
    """
    Generates creative, pedagogical scripts for language learning episodes
    WITHOUT hardcoded scenarios - everything is generated dynamically
    """

    def __init__(self):
        super().__init__("STORYTELLER")

        # Initialize Gemini 2.5 Pro for creative storytelling
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GEMINI_TEXT_MODEL

        logger.info(f"🎭 Storyteller initialized with {self.model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete episode script dynamically

        Input:
            - mission: Mission data from universe master
            - episode: Episode data from universe master
            - cefr_level: CEFR level (A1, A2, etc.)

        Output:
            - script: Complete episode script with sequences, dialogues, characters
        """
        start_time = time.time()

        try:
            mission = input_data["mission"]
            episode = input_data["episode"]
            cefr_level = input_data["cefr_level"]

            logger.info(f"📝 Generating script for: {episode['title']}")

            # Create dynamic prompt - NO HARDCODED SCENARIOS
            prompt = self._create_storytelling_prompt(mission, episode, cefr_level)

            # Call Gemini 2.5 Pro
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.GenerateContentConfig(
                    temperature=0.8,
                    top_p=0.95,
                    response_mime_type="application/json"
                )
            )

            # Parse response
            script = json.loads(response.text)

            # Save for reference
            self.save_output(script, f"script_{episode['master_id']}.json", "scripts")

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Script generated in {duration:.2f}s")

            return {
                "success": True,
                "script": script,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Storyteller error: {str(e)}")
            raise

    def _create_storytelling_prompt(
        self,
        mission: Dict[str, Any],
        episode: Dict[str, Any],
        cefr_level: str
    ) -> str:
        """
        Create dynamic storytelling prompt WITHOUT hardcoded scenarios

        The prompt guides the AI to create scenarios that fit the objective,
        but does NOT specify exact scenes or actions
        """
        prompt = f"""You are an expert language learning content creator specializing in immersive, scenario-based learning.

Your task is to create a complete pedagogical script for a language learning episode in JSON format.

# Episode Context
- **Mission**: {mission['title']} - {mission['objective']}
- **Episode**: {episode['title']} - {episode['objective']}
- **CEFR Level**: {cefr_level}

# Your Creative Task
Design a realistic, engaging scenario that helps learners achieve the episode objective.
You should:
1. Create authentic situations that a language learner would encounter
2. Design natural dialogues with appropriate vocabulary for the CEFR level
3. Introduce 2-4 characters with distinct personalities
4. Structure the episode into 3-5 logical sequences
5. Include cultural context and real-world relevance

# Important Guidelines
- DO NOT use cliché or overly simplified scenarios
- Make dialogues natural and contextually appropriate
- Vary the situations within the episode objective
- Characters should have realistic motivations
- Include some complexity to maintain engagement
- Vocabulary should match the CEFR level but feel natural

# Output JSON Structure
{{
  "episode_id": "{episode['master_id']}",
  "title": "{episode['title']}",
  "objective": "{episode['objective']}",
  "scenario_summary": "Brief description of the scenario you created",
  "characters": [
    {{
      "character_id": "CHAR_1",
      "role": "Description of their role",
      "personality": "Brief personality description",
      "visual_description": "Physical description for image generation (age, appearance, clothing)"
    }}
  ],
  "sequences": [
    {{
      "sequence_id": "SEQ_1",
      "sequence_number": 1,
      "scene_description": "What's happening in this sequence",
      "scene_visual": "Visual description for scene background (location, atmosphere, details)",
      "dialogue": [
        {{
          "character_id": "CHAR_1",
          "text": "What the character says",
          "teaching_note": "What language element this teaches"
        }}
      ],
      "key_vocabulary": ["word1", "word2"],
      "grammar_focus": "Grammar point if applicable"
    }}
  ],
  "learning_outcomes": [
    "Specific skill 1",
    "Specific skill 2"
  ]
}}

Generate a creative, pedagogically sound script that achieves the learning objective in an engaging way."""

        return prompt
