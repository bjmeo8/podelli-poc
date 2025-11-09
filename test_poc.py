"""
Podelli POC - Test Script
Tests the complete episode generation workflow
"""
import asyncio
import sys
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)

from agents.orchestrator import OrchestratorAgent
from config.settings import validate_config


async def main():
    """Test the complete POC workflow"""
    
    logger.info("="*80)
    logger.info("PODELLI POC - Episode Generation Test")
    logger.info("="*80)
    
    # Validate configuration
    logger.info("\n1. Validating configuration...")
    if not validate_config():
        logger.error("❌ Configuration validation failed. Please check your .env file.")
        return
    
    logger.success("✅ Configuration valid")
    
    # Initialize orchestrator
    logger.info("\n2. Initializing orchestrator...")
    orchestrator = OrchestratorAgent()
    logger.success("✅ Orchestrator initialized")
    
    # Generate a single episode
    logger.info("\n3. Starting episode generation...")
    logger.info("   Mission: M1_AIRPORT")
    logger.info("   Episode: M1_E1_PASSPORT")
    logger.info("   Language: fr (French)")
    
    try:
        result = await orchestrator.generate_episode(
            mission_id="M1_AIRPORT",
            episode_id="M1_E1_PASSPORT",
            target_language="fr"
        )
        
        if result["success"]:
            logger.success("\n" + "="*80)
            logger.success("EPISODE GENERATION COMPLETED SUCCESSFULLY!")
            logger.success("="*80)
            logger.success(f"\nGeneration time: {result['generation_time']:.2f}s")
            logger.success(f"Episode data saved to: output/episodes/fr/M1_E1_PASSPORT_complete.json")
            logger.success("\nGenerated content:")
            
            episode = result["episode"]
            logger.success(f"  - Characters: {len(episode['characters'])}")
            logger.success(f"  - Scenes: {len(episode['scenes'])}")
            logger.success(f"  - Sequences: {len(episode['sequences'])}")
            logger.success(f"  - Voice Spells: {len(episode['voice_spells'])}")
            
            total_actions = sum(len(seq['actions']) for seq in episode['sequences'])
            logger.success(f"  - Quiz Actions: {total_actions}")
            
            logger.info("\n" + "="*80)
            logger.info("POC TEST COMPLETED")
            logger.info("="*80)
        else:
            logger.error("❌ Episode generation failed")
            
    except Exception as e:
        logger.error(f"\n❌ Error during generation: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
