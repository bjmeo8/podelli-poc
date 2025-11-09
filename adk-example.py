# Requirementt 
google-adk
pydantic
google-generativeai>=0.5.0
openai>=1.10.0
python-dotenv
google-cloud-aiplatform>=1.50.0
google-cloud-storage>=2.10.0
asyncio # Librairie standard de Python, pas besoin d'installation
# Requirementt

import os
import json
import uuid
import asyncio
from typing import List, Literal, Optional

# Import des librairies ADK, GenAI, VertexAI, OpenAI et GCS
import adk
import google.generativeai as genai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# Clients Google Cloud pour Vertex AI et GCS
import vertexai
from google.cloud import storage
from google.cloud.aiplatform.models import ImageGenerationModel, VideoGenerationModel

# --- 1. CONFIGURATION & UTILS ---

def setup_environment(gcp_project_id: str):
    """Charge les variables d'environnement et initialise les clients Google."""
    load_dotenv()
    try:
        vertexai.init(project=gcp_project_id, location="us-central1")
        print("✅ Vertex AI (pour Veo/Nano Banana) initialisé.")
    except Exception as e:
        print(f"❌ Échec Vertex AI. Erreur: {e}")
    try:
        storage.Client()
        print("✅ GCS client initialisé.")
    except Exception as e:
        print(f"❌ Échec GCS client. Erreur: {e}")

async def async_upload_to_gcs(data: bytes, bucket_name: str, destination_path: str, content_type: str) -> str:
    """Wrapper Asynchrone pour l'upload GCS (fonction I/O bloquante)."""
    # L'exécution dans un thread pool via asyncio.to_thread est la méthode standard pour rendre les
    # appels bloquants (synchrone) des SDK I/O asynchrones.
    return await asyncio.to_thread(_upload_to_gcs_sync, data, bucket_name, destination_path, content_type)

