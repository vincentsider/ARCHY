import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
import base64

load_dotenv()

JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('PROJECT_KEY')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class JiraIntegrationError(Exception):
    pass

def get_auth_headers():
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_bytes = auth_str.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_auth = base64_bytes.decode('ascii')
    return {
        'Authorization': f'Basic {base64_auth}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

def validate_jira_config():
    if not all([JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY]):
        raise JiraIntegrationError("Jira configuration is incomplete. Please check your .env file.")

def fetch_epics() -> List[Dict[str, Any]]:
    validate_jira_config()
    url = f"{JIRA_HOST}/rest/api/3/search"
    jql = f'project = "{PROJECT_KEY}" AND issuetype = Epic'
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            params={'jql': jql, 'fields': 'summary,description'}
        )
        response.raise_for_status()
        epics = response.json()['issues']
        logger.info(f"Found {len(epics)} epics")
        for epic in epics:
            logger.info(f"Epic {epic['key']}: {epic['fields']['summary']}")
        return epics
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching epics: {e}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Request URL: {response.request.url}")
        logger.error(f"Request headers: {response.request.headers}")
        raise JiraIntegrationError(f"Failed to fetch epics: {str(e)}")

def fetch_stories(epic_key: str) -> List[Dict[str, Any]]:
    validate_jira_config()
    url = f"{JIRA_HOST}/rest/api/3/search"
    jql = f'project = "{PROJECT_KEY}" AND "Epic Link" = {epic_key} AND issuetype = Story'
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            params={'jql': jql, 'fields': 'summary,description'}
        )
        response.raise_for_status()
        stories = response.json()['issues']
        logger.info(f"Found {len(stories)} stories for epic {epic_key}")
        for story in stories:
            logger.info(f"Story {story['key']}: {story['fields']['summary']}")
        return stories
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching stories for epic {epic_key}: {e}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Request URL: {response.request.url}")
        logger.error(f"Request headers: {response.request.headers}")
        raise JiraIntegrationError(f"Failed to fetch stories for epic {epic_key}: {str(e)}")

def fetch_subtasks(story_key: str) -> List[Dict[str, Any]]:
    validate_jira_config()
    url = f"{JIRA_HOST}/rest/api/3/search"
    jql = f'project = "{PROJECT_KEY}" AND parent = {story_key} AND issuetype = Sub-task'
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            params={'jql': jql, 'fields': 'summary,description'}
        )
        response.raise_for_status()
        subtasks = response.json()['issues']
        logger.info(f"Found {len(subtasks)} subtasks for story {story_key}")
        for subtask in subtasks:
            logger.info(f"Subtask {subtask['key']}: {subtask['fields']['summary']}")
        return subtasks
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching subtasks for story {story_key}: {e}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Request URL: {response.request.url}")
        logger.error(f"Request headers: {response.request.headers}")
        raise JiraIntegrationError(f"Failed to fetch subtasks for story {story_key}: {str(e)}")

def update_subtask(issue_key: str, optimized_description: str):
    validate_jira_config()
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}"
    
    data = {
        "fields": {
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": optimized_description
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    try:
        response = requests.put(url, headers=get_auth_headers(), json=data)
        response.raise_for_status()
        return response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating subtask {issue_key}: {e}")
        logger.error(f"Response content: {response.content}")
        logger.error(f"Request URL: {response.request.url}")
        logger.error(f"Request headers: {response.request.headers}")
        raise JiraIntegrationError(f"Failed to update subtask {issue_key}: {str(e)}")

def process_epics_and_subtasks():
    try:
        epics = fetch_epics()
        for epic in epics:
            epic_key = epic['key']
            epic_description = epic['fields']['description']
            stories = fetch_stories(epic_key)
            
            for story in stories:
                story_key = story['key']
                story_description = story['fields']['description']
                subtasks = fetch_subtasks(story_key)
                
                for subtask in subtasks:
                    subtask_key = subtask['key']
                    subtask_description = subtask['fields']['description']
                    
                    # Here, we'll need to call our optimization function
                    # optimized_description = optimize_user_story(subtask_description, epic_description, story_description)
                    
                    # For now, let's just use a placeholder
                    optimized_description = f"Optimized: {subtask_description}"
                    
                    update_subtask(subtask_key, optimized_description)
    except JiraIntegrationError as e:
        logger.error(f"Jira integration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_epics_and_subtasks: {e}")
        raise

if __name__ == "__main__":
    process_epics_and_subtasks()
