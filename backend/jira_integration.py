import os
from jira import JIRA
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Jira connection details
JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('PROJECT_KEY')

logger = logging.getLogger(__name__)

def connect_to_jira():
    """Establish a connection to Jira."""
    try:
        jira = JIRA(server=JIRA_HOST, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        return jira
    except Exception as e:
        logger.error(f"Error connecting to Jira: {str(e)}")
        return None

def get_all_subtasks(jira):
    """Fetch all Sub-tasks from Jira."""
    jql = f'project = {PROJECT_KEY} AND issuetype = Sub-task'
    return jira.search_issues(jql, maxResults=False)

def update_subtask_description(jira, subtask, new_description):
    """Update the description of a Sub-task in Jira."""
    try:
        subtask.update(fields={'description': new_description})
        logger.info(f"Updated Sub-task {subtask.key}")
    except Exception as e:
        logger.error(f"Error updating Sub-task {subtask.key}: {str(e)}")

async def process_jira_subtasks(optimize_function):
    """Process all Jira Sub-tasks using the provided optimization function."""
    jira = connect_to_jira()
    if not jira:
        return {"error": "Failed to connect to Jira"}

    subtasks = get_all_subtasks(jira)
    results = []

    for subtask in subtasks:
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
        except Exception as e:
            logger.error(f"Error processing Sub-task {subtask.key}: {str(e)}")
            results.append({
                "key": subtask.key,
                "error": str(e)
            })

    return results
