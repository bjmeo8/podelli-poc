"""
Classe de base pour tous les agents Podelli
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import json
import uuid
from datetime import datetime
from loguru import logger

from config.settings import settings
from tools.prompt_loader import prompt_loader

class BaseAgent(ABC):
    """Classe abstraite pour tous les agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agent_id = agent_name.lower().replace(" ", "_")
        
        self.metrics = {
            "calls": 0,
            "total_duration": 0,
            "errors": 0
        }
        logger.info(f"✅ Agent {agent_name} initialized")
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Méthode principale de traitement
        Doit être implémentée par chaque agent
        """
        pass
    
    def load_prompts(self, user_variables: Dict[str, Any] = None) -> Dict[str, str]:
        """Charge les prompts système et utilisateur de l'agent"""
        return prompt_loader.get_agent_prompts(self.agent_id, user_variables)
    
    def log_call(self, duration: float, success: bool = True):
        """Enregistre une métrique d'appel"""
        self.metrics["calls"] += 1
        self.metrics["total_duration"] += duration
        if not success:
            self.metrics["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de l'agent"""
        avg_duration = (
            self.metrics["total_duration"] / self.metrics["calls"]
            if self.metrics["calls"] > 0
            else 0
        )
        return {
            "agent": self.agent_name,
            "total_calls": self.metrics["calls"],
            "total_duration_seconds": round(self.metrics["total_duration"], 2),
            "average_duration_seconds": round(avg_duration, 2),
            "errors": self.metrics["errors"]
        }
    
    def save_output(self, data: Dict[str, Any], filename: str, subdir: str = "episodes"):
        """Sauvegarde un JSON de sortie"""
        output_path = settings.OUTPUT_DIR / subdir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Saved {filename} to {output_path}")
        return str(output_path)
    
    def generate_id(self) -> str:
        """Génère un UUID"""
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """Retourne un timestamp ISO"""
        return datetime.utcnow().isoformat() + "Z"