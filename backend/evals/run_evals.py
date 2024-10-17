import json
import os
import sys
import datetime
import asyncio
import traceback
import logging

print("Script started")  # Basic print statement

# Add the correct path to recognize the backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("Importing modules")  # Basic print statement
from backend.evals.eval_utils import run_function_evals, load_config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("Setting up directories")  # Basic print statement
# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure the necessary directories exist
os.makedirs(os.path.join(current_dir, "eval_cases"), exist_ok=True)
os.makedirs(os.path.join(current_dir, "eval_results"), exist_ok=True)

# Use an absolute path for story_optimization_cases_path
story_optimization_cases_path = os.path.join(current_dir, "eval_cases", "story_optimization_cases.json")
CONFIG = load_config()

async def run_evals():
    print("Starting story optimization evaluations...")  # Basic print statement
    
    try:
        print("Loading story optimization cases")  # Basic print statement
        # Run story optimization evals
        with open(story_optimization_cases_path, "r") as file:
            story_optimization_cases = json.load(file)
        
        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_path = os.path.join(current_dir, "eval_results", f"story_optimization_evals_{timestamp}.json")
        
        print("Calling run_function_evals")  # Basic print statement
        result = await run_function_evals(
            story_optimization_cases,
            eval_path=eval_path,
        )
        
        print(f"Evaluations complete.")  # Basic print statement
        print(f"Detailed results have been saved to '{eval_path}'")

        # Print a summary of the results
        for idx, case_result in enumerate(result['results'], 1):
            print(f"\nCase {idx}:")  # Basic print statement
            print(f"Original: {case_result['original']}")
            print(f"Optimized: {case_result['optimized']}")
            print(f"Improvement score: {case_result['improvement_score']:.2f}")
            print("Agent Interactions:")
            for interaction in case_result['agent_interactions']:
                if isinstance(interaction, dict):
                    print(f"  Role: {interaction.get('role', 'Unknown')}")
                    content = interaction.get('content', 'No content')
                    if content:
                        print(f"  Content: {content[:100]}...")
                    if interaction.get('tool_calls'):
                        for tool_call in interaction['tool_calls']:
                            print(f"    Tool: {tool_call['function']['name']}")
                else:
                    print(f"  Interaction: {str(interaction)[:100]}...")
                print("---")

        print("\nEvaluation complete. Please check the output file for full details.")
    except Exception as e:
        print(f"An error occurred during evaluation: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("Running main function")  # Basic print statement
    asyncio.run(run_evals())
    print("Script finished")  # Basic print statement
