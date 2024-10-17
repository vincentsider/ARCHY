import sys
import os
import asyncio

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jira_integration import fetch_epics, fetch_subtasks, update_subtask
from main import optimize_story_logic

async def test_jira_integration():
    print("Testing Jira Integration")
    
    # Test fetching epics
    print("\nFetching epics...")
    epics = fetch_epics()
    print(f"Fetched {len(epics)} epics")
    
    if epics:
        # Test fetching subtasks for the first epic
        epic = epics[0]
        print(f"\nFetching subtasks for epic: {epic['key']}")
        subtasks = fetch_subtasks(epic['key'])
        print(f"Fetched {len(subtasks)} subtasks")
        
        if subtasks:
            # Test optimizing and updating a subtask
            subtask = subtasks[0]
            print(f"\nOptimizing subtask: {subtask['key']}")
            
            original_description = subtask['fields']['description']
            epic_description = epic['fields']['description']
            
            optimize_func = optimize_story_logic(original_description, epic_description)
            result = await optimize_func()
            
            print(f"Original description: {original_description[:100]}...")
            print(f"Optimized description: {result.optimized[:100]}...")
            
            print(f"\nUpdating subtask: {subtask['key']}")
            update_result = update_subtask(subtask['key'], result.optimized)
            print(f"Update result: {update_result}")
        else:
            print("No subtasks found for testing")
    else:
        print("No epics found for testing")

if __name__ == "__main__":
    asyncio.run(test_jira_integration())
