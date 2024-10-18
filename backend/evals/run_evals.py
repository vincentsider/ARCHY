import json
import os
import sys
import datetime
import asyncio
import traceback
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Script started")

# Add the correct path to recognize the backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger.info("Importing modules")
from backend.evals.eval_utils import run_function_evals, load_config

logger.info("Setting up directories")
# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure the necessary directories exist
os.makedirs(os.path.join(current_dir, "eval_cases"), exist_ok=True)
os.makedirs(os.path.join(current_dir, "eval_results"), exist_ok=True)

# Use an absolute path for story_optimization_cases_path
story_optimization_cases_path = os.path.join(current_dir, "eval_cases", "story_optimization_cases.json")
CONFIG = load_config()

async def run_evals():
    logger.info("Starting story optimization evaluations...")
    
    try:
        logger.info("Loading story optimization cases")
        # Run story optimization evals
        with open(story_optimization_cases_path, "r") as file:
            story_optimization_cases = json.load(file)
        
        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_path = os.path.join(current_dir, "eval_results", f"story_optimization_evals_{timestamp}.json")
        
        logger.info("Calling run_function_evals")
        result = await run_function_evals(
            story_optimization_cases,
            eval_path=eval_path,
        )
        
        logger.info(f"Evaluations complete.")
        logger.info(f"Detailed results have been saved to '{eval_path}'")

        # Print a summary of the results
        for idx, case_result in enumerate(result['results'], 1):
            logger.info(f"\nCase {idx}:")
            logger.info(f"Original: {case_result['original']}")
            logger.info(f"Optimized: {case_result['optimized']}")
            logger.info(f"Improvement score: {case_result['improvement_score']:.2f}")
            logger.info("Agent Interactions:")
            for interaction in case_result['agent_interactions']:
                if isinstance(interaction, dict):
                    logger.info(f"  Role: {interaction.get('role', 'Unknown')}")
                    logger.info(f"  Content: {interaction.get('content', 'No content')[:100]}...")
                    if interaction.get('tool_calls'):
                        for tool_call in interaction['tool_calls']:
                            logger.info(f"    Tool: {tool_call['function']['name']}")
                else:
                    logger.info(f"  Interaction: {str(interaction)[:100]}...")
                logger.info("---")

        logger.info("\nEvaluation complete. Please check the output file for full details.")
    except Exception as e:
        logger.error(f"An error occurred during evaluation: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Running main function")
    try:
        asyncio.run(run_evals())
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
        logger.error(traceback.format_exc())
    logger.info("Script finished")
