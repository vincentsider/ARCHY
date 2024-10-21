# Swarm System Manual

## Overview

The Swarm System is a multi-agent framework designed to optimize user stories through collaboration between specialized agents. This manual provides a comprehensive guide for understanding, using, and customizing the system.

## Table of Contents

1. [System Components](#system-components)
2. [Swarm Logic Flow](#swarm-logic-flow)
3. [Agent Creation and Configuration](#agent-creation-and-configuration)
4. [Adding Tools and Handoffs](#adding-tools-and-handoffs)
5. [Process Workflow](#process-workflow)
6. [Quality Evaluation](#quality-evaluation)
7. [Capturing the Final User Story](#capturing-the-final-user-story)
8. [Customization and Extension](#customization-and-extension)

## System Components

1. Configuration (`config.py`)
2. Main Application (`main.py`)
3. Agent Definition (`swarm/agent.py`)
4. Swarm Logic (`swarm/swarm.py`)
5. Tools (`swarm/tools.py`)

## Swarm Logic Flow

The swarm logic follows these main steps:

1. **Initialization**: The swarm is initialized with a list of agents and a configuration object. Each agent is created with a name, API key, model, instructions, and tools.

2. **Context Analysis**: When a user story is received, the swarm first analyzes the context using the Master Agent to understand the main intent of the story.

3. **Triage**: The swarm then triages the user story to determine which specialist agents are most relevant for the task.

4. **Processing**: The swarm processes the message by iterating through the relevant agents. This step is not strictly sequential for all agents, but rather focuses on the agents deemed relevant during the triage step. Each relevant agent:
   - Is provided with the user story and context analysis
   - Processes the information and provides its specific input
   - May consult other agents if its confidence is below a certain threshold
   - Can use tools or request handoffs to other agents if needed

5. **Feedback Loop**: After initial processing, the swarm enters a feedback loop where it generates a final summary, assesses its quality, and requests clarifications if needed.

6. **Final Output**: The swarm generates an optimized user story with acceptance criteria based on the collective input from all relevant agents.

## Agent Creation and Configuration

To create a new agent:

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
agents = [
    Agent(
        name=agent_config.name,
        api_key=os.getenv("OPENAI_API_KEY"),
        model=config.openai_model,
        instructions=agent_config.instructions,
        tools=agent_config.tools
    )
    for agent_config in config.agents
]

swarm = Swarm(agents, config)
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

2. Add the tool to the `tools_map` in the Swarm class initialization:

```python
self.tools_map = {tool.__name__: tool for tool in config.tools.values()}
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

4. To implement a handoff, use a transfer function in `swarm/tools.py`:

```python
def transfer_to_new_agent():
    return "HANDOFF:New Agent Name"
```

## Process Workflow

1. **User Story Submission**: A user story is submitted through the `/optimize_story` endpoint.
2. **Context Analysis**: The Master Agent analyzes the context of the user story.
3. **Triage**: The system determines which specialist agents are most relevant.
4. **Agent Processing**: Relevant agents process the story, providing their specialized input.
5. **Consultations and Handoffs**: Agents can consult each other or hand off tasks as needed.
6. **Feedback Loop**: The system generates a summary, assesses quality, and may request clarifications.
7. **Final Synthesis**: The Master Agent synthesizes all inputs into a final optimized user story.

## Quality Evaluation

The quality of the optimized user story is evaluated using the `assess_quality` method in the `Swarm` class. It checks for:

- Correct user story format
- Presence of "so that" clause
- Inclusion of acceptance criteria
- Coverage of different aspects (technical, UX, business, quality)
- Number and specificity of acceptance criteria

## Capturing the Final User Story

The final optimized user story is captured in the `optimize_story` function in `main.py`. It's returned as part of the `OptimizedUserStory` object and logged for easy integration with other systems like Jira.

## Customization and Extension

To customize or extend the swarm system:

1. **Add New Agents**: Create new agent configurations in `config.py` and update `main.py` to include them in the swarm.

2. **Modify Existing Agents**: Update the instructions or tools for existing agents in `config.py`.

3. **Add New Tools**: Define new tool functions in `swarm/tools.py` and add them to the relevant agents' configurations.

4. **Adjust Swarm Logic**: Modify the `process_message` method in `swarm/swarm.py` to change how the swarm processes user stories.

5. **Enhance Quality Evaluation**: Update the `assess_quality` method in `swarm/swarm.py` to refine how story quality is assessed.

6. **Extend API Functionality**: Add new endpoints or modify existing ones in `main.py` to provide additional features or integration points.

By following this guide, you can fully customize the swarm system, adding new agents, tools, and modifying the optimization process as needed.
