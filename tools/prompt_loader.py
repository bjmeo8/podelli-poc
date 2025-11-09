"""
Gestionnaire de chargement et population des prompts
"""
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from config.settings import settings

class PromptLoader:
    """Charge et peuple dynamiquement les prompts depuis les fichiers"""
    
    def __init__(self):
        self.prompts_dir = settings.PROJECT_ROOT / "prompts"
        self._cache = {}
        logger.info(f"📝 PromptLoader initialized: {self.prompts_dir}")
    
    def load_prompt(self, prompt_name: str) -> str:
        """
        Charge un fichier de prompt
        
        Args:
            prompt_name: Nom du fichier (ex: "storyteller_system.txt")
        
        Returns:
            Contenu du prompt
        """
        # Vérifier le cache
        if prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Charger depuis le fichier
        prompt_path = self.prompts_dir / prompt_name
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Mettre en cache
        self._cache[prompt_name] = content
        
        logger.debug(f"✅ Loaded prompt: {prompt_name}")
        return content
    
    def populate_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Remplit un template de prompt avec des variables
        
        Args:
            template: Template avec placeholders {variable_name}
            variables: Dict des valeurs à insérer
        
        Returns:
            Prompt populé
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.error(f"❌ Missing variable in prompt template: {e}")
            raise
    
    def get_agent_prompts(self, agent_name: str, user_variables: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Récupère les prompts système et utilisateur pour un agent
        
        Args:
            agent_name: Nom de l'agent (ex: "storyteller")
            user_variables: Variables pour le prompt utilisateur
        
        Returns:
            Dict avec "system" et "user" prompts
        """
        # Charger le prompt système
        system_prompt = self.load_prompt(f"{agent_name}_system.txt")
        
        # Charger et peupler le prompt utilisateur
        user_template = self.load_prompt(f"{agent_name}_user.txt")
        
        user_prompt = (
            self.populate_prompt(user_template, user_variables)
            if user_variables
            else user_template
        )
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }

# Instance globale
prompt_loader = PromptLoader()