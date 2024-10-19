import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from backend.main import app, swarm, config, optimize_story_logic
from backend.swarm.swarm import Swarm
from backend.swarm.agent import Agent

client = TestClient(app)

@pytest.mark.asyncio
async def test_optimize_story():
    with patch('backend.main.optimize_story_logic', new_callable=AsyncMock) as mock_optimize:
        mock_optimize.return_value = ("Optimized story", [], {"quality_score": 0.9})
        response = client.post("/optimize_story", json={"content": "Test story"})
        assert response.status_code == 200
        assert response.json()["original"] == "Test story"
        assert response.json()["optimized"] == "Optimized story"
        assert response.json()["performance_metrics"]["quality_score"] == 0.9

@pytest.mark.asyncio
async def test_process_all_stories():
    with patch('backend.main.process_stories_background', new_callable=AsyncMock) as mock_process:
        response = client.post("/process_all_stories", json=["Story 1", "Story 2"])
        assert response.status_code == 200
        assert response.json() == {"message": "Story optimization started in the background"}
        mock_process.assert_called_once()

@pytest.mark.asyncio
async def test_get_optimization_status():
    response = client.get("/optimization_status")
    assert response.status_code == 200
    assert "total_stories" in response.json()
    assert "processed_stories" in response.json()
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_swarm_initialization():
    test_agents = [
        Agent("Master Agent", "Test instructions 1", [], "gpt-3.5-turbo"),
        Agent("Test Agent 1", "Test instructions 2", [], "gpt-3.5-turbo"),
        Agent("Test Agent 2", "Test instructions 3", [], "gpt-3.5-turbo")
    ]
    test_config = MagicMock()
    test_swarm = Swarm(test_agents, test_config)
    assert len(test_swarm.agents) == 3
    assert "Master Agent" in test_swarm.agents
    assert "Test Agent 1" in test_swarm.agents
    assert "Test Agent 2" in test_swarm.agents

@pytest.mark.asyncio
async def test_analyze_context():
    mock_master_agent = AsyncMock(spec=Agent)
    mock_master_agent.name = "Master Agent"
    mock_master_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Analyzed context"))]
    )
    
    test_swarm = Swarm([mock_master_agent], MagicMock())
    test_swarm.master_agent = mock_master_agent

    result = await test_swarm.analyze_context("Test user story")
    assert result == "Analyzed context"
    mock_master_agent.get_completion.assert_called_once()

@pytest.mark.asyncio
async def test_triage_user_story():
    mock_master_agent = AsyncMock(spec=Agent)
    mock_master_agent.name = "Master Agent"
    mock_master_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Agent 1, Agent 2"))]
    )
    
    test_swarm = Swarm([mock_master_agent], MagicMock())
    test_swarm.master_agent = mock_master_agent
    test_swarm.agents = {"Agent 1": MagicMock(), "Agent 2": MagicMock(), "Agent 3": MagicMock()}

    result = await test_swarm.triage_user_story("Test user story", "Test context")
    assert result == ["Agent 1", "Agent 2"]
    mock_master_agent.get_completion.assert_called_once()

@pytest.mark.asyncio
async def test_process_message():
    mock_master_agent = AsyncMock(spec=Agent)
    mock_agent1 = AsyncMock(spec=Agent)
    mock_agent2 = AsyncMock(spec=Agent)

    mock_master_agent.name = "Master Agent"
    mock_agent1.name = "Agent 1"
    mock_agent2.name = "Agent 2"

    # Add 'tools' attribute to mock agents
    mock_master_agent.tools = []
    mock_agent1.tools = []
    mock_agent2.tools = []

    mock_master_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Agent 1, Agent 2"))]
    )
    mock_agent1.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Agent 1 response"))]
    )
    mock_agent2.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Agent 2 response"))]
    )

    test_swarm = Swarm([mock_master_agent, mock_agent1, mock_agent2], MagicMock())
    test_swarm.master_agent = mock_master_agent
    test_swarm.agents = {"Master Agent": mock_master_agent, "Agent 1": mock_agent1, "Agent 2": mock_agent2}

    with patch.object(test_swarm, 'generate_final_summary', new_callable=AsyncMock) as mock_generate_summary:
        mock_generate_summary.return_value = "Final summary"
        
        result, interactions, metrics = await test_swarm.process_message("Test message", {}, "Test context")
        
        assert result == "Final summary"
        assert len(interactions) > 0
        assert "execution_time" in metrics
        assert "iterations_used" in metrics
        assert "quality_score" in metrics

@pytest.mark.asyncio
async def test_run_agent():
    mock_agent = AsyncMock(spec=Agent)
    mock_agent.name = "Test Agent"
    mock_agent.tools = []  # Add 'tools' attribute
    mock_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Test response",
            tool_calls=[MagicMock(
                function=MagicMock(
                    name="test_tool",
                    arguments="{}"
                )
            )]
        ))]
    )

    mock_master_agent = AsyncMock(spec=Agent)
    mock_master_agent.name = "Master Agent"
    mock_master_agent.tools = []  # Add 'tools' attribute

    test_swarm = Swarm([mock_master_agent, mock_agent], MagicMock())
    
    with patch.object(test_swarm, 'execute_tool_call', new_callable=AsyncMock) as mock_execute_tool:
        mock_execute_tool.return_value = "Tool result"
        
        result = await test_swarm.run_agent(mock_agent, [{"role": "user", "content": "Test message"}], {"test_tool": lambda: None})
        
        assert result.agent == mock_agent
        assert len(result.messages) == 3  # user message, agent response, and tool response
        assert result.decision == "No decision recorded"

