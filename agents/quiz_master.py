"""
QUIZ MASTER AGENT
Generates interactive quiz actions (Video Quiz, QCM, etc.)
"""
import time
import json
from typing import Dict, Any, List
from loguru import logger
from google import genai

from agents.base_agent import BaseAgent
from config.settings import settings


class QuizMasterAgent(BaseAgent):
    """
    Creates interactive pedagogical quizzes based on episode content
    """

    def __init__(self):
        super().__init__("QUIZ_MASTER")

        # Initialize Gemini for quiz generation
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.GEMINI_TEXT_MODEL_FAST

        logger.info(f"📝 Quiz Master initialized with {self.model}")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quiz actions for episode

        Input:
            - script: English script
            - translated_script: Translated script
            - video_files: Generated video files
            - audio_files: Generated audio files
            - episode_id: Episode ID

        Output:
            - quiz_actions: List of quiz action objects
        """
        start_time = time.time()

        try:
            script = input_data["script"]
            translated_script = input_data["translated_script"]
            video_files = input_data.get("video_files", {})
            episode_id = input_data["episode_id"]

            logger.info(f"📝 Generating quiz content for {episode_id}...")

            quiz_actions = []

            # Generate quizzes for each sequence
            for sequence in translated_script["sequences"]:
                sequence_id = sequence["sequence_id"]

                # 1. Video Quiz (comprehension)
                video_quiz = await self._generate_video_quiz(sequence, video_files.get(sequence_id))
                if video_quiz:
                    quiz_actions.append(video_quiz)

                # 2. QCM Text (vocabulary/grammar)
                qcm_text = await self._generate_qcm_text(sequence)
                if qcm_text:
                    quiz_actions.extend(qcm_text)

                # 3. QCM Audio (listening comprehension)
                qcm_audio = await self._generate_qcm_audio(sequence)
                if qcm_audio:
                    quiz_actions.append(qcm_audio)

            duration = time.time() - start_time
            self.log_call(duration, success=True)

            logger.success(f"✅ Generated {len(quiz_actions)} quiz actions in {duration:.2f}s")

            return {
                "success": True,
                "quiz_actions": quiz_actions,
                "generation_time": duration
            }

        except Exception as e:
            duration = time.time() - start_time
            self.log_call(duration, success=False)
            logger.error(f"❌ Quiz Master error: {str(e)}")
            raise

    async def _generate_video_quiz(
        self,
        sequence: Dict[str, Any],
        video_path: str
    ) -> Dict[str, Any]:
        """Generate a video comprehension quiz"""
        
        prompt = f"""Create a comprehension question about this dialogue scene.

Scene: {sequence['scene_description']}

Dialogue:
{json.dumps(sequence['dialogue'], ensure_ascii=False, indent=2)}

Create a multiple-choice question that tests comprehension of the dialogue.
Return JSON with this structure:
{{
  "question": "The question text",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_index": 0,
  "explanation": "Why this is the correct answer"
}}"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )

        quiz_data = json.loads(response.text)

        return {
            "action_type": "VIDEO_QUIZ",
            "sequence_id": sequence["sequence_id"],
            "video_path": video_path,
            "question": quiz_data["question"],
            "options": quiz_data["options"],
            "correct_answer": quiz_data["correct_index"],
            "explanation": quiz_data["explanation"]
        }

    async def _generate_qcm_text(self, sequence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate text-based QCM for vocabulary/grammar"""
        
        prompt = f"""Create 2 multiple-choice questions about vocabulary or grammar from this dialogue.

Dialogue:
{json.dumps(sequence['dialogue'], ensure_ascii=False, indent=2)}

Key vocabulary: {sequence.get('key_vocabulary', [])}
Grammar focus: {sequence.get('grammar_focus', 'N/A')}

Create questions that test understanding of new vocabulary or grammar patterns.
Return JSON array with this structure:
[
  {{
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Why this is correct",
    "focus": "vocabulary or grammar"
  }}
]"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )

        quizzes_data = json.loads(response.text)

        quiz_actions = []
        for quiz_data in quizzes_data:
            quiz_actions.append({
                "action_type": "QCM_TEXT",
                "sequence_id": sequence["sequence_id"],
                "question": quiz_data["question"],
                "options": quiz_data["options"],
                "correct_answer": quiz_data["correct_index"],
                "explanation": quiz_data["explanation"],
                "focus": quiz_data.get("focus", "vocabulary")
            })

        return quiz_actions

    async def _generate_qcm_audio(self, sequence: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audio-based listening comprehension quiz"""
        
        # Select one dialogue line to test
        if not sequence["dialogue"]:
            return None

        test_line = sequence["dialogue"][0]

        prompt = f"""Create a listening comprehension question.

The learner will hear: "{test_line['text']}"

Create a question asking what they heard, with plausible wrong options.
Return JSON:
{{
  "question": "What did you hear?",
  "options": ["Correct phrase", "Wrong option 1", "Wrong option 2", "Wrong option 3"],
  "correct_index": 0
}}"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )

        quiz_data = json.loads(response.text)

        return {
            "action_type": "QCM_AUDIO",
            "sequence_id": sequence["sequence_id"],
            "audio_text": test_line["text"],
            "question": quiz_data["question"],
            "options": quiz_data["options"],
            "correct_answer": quiz_data["correct_index"]
        }
