import datetime
import json
import uuid
import logging
import time
import os
from fastapi.testclient import TestClient
from backend.main import app
from difflib import SequenceMatcher

client = TestClient(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'eval_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

CONFIG = load_config()

def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def run_function_evals(test_cases, eval_path=None):
    results = []
    eval_id = str(uuid.uuid4())
    eval_timestamp = datetime.datetime.now().isoformat()

    for idx, test_case in enumerate(test_cases, 1):
        case_results = {
            "messages": test_case["conversation"],
            "expected_function": test_case["function"],
            "actual_function": [],
            "actual_message": [],
            "agent_interactions": [],
            "improvement_scores": []
        }
        logging.info(f"Processing test case {idx}/{len(test_cases)}")
        logging.info(f"Conversation: {test_case['conversation']}")
        
        response = client.post("/optimize_story", json={"content": test_case["conversation"][0]["content"]})
        output = extract_response_info(response)
        
        case_results["actual_function"].append(output.get("function", "None"))
        case_results["actual_message"].append(output.get("message", "None"))
        case_results["agent_interactions"] = output.get("agent_interactions", [])
        case_results["model"] = output.get("model", "Unknown")

        # Calculate improvement score
        original_story = test_case["conversation"][0]["content"]
        optimized_story = output.get("message", "")
        improvement_score = calculate_similarity(optimized_story, original_story)
        case_results["improvement_scores"].append(improvement_score)
        
        logging.info(f"Improvement score: {improvement_score:.2f}")
        results.append(case_results)

    final_result = {
        "id": eval_id,
        "timestamp": eval_timestamp,
        "results": results
    }

    if eval_path:
        os.makedirs(os.path.dirname(eval_path), exist_ok=True)
        with open(eval_path, "w") as file:
            json.dump(final_result, file, indent=4)

    return final_result

def extract_response_info(response):
    results = {}
    if response.status_code == 200:
        results["function"] = "optimize_story"
        response_json = response.json()
        results["message"] = response_json.get("optimized", "No optimized story")
        results["agent_interactions"] = response_json.get("agent_interactions", [])
        results["model"] = response_json.get("model", "Unknown")
        
        # Enhance agent interactions with more details
        for interaction in results["agent_interactions"]:
            if "role" in interaction and interaction["role"] == "assistant":
                interaction["agent_name"] = interaction.get("agent_name", "Unknown Agent")
                interaction["decision"] = interaction.get("decision", "No decision recorded")
                if "tool_calls" in interaction:
                    interaction["tools_used"] = [tool["function"]["name"] for tool in interaction["tool_calls"]]
                else:
                    interaction["tools_used"] = []
    elif response.status_code == 429:
        results["function"] = "rate_limit"
        results["message"] = response.json().get("detail", "Rate limit exceeded")
    else:
        results["function"] = "error"
        results["message"] = response.json().get("detail", "Unknown error")
    return results