@pytest.mark.asyncio
async def test_generate_final_summary():
    mock_master_agent = AsyncMock(spec=Agent)
    mock_master_agent.name = "Master Agent"
    mock_master_agent.tools = []  # Add 'tools' attribute
    mock_master_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Final summary"))]
    )

    test_swarm = Swarm([mock_master_agent], MagicMock())
    test_swarm.master_agent = mock_master_agent

    with patch.object(test_swarm, 'validate_final_response', return_value=True):
        result = await test_swarm.generate_final_summary([{"role": "user", "content": "Test message"}], "Test context")
        
        assert result == "Final summary"
        mock_master_agent.get_completion.assert_called_once()

@pytest.mark.asyncio
async def test_pega_specialist_handoff():
    mock_pega_specialist = AsyncMock(spec=Agent)
    mock_pega_specialist.name = "Pega Specialist"
    mock_pega_specialist.tools = []  # Add 'tools' attribute
    mock_pega_specialist.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Pega Specialist response",
            tool_calls=[MagicMock(
                function=MagicMock(
                    name="transfer_to_technical_requirements",
                    arguments="{}"
                )
            )]
        ))]
    )

    mock_technical_requirements = AsyncMock(spec=Agent)
    mock_technical_requirements.name = "Technical Requirements Agent"
    mock_technical_requirements.tools = []  # Add 'tools' attribute
    mock_technical_requirements.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Technical Requirements response"
        ))]
    )

    mock_master_agent = AsyncMock(spec=Agent)
    mock_master_agent.name = "Master Agent"
    mock_master_agent.tools = []  # Add 'tools' attribute
    mock_master_agent.get_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(
            content="Master Agent response"
        ))]
    )

    mock_agents = {
        "Pega Specialist": mock_pega_specialist,
        "Technical Requirements Agent": mock_technical_requirements,
        "Master Agent": mock_master_agent
    }

    mock_config = MagicMock()
    mock_config.max_clarification_rounds = 1
    mock_config.quality_threshold = 0.8

    test_swarm = Swarm(list(mock_agents.values()), mock_config)
    test_swarm.agents = mock_agents
    test_swarm.master_agent = mock_master_agent

    with patch('backend.swarm.swarm.Swarm.execute_tool_call', new_callable=AsyncMock) as mock_execute_tool_call, \
         patch('backend.swarm.swarm.Swarm.triage_user_story', new_callable=AsyncMock) as mock_triage:
        mock_execute_tool_call.return_value = "HANDOFF:Technical Requirements Agent"
        mock_triage.return_value = ["Pega Specialist"]

        message = "Test user story"
        context_analysis = "Test context analysis"
        tools_map = {}

        final_response, agent_interactions, performance_metrics = await test_swarm.process_message(message, tools_map, context_analysis)

        # Verify that the Pega Specialist was called
        mock_pega_specialist.get_completion.assert_called_once()

        # Verify that the Technical Requirements Agent was called due to handoff
        mock_technical_requirements.get_completion.assert_called_once()

        # Verify that the Master Agent was called to generate the final summary
        mock_master_agent.get_completion.assert_called()

        # Check if the agent interactions contain the expected handoff
        handoff_interaction = next((interaction for interaction in agent_interactions if interaction.get('decision') == "Handoff to Technical Requirements Agent"), None)
        assert handoff_interaction is not None, "Expected handoff interaction not found"

        # Verify the structure of the final response
        assert isinstance(final_response, str), "Final response should be a string"
        assert isinstance(agent_interactions, list), "Agent interactions should be a list"
        assert isinstance(performance_metrics, dict), "Performance metrics should be a dictionary"

@pytest.mark.asyncio
async def test_rate_limiting():
    class MockLimiter:
        def __init__(self):
            self.call_count = 0

        def limit(self, limit_string):
            def decorator(func):
                async def wrapper(*args, **kwargs):
                    self.call_count += 1
                    print(f"Request {self.call_count} received")
                    if self.call_count <= 5:
                        result = await func(*args, **kwargs)
                        print(f"Request {self.call_count} succeeded")
                        return result
                    print(f"Request {self.call_count} rate limited")
                    raise HTTPException(status_code=429, detail="5 per 1 minute")
                return wrapper
            return decorator

    mock_limiter = MockLimiter()

    with patch('backend.main.limiter.limit', mock_limiter.limit), \
         patch('backend.main.optimize_story_logic', new_callable=AsyncMock) as mock_optimize:
        mock_optimize.return_value = ("Mocked optimized story", [], {"quality_score": 0.9})
        
        # First 5 requests should succeed
        for i in range(5):
            response = client.post("/optimize_story", json={"content": "Test story"})
            print(f"Response {i+1} status code: {response.status_code}")
            assert response.status_code == 200, f"Request {i+1} should have succeeded"
            assert response.json()["optimized"] == "Mocked optimized story"

        # 6th request should be rate limited
        response = client.post("/optimize_story", json={"content": "Test story"})
        print(f"Response 6 status code: {response.status_code}")
        assert response.status_code == 429, "The 6th request should be rate limited"
        assert response.json() == {"detail": "5 per 1 minute"}

    print(f"Total calls to rate limiter: {mock_limiter.call_count}")
    assert mock_limiter.call_count == 6, f"Expected 6 calls to rate limiter, but got {mock_limiter.call_count}"
