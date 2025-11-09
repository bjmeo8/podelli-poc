"""
Settings and Configuration for Podelli POC
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model Configuration
GEMINI_TEXT_MODEL = "gemini-2.5-pro-002"  # For text generation and agents
GEMINI_TEXT_MODEL_FAST = "gemini-2.5-flash-002"  # For faster text generation
NANO_BANANA_MODEL = "gemini-2.5-flash-image-preview"  # For image generation (Nano Banana)
VEO_MODEL = "veo-3.1-generate-preview"  # For video generation
VEO_FAST_MODEL = "veo-3.1-fast-generate-preview"  # For faster video generation
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"  # For voice generation

# Media Settings
IMAGE_ASPECT_RATIO = "9:16"  # Portrait format for mobile
VIDEO_ASPECT_RATIO = "9:16"  # Portrait format for mobile
VIDEO_RESOLUTION = "1080p"
VIDEO_FPS = 24
VIDEO_DURATION_DIALOGUE = 7  # seconds
VIDEO_DURATION_SCENE = 10  # seconds

AUDIO_FORMAT = "mp3"
AUDIO_SAMPLE_RATE = 24000

# Voice Settings (OpenAI TTS voices)
VOICE_MAPPING = {
    "CHAR_TRAVELER": "alloy",       # Neutral, versatile
    "CHAR_AIRPORT_AGENT": "nova",   # Warm, friendly female
    "CHAR_INFO_DESK": "echo",       # Neutral male
    "CHAR_TAXI_DRIVER": "onyx",     # Deep, authoritative
    "ANNOUNCEMENT": "echo",          # Official tone
    "VOICE_SPELL": "nova"           # Clear pronunciation
}

# Generation Settings
MAX_RETRIES = 3
GENERATION_TIMEOUT = 120  # seconds

# POC Settings
TARGET_LANGUAGE = "fr"  # French
NATIVE_LANGUAGE = "en"  # English
UNIVERSE_FILE = DATA_DIR / "universe_master.json"

# Validate API keys
def validate_config():
    """Validate that required API keys are present"""
    errors = []

    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY not found in .env")

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not found in .env")

    if errors:
        print("�  Configuration Warnings:")
        for error in errors:
            print(f"   - {error}")
        print("\n   Please set these in your .env file")
        return False

    return True