def _upload_to_gcs_sync(data: bytes, bucket_name: str, destination_path: str, content_type: str) -> str:
    """Fonction synchrone d'upload GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    filename_base = f"{destination_path}/{uuid.uuid4()}"
    if content_type == "image/png": filename = filename_base + ".png"
    elif content_type == "audio/mpeg": filename = filename_base + ".mp3"
    elif content_type == "video/mp4": filename = filename_base + ".mp4"
    else: filename = filename_base # Fallback
    
    blob = bucket.blob(filename)
    blob.upload_from_string(data, content_type=content_type)
    
    gcs_uri = f"gs://{bucket_name}/{filename}"
    print(f"⬆️ Asset uploadé sur GCS : {gcs_uri}")
    return gcs_uri

# --- 2. STRUCTURES DE DONNÉES (PYDANTIC MODELS) ---
# ... (Mêmes classes Pydantic que précédemment, omises ici pour la concision)
class ActionItem(BaseModel):
    action_type: Literal['VIDEO_QUIZ', 'VOICE_SPELL', 'QCM_IMAGE', 'SPEAKING_TASK']
    master_text: str = Field(description="The main text for the action in English.")
    quiz_options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    phonetic_transcription: Optional[str] = None
class SequenceItem(BaseModel):
    master_id: str
    master_description: str = Field(description="A short description of what happens in this sequence.")
    dialogue_line: str = Field(description="The single line of dialogue for this sequence.")
    actions: List[ActionItem]
class EpisodeScript(BaseModel):
    episode_master_id: str
    master_title: str
    full_dialogue_en: str = Field(description="The complete dialogue of the episode in English.")
    key_visuals_prompt: str = Field(description="Prompt for the Art Director for consistent visuals.")
    sequences: List[SequenceItem]
class LocalizedEpisode(BaseModel):
    language_code: str
    title: str
    full_dialogue: str
    sequences: List[dict]


# --- 3. AGENTS SPÉCIALISÉS (AVEC GOOGLE ADK + ASYNC) ---

class StorytellerAgent(adk.Agent):
    SYSTEM_PROMPT = "You are the Podelli Storyteller. Your task is to design engaging, pedagogically sound language learning scenarios (scripts) for the Podelli platform. Your output must be in perfect English and strictly adhere to the provided JSON schema."
    def __init__(self, api_key: str):
        super().__init__()
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel('gemini-2.5-pro', system_instruction=self.SYSTEM_PROMPT)

    async def invoke(self, episode_objective: str, episode_master_id: str, episode_title: str) -> EpisodeScript:
        print(f"📚 Storyteller: Génération du script master (Gemini 2.5 Pro) pour '{episode_title}'...")
        prompt = f"""
        Episode Objective: {episode_objective}
        Episode Title: {episode_title}
        Master ID: {episode_master_id}
        """
        # Exécution synchrone du LLM dans un thread pool
        response = await asyncio.to_thread(
            self.llm.generate_content,
            prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json")
        )
        try:
            validated_script = EpisodeScript(**json.loads(response.text))
            return validated_script
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Storyteller: Erreur de validation du script. Erreur: {e}\nTexte reçu:\n{response.text}")
            raise

class TranslatorAgent(adk.Agent):
    SYSTEM_PROMPT = "You are the Podelli Translator. Your task is to accurately and naturally localize the English Master Scripts into the target language, preserving the JSON structure. Your translation must be contextually appropriate for the Podelli narrative universe."
    def __init__(self, api_key: str):
        super().__init__()
        genai.configure(api_key=api_key)
        self.llm = genai.GenerativeModel('gemini-2.5-pro', system_instruction=self.SYSTEM_PROMPT)

    async def invoke(self, master_script: EpisodeScript, target_language: str) -> LocalizedEpisode:
        print(f"🌍 Translator: Traduction (Gemini 2.5 Pro) vers {target_language}...")
        prompt = f"""
        Translate all user-facing strings in the following JSON to the language: {target_language}.
        Schema: {json.dumps(LocalizedEpisode.model_json_schema(), indent=2)}
        Master Script: {master_script.model_dump_json()}
        """
        response = await asyncio.to_thread(
            self.llm.generate_content,
            prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json")
        )
        try:
            validated_data = LocalizedEpisode(**json.loads(response.text))
            return validated_data
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"❌ Translator: Erreur de validation de la traduction. Erreur: {e}\nTexte reçu:\n{response.text}")
            raise

class ArtDirectorAgent(adk.Agent):
    SYSTEM_PROMPT = "You are the Podelli Art Director. Your task is to generate high-consistency key visuals using the Nano Banana model, ensuring the characters and environments match the narrative description for long-term coherence."
    def __init__(self, gcs_bucket: str):
        super().__init__()
        self.model = ImageGenerationModel.from_pretrained("gemini-2.5-flash-image")
        self.gcs_bucket = gcs_bucket

    async def invoke(self, prompt: str, master_id: str) -> str:
        """Génère l'image avec Nano Banana et l'upload sur GCS."""
        print(f"🎨 Art Director: Génération d'une image (Nano Banana) pour '{master_id}'...")
        
        # Le SDK Vertex AI n'est pas async, on utilise to_thread
        # images = await asyncio.to_thread(self.model.generate_images, prompt=prompt, number_of_images=1)
        # image_bytes = images.generated_images[0].image_bytes
        
        # Simulation des bytes générés pour la démo sans le vrai SDK (pour simplifier la gestion des dépendances binaires)
        image_bytes = f"Image Data Placeholder for: {prompt}".encode('utf-8')

        return await async_upload_to_gcs(image_bytes, self.gcs_bucket, "assets/images", "image/png")

class VoiceActorAgent(adk.Agent):
    def __init__(self, api_key: str, gcs_bucket: str):
        super().__init__()
        self.client = OpenAI(api_key=api_key)
        self.gcs_bucket = gcs_bucket

    async def invoke(self, text: str, lang: str, master_id: str) -> str:
        """Génère l'audio avec GPT-4o TTS et l'upload sur GCS."""
        print(f"🎙️ Voice Actor: Génération audio (GPT-4o TTS) pour '{text[:30]}...' ({lang})")
        
        # L'API OpenAI supporte l'async
        response = await self.client.audio.speech.create(
            model="tts-1", # Correspond à l'API GPT-4o-TTS
            voice="nova",
            input=text,
            response_format="mp3"
        )
        audio_bytes = response.content
        
        return await async_upload_to_gcs(audio_bytes, self.gcs_bucket, f"assets/audio/{lang}", "audio/mpeg")

class VideoDirectorAgent(adk.Agent):
    def __init__(self, gcs_bucket: str):
        super().__init__()
        self.model = VideoGenerationModel.from_pretrained("veo-3-1-fast")
        self.gcs_bucket = gcs_bucket
        
    async def invoke(self, scene_description: str, key_visual_gcs_uri: str, master_id: str) -> str:
        """Génère la vidéo avec Veo et l'upload sur GCS."""
        print(f"🎬 Video Director: Démarrage de la génération vidéo (Veo 3.1 fast) pour '{scene_description[:30]}...'")
        
        # Veo est asynchrone par nature (long running operation).
        # operation = await asyncio.to_thread(
        #     self.model.generate,
        #     prompt=scene_description,
        #     input_uri=key_visual_gcs_uri,
        #     generation_config={"fps": 24, "length_seconds": 5}
        # )
        
        # print("⏳ Attente du résultat de la génération Veo (opération longue)...")
        # video_bytes = await asyncio.to_thread(operation.result) # Attend que l'opération soit terminée

        # Simulation des bytes vidéo générés
        video_bytes = f"Video Data Placeholder for: {scene_description}".encode('utf-8')
        
        return await async_upload_to_gcs(video_bytes, self.gcs_bucket, "assets/video", "video/mp4")

