import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.jira_integration import connect_to_jira, get_all_subtasks, update_subtask_description, process_jira_subtasks

@pytest.fixture
def mock_jira():
    with patch('backend.jira_integration.JIRA') as mock_jira_class:
        mock_jira_instance = MagicMock()
        mock_jira_class.return_value = mock_jira_instance
        yield mock_jira_instance

def test_connect_to_jira(mock_jira):
    result = connect_to_jira()
    assert result is not None
    assert mock_jira is result

def test_get_all_subtasks(mock_jira):
    mock_jira.search_issues.return_value = [MagicMock(), MagicMock()]
    result = get_all_subtasks(mock_jira)
    assert len(result) == 2
    mock_jira.search_issues.assert_called_once()

def test_update_subtask_description(mock_jira):
    mock_subtask = MagicMock()
    update_subtask_description(mock_jira, mock_subtask, "New description")
    mock_subtask.update.assert_called_once_with(fields={'description': "New description"})

@pytest.mark.asyncio
async def test_process_jira_subtasks():
    mock_optimize_function = AsyncMock()
    mock_optimize_function.return_value = ("Optimized", [], {"quality_score": 0.9})
    mock_subtask = MagicMock()
    mock_subtask.fields.description = "Original description"
    mock_subtask.key = "TEST-1"

    with patch('backend.jira_integration.connect_to_jira') as mock_connect, \
         patch('backend.jira_integration.get_all_subtasks') as mock_get_all_subtasks, \
         patch('backend.jira_integration.update_subtask_description') as mock_update_subtask:
        mock_jira = MagicMock()
        mock_connect.return_value = mock_jira
        mock_get_all_subtasks.return_value = [mock_subtask]

        results = await process_jira_subtasks(mock_optimize_function)

    assert len(results) == 1
    assert results[0]['key'] == "TEST-1"
    assert results[0]['original'] == "Original description"
    assert results[0]['optimized'] == "Optimized"
    assert results[0]['performance_metrics'] == {"quality_score": 0.9}
    mock_optimize_function.assert_called_once_with("Original description")
    mock_update_subtask.assert_called_once_with(mock_jira, mock_subtask, "Optimized")

# Add more tests as needed for error handling and edge cases
