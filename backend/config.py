from typing import List, Callable
from pydantic import BaseModel
from backend.swarm.tools import (
    look_up_item, execute_refund,
    transfer_to_technical_requirements, transfer_to_ux,
    transfer_to_qa, transfer_to_stakeholder_liaison, transfer_to_master
)

class AgentConfig(BaseModel):
    name: str
    instructions: str
    tools: List[str]

class Config(BaseModel):
    openai_model: str = "gpt-4o"
    agents: List[AgentConfig]
    tools: dict[str, Callable]
    max_clarification_rounds: int = 3
    quality_threshold: float = 0.8

# Default configuration
default_config = Config(
    agents=[
        AgentConfig(
            name="Master Agent",
            instructions="You are the Master Agent responsible for coordinating the optimization of user stories. Your role is to analyze the initial user story, decide which specialist agents to involve, and synthesize their inputs into a final, optimized user story. Use your judgment to determine which agents are necessary for each story, and don't hesitate to involve multiple agents if needed. Your goal is to produce a comprehensive, well-rounded user story that covers technical, UX, and business aspects as appropriate. When synthesizing the final user story, ensure it follows the format 'As a user, I want... so that...' followed by a prioritized list of acceptance criteria.",
            tools=["transfer_to_technical_requirements", "transfer_to_ux", "transfer_to_qa", "transfer_to_stakeholder_liaison"]
        ),
        AgentConfig(
            name="Technical Requirements Agent",
            instructions="You are the Technical Requirements Agent. Your role is to analyze user stories from a technical perspective and break them down into specific technical requirements. Focus on the technical feasibility and implementation details of each user story.",
            tools=["look_up_item", "transfer_to_master"]
        ),
        AgentConfig(
            name="User Experience Agent",
            instructions="You are the UX Agent. Your role is to optimize user stories by considering the user experience perspective. Focus on usability, accessibility, and user interface design considerations. Ensure user stories reflect end-user needs and usability standards.",
            tools=["transfer_to_master"]
        ),
        AgentConfig(
            name="Quality Assurance Agent",
            instructions="You are the QA Agent. Your role is to review and refine user stories to ensure they are testable and meet quality standards. Focus on defining acceptance criteria, identifying potential edge cases, and ensuring clarity for QA processes.",
            tools=["transfer_to_master"]
        ),
        AgentConfig(
            name="Stakeholder Liaison Agent",
            instructions="You are the Stakeholder Liaison Agent. Your role is to review the optimized user story and ensure it aligns with business goals and user needs. Provide specific business-related acceptance criteria and suggest any necessary adjustments to meet stakeholder expectations. Ensure alignment with business priorities and capture input from stakeholders.",
            tools=["execute_refund", "transfer_to_master"]
        )
    ],
    tools={
        "look_up_item": look_up_item,
        "execute_refund": execute_refund,
        "transfer_to_technical_requirements": transfer_to_technical_requirements,
        "transfer_to_ux": transfer_to_ux,
        "transfer_to_qa": transfer_to_qa,
        "transfer_to_stakeholder_liaison": transfer_to_stakeholder_liaison,
        "transfer_to_master": transfer_to_master,
    },
    max_clarification_rounds=3,
    quality_threshold=0.8
)

# Function to load custom configuration
def load_config(config_path: str) -> Config:
    # Implement loading from a file (e.g., JSON or YAML)
    # For now, we'll just return the default config
    return default_config
