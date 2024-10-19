import os
import sys

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from jira import JIRA
from dotenv import load_dotenv
import logging
import asyncio
from backend.swarm.agent import Agent
from backend.config import Config, load_config

# Load environment variables
load_dotenv()

# Jira connection details
JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('PROJECT_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_jira():
    """Establish a connection to Jira."""
    print("Attempting to connect to Jira...")
    try:
        jira = JIRA(server=JIRA_HOST, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        print("Successfully connected to Jira.")
        return jira
    except Exception as e:
        print(f"Error connecting to Jira: {str(e)}")
        logger.error(f"Error connecting to Jira: {str(e)}")
        return None

def get_all_subtasks(jira):
    """Fetch all Sub-tasks from Jira."""
    print(f"Fetching subtasks for project: {PROJECT_KEY}")
    jql = f'project = {PROJECT_KEY} AND issuetype = Sub-task'
    subtasks = jira.search_issues(jql, maxResults=False)
    print(f"Found {len(subtasks)} subtasks.")
    return subtasks

def update_subtask_description(jira, subtask, new_description):
    """Update the description of a Sub-task in Jira."""
    try:
        subtask.update(fields={'description': new_description})
        print(f"Updated Sub-task {subtask.key}")
        logger.info(f"Updated Sub-task {subtask.key}")
    except Exception as e:
        print(f"Error updating Sub-task {subtask.key}: {str(e)}")
        logger.error(f"Error updating Sub-task {subtask.key}: {str(e)}")

async def optimize_story(story: str):
    print("Optimizing story...")
    config = load_config("config.json")  # Use the load_config function
    agents = [
        Agent(ac.name, OPENAI_API_KEY, config.openai_model, ac.instructions, ac.tools) for ac in config.agents
    ]
    
    # Import Swarm here to avoid circular import
    from backend.swarm.swarm import Swarm
    swarm = Swarm(agents, config)
    
    # Create a tools_map dictionary
    tools_map = {name: func for name, func in config.tools.items() if callable(func)}
    
    context_analysis = await swarm.analyze_context(story)
    optimized_story, agent_interactions, performance_metrics = await swarm.process_message(story, tools_map, context_analysis)
    print("Story optimization completed.")
    return optimized_story, agent_interactions, performance_metrics

async def process_jira_subtasks(optimize_function):
    """Process all Jira Sub-tasks using the provided optimization function."""
    print("Starting to process Jira subtasks...")
    jira = connect_to_jira()
    if not jira:
        print("Failed to connect to Jira. Exiting.")
        return {"error": "Failed to connect to Jira"}

    subtasks = get_all_subtasks(jira)
    results = []

    for subtask in subtasks:
        print(f"Processing subtask: {subtask.key}")
        original_description = subtask.fields.description
        try:
            optimized, agent_interactions, performance_metrics = await optimize_function(original_description)
            update_subtask_description(jira, subtask, optimized)
            results.append({
                "key": subtask.key,
                "original": original_description,
                "optimized": optimized,
                "performance_metrics": performance_metrics
            })
            print(f"Successfully processed subtask: {subtask.key}")
        except Exception as e:
            print(f"Error processing Sub-task {subtask.key}: {str(e)}")
            logger.error(f"Error processing Sub-task {subtask.key}: {str(e)}")
            results.append({
                "key": subtask.key,
                "error": str(e)
            })

    print("Finished processing all subtasks.")
    return results

async def main():
    print("Starting Jira integration test")
    results = await process_jira_subtasks(optimize_story)
    
    print("Jira integration test completed")
    print(f"Processed {len(results)} subtasks")
    
    for result in results:
        if "error" in result:
            print(f"Error processing subtask {result['key']}: {result['error']}")
        else:
            print(f"Successfully processed subtask {result['key']}")
            print(f"Original: {result['original'][:100]}...")
            print(f"Optimized: {result['optimized'][:100]}...")
            print(f"Performance metrics: {result['performance_metrics']}")
        print("---")

if __name__ == "__main__":
    print("Script started.")
    asyncio.run(main())
    print("Script finished.")
