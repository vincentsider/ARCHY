# Swarm Logic Explanation

This document provides a comprehensive explanation of our current swarm logic implementation, including the swarm flow, agent handoff process, how to add new agents and tools, and how to modify the swarm logic.

## 1. Swarm Flow

Our swarm logic follows these main steps:

1. **Initialization**: The swarm is initialized with a list of agents and a configuration object. Each agent is created with a name, API key, model, instructions, and tools.

2. **Context Analysis**: When a user story is received, the swarm first analyzes the context using the Master Agent to understand the main intent of the story.

3. **Triage**: The swarm then triages the user story to determine which specialist agents are most relevant for the task.

4. **Processing**: The swarm processes the message by iterating through the relevant agents. This step is not strictly sequential for all agents, but rather focuses on the agents deemed relevant during the triage step. Here's a more detailed breakdown:

   a. The swarm identifies the relevant agents based on the triage results.
   
   b. For each relevant agent:
      - The agent is provided with the user story and context analysis.
      - The agent processes the information and provides its specific input.
      - If the agent's confidence is below a certain threshold, it may consult other agents.
      - The agent may use tools or request handoffs to other agents if needed.
   
   c. The process is iterative, allowing for multiple rounds of input and refinement.
   
   d. Not all agents in the swarm are necessarily involved in every user story optimization; only those identified as relevant participate.

5. **Feedback Loop**: After initial processing, the swarm enters a feedback loop where it generates a final summary, assesses its quality, and requests clarifications if needed.

6. **Final Output**: The swarm generates an optimized user story with acceptance criteria based on the collective input from all relevant agents.

## 2. Agent Handoff

Agent handoff is implemented through a system of transfer functions and consultation requests:

1. **Transfer Functions**: Each agent has access to transfer functions (e.g., `transfer_to_technical_requirements()`) that allow it to hand off the conversation to another agent when necessary.

2. **Consultation Requests**: Agents can request consultations from other agents using the `request_consultation()` method. This allows agents to seek input from specialists without fully transferring control.

3. **Confidence Assessment**: The swarm assesses the confidence of each agent's response. If confidence is low, it may trigger consultations with other agents.

4. **Master Agent Oversight**: The Master Agent oversees the process and can request additional input from specialists when needed.

## 3. Adding New Agents and Tools

To add new agents and tools to the swarm:

1. **Adding a New Agent**:
   - Define the agent's configuration in the `config.json` file, including its name, instructions, and tools.
   - Create a new transfer function in `backend/swarm/tools.py` for the new agent (e.g., `transfer_to_new_agent()`).
   - Update the `agents` list in `backend/main.py` to include the new agent.

2. **Adding New Tools**:
   - Define the new tool function in `backend/swarm/tools.py`.
   - Add the tool to the appropriate agent's configuration in `config.json`.
   - Ensure the tool is properly mapped in the `tools_map` in the Swarm class.

## 4. Modifying Swarm Logic

To modify the swarm logic:

1. **Adjusting the Swarm Flow**:
   - Modify the `process_message()` method in the `Swarm` class (`backend/swarm/swarm.py`) to change the overall flow of the swarm.

2. **Changing Agent Behavior**:
   - Update the agent's instructions in the `config.json` file.
   - Modify the `run()` method in the `Agent` class (`backend/swarm/agent.py`) to change how agents process messages and make decisions.

3. **Modifying the Feedback Loop**:
   - Adjust the `generate_final_summary()` and `assess_quality()` methods in the `Swarm` class to change how the final output is generated and evaluated.

4. **Changing Handoff Logic**:
   - Modify the `run_agent()` method in the `Swarm` class to adjust how handoffs are triggered and processed.

5. **Adjusting Performance Parameters**:
   - Update the `max_iterations`, `early_stopping_threshold`, and `confidence_threshold` attributes in the `Swarm` class to fine-tune the swarm's performance.

## 5. Key Components

1. **Swarm Class**: Orchestrates the overall process, manages agent interactions, and generates the final output.

2. **Agent Class**: Represents individual agents, handles completions, and processes tool calls.

3. **Tools**: Provide specific functionalities that agents can use, including transfers between agents.

4. **Main Application**: Sets up the FastAPI server, initializes the swarm, and handles API endpoints for story optimization and Jira integration.

## 6. Compliance with OpenAI Swarm Best Practices

Our implementation aligns well with OpenAI Swarm best practices:

1. **Modularity**: The system is designed with separate classes for Swarm and Agent, allowing for easy expansion and modification.

2. **Dynamic Agent Selection**: The triage process ensures that only relevant agents are involved in each task.

3. **Flexible Communication**: Agents can transfer control and request consultations, allowing for complex interactions.

4. **Quality Control**: The system includes mechanisms for assessing confidence and quality, with feedback loops for improvement.

5. **Scalability**: The design allows for easy addition of new agents and tools.

6. **Error Handling and Logging**: Comprehensive error handling and logging are implemented throughout the system.

7. **Performance Monitoring**: The system tracks and reports on performance metrics for each optimization task.

By following this structure, our swarm logic implementation provides a robust and flexible system for optimizing user stories through collaborative agent interactions.
