# Swarm System Manual

## Overview

The Swarm System is a multi-agent framework designed to optimize user stories through collaboration between specialized agents. This manual provides a comprehensive guide for understanding, using, and customizing the system.

## Table of Contents

1. [System Components](#system-components)
2. [System Flow](#system-flow)
3. [Agent Creation](#agent-creation)
4. [Adding Tools and Handoffs](#adding-tools-and-handoffs)
5. [Process Workflow](#process-workflow)
6. [Quality Evaluation](#quality-evaluation)
7. [Capturing the Final User Story](#capturing-the-final-user-story)

## System Components

1. Configuration (`config.py`)
2. Main Application (`main.py`)
3. Agent Definition (`swarm/agent.py`)
4. Swarm Logic (`swarm/swarm.py`)
5. Tools (`swarm/tools.py`)

## System Flow

1. **Configuration Loading**: The system starts by loading the configuration from `config.py`.
2. **Agent Creation**: Agents are created in `main.py` based on the configuration.
3. **Swarm Initialization**: The Swarm is initialized with the created agents.
4. **User Story Processing**: When a user story is submitted, the Swarm processes it through multiple agents.
5. **Agent Interactions**: Agents can hand off tasks to each other using transfer tools.
6. **Story Optimization**: The final optimized story is returned after all agent interactions.

## Agent Creation

To create a new agent, follow these steps:

1. Update the `config.py` file to include the new agent configuration:

```python
agents = [
    # ... existing agents ...
    {
        "name": "New Agent Name",
        "instructions": "Detailed instructions for the new agent's role and responsibilities.",
        "tools": ["tool1", "tool2", "transfer_to_master"]
    }
]
```

2. In `main.py`, ensure the agent is created when loading the configuration:

```python
agents = []
for agent_config in config.agents:
    agent_tools = [config.tools[tool] for tool in agent_config.tools if tool in config.tools]
    agent = Agent(
        name=agent_config.name,
        instructions=agent_config.instructions,
        tools=agent_tools,
        model=config.openai_model
    )
    agents.append(agent)

swarm = Swarm(agents)
```

## Adding Tools and Handoffs

1. To add a new tool, define the tool function in `swarm/tools.py`:

```python
def new_tool(param1: str, param2: int) -> str:
    """
    Description of what the new tool does.
    
    :param param1: Description of param1
    :param param2: Description of param2
    :return: Description of the return value
    """
    # Tool implementation
    return "Tool result"
```

2. Update the `config.tools` dictionary in `main.py` to include the new tool:

```python
config.tools = {
    # ... existing tools ...
    "new_tool": new_tool,
}
```

3. Add the tool to the appropriate agent's configuration in `config.py`:

```python
agents = [
    {
        "name": "Agent Name",
        "instructions": "Agent instructions",
        "tools": ["existing_tool", "new_tool", "transfer_to_master"]
    }
]
```

4. To implement a handoff, use a transfer tool in the agent's response:

```python
return {
    "content": "Transferring to Technical Requirements Agent for detailed analysis.",
    "function_call": {
        "name": "transfer_to_technical_requirements",
        "arguments": "{}"
    }
}
```

## Process Workflow

1. **User Story Submission**: A user story is submitted through the `/optimize_story` endpoint.
2. **Initial Processing**: The Swarm starts processing with the Master Agent.
3. **Agent Analysis**: Each agent analyzes the story based on its specialization.
4. **Tool Usage**: Agents can use tools to perform specific actions or analyses.
5. **Handoffs**: Agents can transfer control to other agents using transfer tools.
6. **Iteration**: The process continues through multiple agents until optimization is complete.
7. **Final Synthesis**: The Master Agent synthesizes all inputs into a final optimized user story.

## Quality Evaluation

The quality of the optimized user story is evaluated using the `assess_quality` method in the `Swarm` class:

```python
def assess_quality(self, final_response: str) -> float:
    score = 0.0
    if final_response.startswith("As a user, I want"):
        score += 0.3
    if "so that" in final_response:
        score += 0.2
    if "Acceptance Criteria:" in final_response:
        score += 0.2
    
    aspects = ['technical', 'ux', 'business', 'quality']
    covered_aspects = sum(1 for aspect in aspects if aspect.lower() in final_response.lower())
    score += covered_aspects * 0.075
    
    criteria_count = final_response.count("\n") - 1
    score += min(criteria_count * 0.025, 0.25)
    
    return min(score, 1.0)
```

This method evaluates the story based on:
- Proper user story format
- Inclusion of "so that" clause
- Presence of acceptance criteria
- Coverage of different aspects (technical, UX, business, quality)
- Number of detailed criteria

## Capturing the Final User Story

The final optimized user story is captured in the `optimize_story` function in `main.py`:

```python
@app.post("/optimize_story", response_model=OptimizedUserStory)
@rate_limit("5/minute")
async def optimize_story(user_story: UserStory, request: Request):
    try:
        optimized, agent_interactions, performance_metrics = await optimize_story_cached(user_story.content)()
        
        # Log the final user story for easy access and integration
        logger.info(f"Final User Story for Jira Integration:\n{optimized}")
        
        return OptimizedUserStory(
            original=user_story.content,
            optimized=optimized,
            agent_interactions=agent_interactions,
            model=config.openai_model,
            performance_metrics=performance_metrics
        )
    except Exception as e:
        logger.error(f"Error occurred while optimizing story: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while optimizing the story: {str(e)}")
```

The optimized story is logged and returned as part of the `OptimizedUserStory` object, which can be easily integrated with other platforms like Jira.

By following this guide, users can fully customize the swarm system, adding new agents, tools, and modifying the optimization process as needed. The provided code snippets and examples should help in understanding and implementing changes to the system.