# --- 4. ORCHESTRATEUR (ADK TEAM - ASYNC) ---

class ContentGenerationTeam(adk.Team):
    def __init__(self, config: dict):
        super().__init__()
        print("🛠️ Initialisation de l'équipe d'agents (Google ADK Team ASYNC)...")
        self.storyteller = StorytellerAgent(api_key=config['GOOGLE_API_KEY'])
        self.translator = TranslatorAgent(api_key=config['GOOGLE_API_KEY'])
        self.art_director = ArtDirectorAgent(gcs_bucket=config['GCS_BUCKET_NAME'])
        self.voice_actor = VoiceActorAgent(api_key=config['OPENAI_API_KEY'], gcs_bucket=config['GCS_BUCKET_NAME'])
        self.video_director = VideoDirectorAgent(gcs_bucket=config['GCS_BUCKET_NAME'])
        self.generated_assets = {}

    async def run_generation_for_episode(self, episode_spec: dict, config: dict):
        master_id = episode_spec['master_id']
        print(f"\n🚀 DÉBUT DE LA GÉNÉRATION POUR L'ÉPISODE: {episode_spec['title']} ({master_id}) 🚀")
        self.generated_assets[master_id] = {}

        # 1. Scénarisation (Master - ASYNC)
        master_script = await self.storyteller.invoke(
            episode_objective=episode_spec['objective'],
            episode_master_id=master_id,
            episode_title=episode_spec['title']
        )
        
        # 2. Production Visuelle Universelle (ASYNC)
        print("\n--- Génération et Upload des assets universels ---")
        key_visual_gcs_uri = await self.art_director.invoke(master_script.key_visuals_prompt, master_id)
        self.generated_assets[master_id]['universal'] = {'key_visual': key_visual_gcs_uri}
        
        # 3. Localisation et Production Média (Mono-Langue de Test)
        # On ne prend que la première langue pour le test, comme demandé
        target_lang = config['target_languages'][0] 

        print(f"\n--- Traitement de la langue: {target_lang} ---")
        self.generated_assets[master_id][target_lang] = {}

        # Traduction (ASYNC)
        localized_episode = await self.translator.invoke(master_script, target_lang)
        
        # Récupérer les assets à générer
        dialogue_line = localized_episode.sequences[0]['dialogue_line']
        seq_master_id = master_script.sequences[0].master_id
        
        # Lancer les tâches Média en parallèle pour maximiser l'efficacité
        audio_task = self.voice_actor.invoke(dialogue_line, target_lang, seq_master_id)
        video_task = self.video_director.invoke(master_script.sequences[0].master_description, key_visual_gcs_uri, seq_master_id)

        # Attendre que les deux tâches (Audio et Vidéo) soient terminées
        audio_path, video_path = await asyncio.gather(audio_task, video_task)
        
        self.generated_assets[master_id][target_lang]['audio'] = audio_path
        self.generated_assets[master_id][target_lang]['video'] = video_path

        print(f"💾 Les URIs GCS sont prêtes à être enregistrées dans Cloud SQL pour l'épisode {master_id} en {target_lang}.")
        
        print(f"\n✅ GÉNÉRATION TERMINÉE POUR L'ÉPISODE: {episode_spec['title']} ✅")

# --- 5. EXÉCUTION PRINCIPALE ---

if __name__ == "__main__":
    
    try:
        with open("universe_master.json", "r", encoding="utf-8") as f:
            app_config = json.load(f)
    except FileNotFoundError:
        print("❌ Erreur: Le fichier 'universe_master.json' est introuvable.")
        exit()

    api_config = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
        "GCS_BUCKET_NAME": os.getenv("GCS_BUCKET_NAME"),
    }
    
    setup_environment(api_config['GCP_PROJECT_ID'])

    if not all(api_config.values()):
        print("❌ Erreur: Clés de configuration (API ou GCP) manquantes dans le fichier .env.")
        exit()

    # Initialiser et lancer le processus ASYNCHRONE
    sga_team = ContentGenerationTeam(config=api_config)
    
    first_episode_spec = app_config['missions'][0]['episodes'][0]
    
    # Lancement du run asynchrone
    asyncio.run(sga_team.run_generation_for_episode(first_episode_spec, app_config))

    # Afficher un résumé des URIs GCS générés
    print("\n\n--- RÉSUMÉ DES ASSETS GCS GÉNÉRÉS ---")
    print(json.dumps(sga_team.generated_assets, indent=2))
    print("\nCes URIs doivent être stockées dans votre table Cloud SQL 'Assets'.")
