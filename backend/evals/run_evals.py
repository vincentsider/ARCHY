import json
import os
import sys
import datetime

# Add the correct path to recognize the backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.evals.eval_utils import run_function_evals, load_config

# Ensure the necessary directories exist
os.makedirs("eval_cases", exist_ok=True)
os.makedirs("eval_results", exist_ok=True)

story_optimization_cases = "eval_cases/story_optimization_cases.json"
CONFIG = load_config()

if __name__ == "__main__":
    print("Starting story optimization evaluations...")
    
    # Run story optimization evals
    with open(story_optimization_cases, "r") as file:
        story_optimization_cases = json.load(file)
    
    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_path = f"eval_results/story_optimization_evals_{timestamp}.json"
    
    result = run_function_evals(
        story_optimization_cases,
        eval_path=eval_path,
    )
    
    print(f"Evaluations complete.")
    print(f"Detailed results have been saved to '{eval_path}'")

    # Print a summary of the results
    for idx, case_result in enumerate(result['results'], 1):
        print(f"\nCase {idx}:")
        print(f"Original: {case_result['messages'][0]['content']}")
        print(f"Optimized: {case_result['actual_message'][0]}")
        print(f"Improvement score: {case_result['improvement_scores'][0]:.2f}")
        print("Agent Interactions:")
        for interaction in case_result['agent_interactions']:
            if isinstance(interaction, dict):
                print(f"  Role: {interaction.get('role', 'Unknown')}")
                print(f"  Content: {interaction.get('content', 'No content')}")
                if interaction.get('tool_calls'):
                    for tool_call in interaction['tool_calls']:
                        print(f"    Tool: {tool_call['function']['name']}")
                        print(f"    Arguments: {tool_call['function']['arguments']}")
            else:
                print(f"  Interaction: {interaction}")
            print("---")

    print("\nEvaluation complete. Please check the output file for full details.")
