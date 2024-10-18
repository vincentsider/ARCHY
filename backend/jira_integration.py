import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

# Jira connection details
JIRA_HOST = os.getenv('JIRA_HOST')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
PROJECT_KEY = os.getenv('PROJECT_KEY')

def connect_to_jira():
    """Establish a connection to Jira."""
    try:
        jira = JIRA(server=JIRA_HOST, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
        return jira
    except Exception as e:
        print(f"Error connecting to Jira: {str(e)}")
        return None

def get_all_issues(jira):
    """Fetch all Epics, Tasks, and Sub-tasks from Jira."""
    issues = []
    for issue_type in ['Epic', 'Task', 'Sub-task']:
        jql = f'project = {PROJECT_KEY} AND issuetype = "{issue_type}"'
        batch = jira.search_issues(jql, maxResults=100)
        issues.extend(batch)
    return issues

def update_subtask_description(jira, subtask, new_description):
    """Update the description of a Sub-task in Jira."""
    try:
        subtask.update(fields={'description': new_description})
        print(f"Updated Sub-task {subtask.key}")
    except Exception as e:
        print(f"Error updating Sub-task {subtask.key}: {str(e)}")

def optimize_subtask_description(description, epic_description):
    """Optimize the Sub-task description based on the Epic's context."""
    # TODO: Implement the optimization logic
    # This function should use NLP techniques to improve the description
    # and ensure the persona is clearly defined based on the Epic's context
    return description  # Placeholder return, replace with actual optimization

def main():
    jira = connect_to_jira()
    if not jira:
        return

    issues = get_all_issues(jira)
    epics = {issue.key: issue for issue in issues if issue.fields.issuetype.name == 'Epic'}
    
    for issue in issues:
        if issue.fields.issuetype.name == 'Sub-task':
            epic_key = issue.fields.parent.fields.parent.key
            epic = epics.get(epic_key)
            if epic:
                new_description = optimize_subtask_description(issue.fields.description, epic.fields.description)
                update_subtask_description(jira, issue, new_description)

if __name__ == "__main__":
    main()
