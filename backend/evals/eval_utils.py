import json
import os
from typing import List, Dict, Any
from backend.main import optimize_story_logic, UserStory
from backend.config import Config
import logging
import asyncio
import traceback

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_config() -> Config:
    # Implement this function to load your configuration
    pass

async def run_function_evals(
    eval_cases: List[Dict[str, Any]],
    eval_path: str,
) -> Dict[str, Any]:
    results = []
    for case in eval_cases:
        logger.debug(f"Processing case: {case}")
        try:
            conversation = case.get('conversation', [])
            user_message = next((msg['content'] for msg in conversation if msg['role'] == 'user'), None)
            
            if not user_message:
                raise ValueError(f"Unable to extract user story from case: {case}")
            
            logger.debug(f"Optimizing user story: {user_message}")
            user_story = UserStory(content=user_message)
            
            logger.debug("Calling optimize_story_logic function")
            optimize_func = optimize_story_logic(user_story.content)
            response = await optimize_func()
            
            logger.debug(f"Optimized story result: {response.optimized}")
            
            result = {
                "original": user_message,
                "optimized": response.optimized,
                "agent_interactions": response.agent_interactions,
                "performance_metrics": response.performance_metrics,
                "improvement_score": response.performance_metrics.get("quality_score", 0)
            }
        except Exception as e:
            logger.error(f"Error processing case: {e}")
            logger.error(traceback.format_exc())
            result = {
                "original": user_message if 'user_message' in locals() else "Unknown",
                "optimized": str(e),
                "agent_interactions": [],
                "performance_metrics": {},
                "improvement_score": 0
            }
        
        results.append(result)
    
    eval_result = {
        "results": results
    }
    
    with open(eval_path, "w") as f:
        json.dump(eval_result, f, indent=2)
    
    return eval_result

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_improvement = sum(result['improvement_score'] for result in results)
    average_improvement = total_improvement / len(results) if results else 0
    
    return {
        "total_cases": len(results),
        "average_improvement": average_improvement,
        "best_case": max(results, key=lambda x: x['improvement_score']) if results else None,
        "worst_case": min(results, key=lambda x: x['improvement_score']) if results else None
    }

def generate_report(eval_result: Dict[str, Any], output_path: str):
    analysis = analyze_results(eval_result['results'])
    
    report = f"""
    Evaluation Report
    =================
    Total cases evaluated: {analysis['total_cases']}
    Average improvement score: {analysis['average_improvement']:.2f}
    
    Best case:
    Original: {analysis['best_case']['original'] if analysis['best_case'] else 'N/A'}
    Optimized: {analysis['best_case']['optimized'] if analysis['best_case'] else 'N/A'}
    Improvement score: {analysis['best_case']['improvement_score'] if analysis['best_case'] else 'N/A'}
    
    Worst case:
    Original: {analysis['worst_case']['original'] if analysis['worst_case'] else 'N/A'}
    Optimized: {analysis['worst_case']['optimized'] if analysis['worst_case'] else 'N/A'}
    Improvement score: {analysis['worst_case']['improvement_score'] if analysis['worst_case'] else 'N/A'}
    """
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Evaluation report generated and saved to {output_path}")
