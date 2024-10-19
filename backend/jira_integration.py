import os
import sys
import traceback

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_jira():
    """Establish a connection to Jira."""
    logger.info("Attempting to connect to Jira...")
    try:
        jira = JIRA(server=JIRA_HOST, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        logger.info("Successfully connected to Jira.")
        return jira
    except Exception as e:
        logger.error(f"Error connecting to Jira: {str(e)}")
        return None

def get_all_subtasks(jira):
    """Fetch all Sub-tasks from Jira."""
    logger.info(f"Fetching subtasks for project: {PROJECT_KEY}")
    jql = f'project = {PROJECT_KEY} AND issuetype = Sub-task'
    subtasks = jira.search_issues(jql, maxResults=False)
    logger.info(f"Found {len(subtasks)} subtasks.")
    return subtasks

def update_subtask_description(jira, subtask, new_description):
    """Update the description of a Sub-task in Jira."""
    try:
        subtask.update(fields={'description': new_description})
        logger.info(f"Successfully updated Sub-task {subtask.key} in Jira")
        return True
    except Exception as e:
        logger.error(f"Error updating Sub-task {subtask.key} in Jira: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def optimize_story(story: str):
    logger.info("Optimizing story...")
    try:
        config = load_config("config.json")
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
        logger.info("Story optimization completed successfully.")
        return optimized_story, agent_interactions, performance_metrics
    except Exception as e:
        logger.error(f"Error during story optimization: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def process_jira_subtasks(optimize_function):
    """Process all Jira Sub-tasks using the provided optimization function."""
    logger.info("Starting to process Jira subtasks...")
    jira = connect_to_jira()
    if not jira:
        logger.error("Failed to connect to Jira. Exiting.")
        return {"error": "Failed to connect to Jira"}

    subtasks = get_all_subtasks(jira)
    results = []

    for subtask in subtasks:
        logger.info(f"Processing subtask: {subtask.key}")
        original_description = subtask.fields.description
        try:
            optimized, agent_interactions, performance_metrics = await optimize_function(original_description)
            update_success = update_subtask_description(jira, subtask, optimized)
            if update_success:
                logger.info(f"Successfully processed and updated subtask {subtask.key} in Jira")
                results.append({
                    "key": subtask.key,
                    "original": original_description,
                    "optimized": optimized,
                    "performance_metrics": performance_metrics,
                    "jira_update_status": "Success"
                })
            else:
                logger.warning(f"Subtask {subtask.key} was optimized but failed to update in Jira")
                results.append({
                    "key": subtask.key,
                    "original": original_description,
                    "optimized": optimized,
                    "performance_metrics": performance_metrics,
                    "jira_update_status": "Failed"
                })
        except Exception as e:
            logger.error(f"Error processing Sub-task {subtask.key}: {str(e)}")
            logger.error(traceback.format_exc())
            results.append({
                "key": subtask.key,
                "error": str(e),
                "jira_update_status": "Failed"
            })

    logger.info("Finished processing all subtasks.")
    return results

async def main():
    logger.info("Starting Jira integration test")
    results = await process_jira_subtasks(optimize_story)
    
    logger.info("Jira integration test completed")
    logger.info(f"Processed {len(results)} subtasks")
    
    success_count = sum(1 for result in results if result.get("jira_update_status") == "Success")
    failure_count = sum(1 for result in results if result.get("jira_update_status") == "Failed")
    
    logger.info(f"Successfully updated {success_count} subtasks in Jira")
    logger.info(f"Failed to update {failure_count} subtasks in Jira")
    
    for result in results:
        if "error" in result:
            logger.error(f"Error processing subtask {result['key']}: {result['error']}")
        else:
            logger.info(f"Subtask {result['key']} - Jira update status: {result['jira_update_status']}")
            logger.debug(f"Original: {result['original'][:100]}...")
            logger.debug(f"Optimized: {result['optimized'][:100]}...")
            logger.debug(f"Performance metrics: {result['performance_metrics']}")
        logger.info("---")

if __name__ == "__main__":
    logger.info("Script started.")
    asyncio.run(main())
    logger.info("Script finished.")
