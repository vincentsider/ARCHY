from typing import List, Dict, Any, Callable
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_TOKENS = 500  # Maximum tokens for optimized story
RATE_LIMIT = 20  # Number of requests per minute
RATE_LIMIT_PERIOD = 60  # Time period in seconds

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            now = time.time()
            self.calls = [call for call in self.calls if call > now - self.period]
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] - (now - self.period)
                time.sleep(sleep_time)
            self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

rate_limiter = RateLimiter(RATE_LIMIT, RATE_LIMIT_PERIOD)

class Agent:
    def __init__(self, name: str, role: str, instructions: str):
        self.name = name
        self.role = role
        self.instructions = instructions

    @rate_limiter
    def process(self, user_story: str) -> str:
        logger.info(f"{self.name} processing user story: {user_story}")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a {self.role}. {self.instructions}"},
                    {"role": "user", "content": f"Analyze and improve this user story: {user_story}"}
                ],
                max_tokens=MAX_TOKENS
            )
            result = response.choices[0].message.content
            logger.info(f"{self.name} completed processing. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {self.name} processing: {str(e)}")
            raise

class MasterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Master Agent",
            role="Lead Business Analyst",
            instructions="Your role is to oversee and guide the improvement of user stories. Ensure that all user stories are clear, comprehensive, and actionable, meeting a high standard for developer usability. Provide a final, refined user story that incorporates all the feedback from supporting agents."
        )
        self.supporting_agents = []

    def add_supporting_agent(self, agent: Agent):
        self.supporting_agents.append(agent)

    def orchestrate(self, user_story: str) -> str:
        logger.info(f"Master Agent starting orchestration for user story: {user_story}")
        refined_story = user_story
        feedback = []
        for agent in self.supporting_agents:
            logger.info(f"Master Agent delegating to {agent.name}")
            try:
                agent_feedback = agent.process(refined_story)
                feedback.append(f"{agent.name} feedback: {agent_feedback}")
            except Exception as e:
                logger.error(f"Error in {agent.name} processing: {str(e)}")
                # Continue with the next agent if one fails
                continue
        
        logger.info("Master Agent performing final refinement")
        final_refinement = self.process(f"Original story: {user_story}\n\nFeedback:\n" + "\n".join(feedback))
        logger.info(f"Master Agent completed orchestration. Final refinement: {final_refinement}")
        return final_refinement

    @rate_limiter
    def process(self, input_text: str) -> str:
        logger.info(f"{self.name} processing: {input_text}")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a {self.role}. {self.instructions}"},
                    {"role": "user", "content": f"{input_text}\n\nProvide a final, refined user story that incorporates all the feedback:"}
                ],
                max_tokens=MAX_TOKENS
            )
            result = response.choices[0].message.content
            logger.info(f"{self.name} completed processing. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {self.name} processing: {str(e)}")
            raise

# Supporting Agents
technical_requirements_agent = Agent(
    name="Technical Requirements Agent",
    role="Technical Analyst",
    instructions="Focus on the technical feasibility and requirements of the user story. Identify potential technical risks or needs for technical clarity. Suggest specific technical refinements to align the user story with development capabilities. Provide concrete technical acceptance criteria."
)

ux_agent = Agent(
    name="User Experience Agent",
    role="UX Designer",
    instructions="Ensure the user story reflects end-user needs and usability standards. Recommend specific adjustments for user-centered design principles. Highlight areas where user needs should be more explicitly addressed. Suggest usability-focused acceptance criteria."
)

qa_agent = Agent(
    name="Quality Assurance Agent",
    role="QA Specialist",
    instructions="Focus on making the user story testable and ensuring clarity for QA. Suggest specific revisions for clear, measurable acceptance criteria. Identify areas where the story may lack testable components. Propose potential edge cases or scenarios that should be considered."
)

stakeholder_liaison_agent = Agent(
    name="Stakeholder Liaison Agent",
    role="Stakeholder Representative",
    instructions="Ensure alignment with business priorities and stakeholder needs. Provide feedback on business objectives and strategic considerations. Suggest refinements to enhance the user story's value proposition. Propose business-oriented acceptance criteria."
)

# Set up Master Agent with supporting agents
master_agent = MasterAgent()
master_agent.add_supporting_agent(technical_requirements_agent)
master_agent.add_supporting_agent(ux_agent)
master_agent.add_supporting_agent(qa_agent)
master_agent.add_supporting_agent(stakeholder_liaison_agent)

def optimize_user_story(user_story: str) -> str:
    """
    Optimize a user story using the Master Agent and its supporting agents.
    """
    logger.info(f"Starting user story optimization for: {user_story}")
    try:
        optimized_story = master_agent.orchestrate(user_story)
        logger.info(f"User story optimization completed. Optimized story: {optimized_story}")
        return optimized_story
    except Exception as e:
        logger.error(f"Error in user story optimization: {str(e)}")
        raise

# Mock function for Jira integration (to be replaced with actual Jira API calls)
def get_jira_user_stories() -> List[str]:
    return [
        "As a user, I want to log in to the system so that I can access my account.",
        "As an admin, I want to generate reports on user activity.",
        "As a customer, I want to view my order history."
    ]

def update_jira_user_story(story_id: str, updated_story: str):
    # This function would update the story in Jira
    # For now, we'll just print the updated story
    print(f"Updated story {story_id}: {updated_story}")

# Main function to process all user stories
def process_all_user_stories():
    user_stories = get_jira_user_stories()
    for i, story in enumerate(user_stories):
        try:
            optimized_story = optimize_user_story(story)
            update_jira_user_story(f"STORY-{i+1}", optimized_story)
        except Exception as e:
            logger.error(f"Error processing story {i+1}: {str(e)}")
            continue

# Test the system
if __name__ == "__main__":
    process_all_user_stories()
