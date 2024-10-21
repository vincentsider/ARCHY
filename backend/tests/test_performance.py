import json
import os
import sys
import datetime
import time
import statistics

# Add the correct path to recognize the backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.evals.eval_utils import run_function_evals, load_config
from backend.main import optimize_story

CONFIG = load_config()

def test_process_stories_performance():
    print("Starting story optimization performance test...")
    
    # Define the path to the story optimization cases file
    story_optimization_cases_path = os.path.join(os.path.dirname(__file__), "..", "evals", "eval_cases", "story_optimization_cases.json")
    
    # Run story optimization evals
    with open(story_optimization_cases_path, "r") as file:
        story_optimization_cases = json.load(file)
    
    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_path = f"eval_results/story_optimization_performance_{timestamp}.json"
    
    start_time = time.time()
    
    results = []
    for case in story_optimization_cases:
        case_start_time = time.time()
        optimized_story, agent_interactions, performance_metrics = optimize_story(case['messages'][0]['content'])
        case_end_time = time.time()
        
        results.append({
            'original': case['messages'][0]['content'],
            'optimized': optimized_story,
            'agent_interactions': agent_interactions,
            'performance_metrics': performance_metrics,
            'execution_time': case_end_time - case_start_time
        })
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nPerformance test complete.")
    print(f"Detailed results have been saved to '{eval_path}'")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Stories processed: {len(story_optimization_cases)}")
    print(f"Average time per story: {total_time / len(story_optimization_cases):.2f} seconds")

    # Calculate performance statistics
    processing_times = [result['execution_time'] for result in results]
    avg_time = statistics.mean(processing_times)
    min_time = min(processing_times)
    max_time = max(processing_times)

    print(f"\nPerformance Statistics:")
    print(f"Average processing time: {avg_time:.2f} seconds")
    print(f"Minimum processing time: {min_time:.2f} seconds")
    print(f"Maximum processing time: {max_time:.2f} seconds")

    # Print a summary of the results
    for idx, result in enumerate(results, 1):
        print(f"\nCase {idx}:")
        print(f"Original: {result['original'][:100]}...")
        print(f"Optimized: {result['optimized'][:100]}...")
        print(f"Quality score: {result['performance_metrics']['quality_score']:.2f}")
        print(f"Processing time: {result['execution_time']:.2f} seconds")
        
        if result['performance_metrics']['quality_score'] < 0.5:
            print("WARNING: Low quality score. This case may need further investigation.")
        
        print("Agent Interactions:")
        for interaction in result['agent_interactions']:
            if isinstance(interaction, dict):
                print(f"  Role: {interaction.get('role', 'Unknown')}")
                print(f"  Content: {interaction.get('content', 'No content')[:100]}...")
                if interaction.get('tool_calls'):
                    for tool_call in interaction['tool_calls']:
                        print(f"    Tool: {tool_call['function']['name']}")
            else:
                print(f"  Interaction: {str(interaction)[:100]}...")
            print("---")

    # Save detailed results to file
    with open(eval_path, 'w') as f:
        json.dump(results, f, indent=2)

    print("\nPerformance test complete. Please check the output file for full details.")

if __name__ == "__main__":
    test_process_stories_performance()
