from typing import List, Callable
from pydantic import BaseModel

class AgentConfig(BaseModel):
    name: str
    instructions: str
    tools: List[str]

class Config(BaseModel):
    openai_model: str = "gpt-4o"
    agents: List[AgentConfig]
    tools: dict[str, Callable]

# Default configuration
default_config = Config(
    agents=[
        AgentConfig(
            name="Technical Requirements Agent",
            instructions="You are a Technical Analyst. Focus on the technical feasibility and requirements of each user story.",
            tools=["look_up_item", "transfer_to_ux", "transfer_to_qa", "transfer_to_stakeholder_liaison", "transfer_to_master"]
        ),
        AgentConfig(
            name="User Experience Agent",
            instructions="You are a UX Designer. Ensure user stories reflect end-user needs and usability standards.",
            tools=["transfer_to_technical_requirements", "transfer_to_qa", "transfer_to_stakeholder_liaison", "transfer_to_master"]
        ),
        AgentConfig(
            name="Quality Assurance Agent",
            instructions="You are a QA Specialist. Focus on making user stories testable and ensuring clarity for QA.",
            tools=["transfer_to_technical_requirements", "transfer_to_ux", "transfer_to_stakeholder_liaison", "transfer_to_master"]
        ),
        AgentConfig(
            name="Stakeholder Liaison Agent",
            instructions="You are a Stakeholder Representative. Ensure alignment with business priorities and capture input from stakeholders.",
            tools=["execute_refund", "transfer_to_technical_requirements", "transfer_to_ux", "transfer_to_qa", "transfer_to_master"]
        ),
        AgentConfig(
            name="Master Agent",
            instructions="You are a Lead Business Analyst. Your role is to oversee and guide the improvement of user stories.",
            tools=["transfer_to_technical_requirements", "transfer_to_ux", "transfer_to_qa", "transfer_to_stakeholder_liaison"]
        )
    ],
    tools={}  # This will be populated in main.py
)

# Function to load custom configuration
def load_config(config_path: str) -> Config:
    # Implement loading from a file (e.g., JSON or YAML)
    # For now, we'll just return the default config
    return default_config
