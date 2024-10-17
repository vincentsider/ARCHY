from typing import List, Dict, Any, Optional
from .agent import Agent
import json
import asyncio
import time
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Response(BaseModel):
    agent: Agent
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    optimized: str = ""
    agent_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)

class Swarm:
    def __init__(self, agents: List[Agent]):
        self.agents = {agent.name: agent for agent in agents}
        self.master_agent = self.agents.get("Master Agent")
        if not self.master_agent:
            raise ValueError("Master Agent not found in the list of agents")
        self.current_agent = self.master_agent
        self.max_iterations = 5

    async def analyze_context(self, message: str, epic_context: Optional[str] = None, story_context: Optional[str] = None) -> str:
        context_prompt = f"Analyze the following user story and provide a brief summary of its main intent, focusing on the specific task or goal the user wants to achieve. Consider the epic and story context if provided. Avoid introducing additional processes or requirements not explicitly mentioned:\n\nUser Story: {message}\n\nEpic Context: {epic_context or 'Not provided'}\n\nStory Context: {story_context or 'Not provided'}"
        context_response = self.master_agent.get_completion([{"role": "user", "content": context_prompt}], [])
        return context_response.choices[0].message.content

    async def process_message(self, message: str, context_analysis: str) -> Response:
        start_time = time.time()
        messages = [
            {"role": "system", "content": self.current_agent.instructions},
            {"role": "user", "content": message},
            {"role": "system", "content": f"Context Analysis: {context_analysis}"}
        ]
        agent_interactions = []
        
        iterations = 0
        while iterations < self.max_iterations:
            response = await self.run_full_turn(messages)
            agent_interactions.extend(response.messages)
            messages.extend(response.messages)
            self.current_agent = response.agent

            if self.current_agent == self.master_agent:
                break

            iterations += 1

        final_response = self.generate_final_summary(messages, context_analysis)

        end_time = time.time()
        execution_time = end_time - start_time

        performance_metrics = {
            "execution_time": execution_time,
            "iterations_used": iterations,
            "quality_score": self.assess_quality(final_response)
        }

        return Response(
            agent=self.current_agent,
            messages=messages,
            optimized=final_response,
            agent_interactions=agent_interactions,
            performance_metrics=performance_metrics
        )

    async def run_full_turn(self, messages: List[Dict[str, str]]) -> Response:
        num_init_messages = len(messages)
        messages = messages.copy()

        while True:
            tool_schemas = [self.current_agent.function_to_schema(tool) for tool in self.current_agent.tools]
            tools_map = {tool.__name__: tool for tool in self.current_agent.tools}

            response = self.current_agent.get_completion(messages, tool_schemas)
            message = response.choices[0].message
            messages.append({"role": "assistant", "content": message.content})

            if message.content:
                logger.info(f"{self.current_agent.name}: {message.content}")

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                result = await self.execute_tool_call(tool_call, tools_map)

                if isinstance(result, Agent):
                    self.current_agent = result
                    result = f"Transferred to {self.current_agent.name}. Adopt persona immediately."

                result_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": str(result),
                }
                messages.append(result_message)

        return Response(agent=self.current_agent, messages=messages[num_init_messages:], optimized="", agent_interactions=[], performance_metrics={})

    async def execute_tool_call(self, tool_call, tools_map):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        logger.info(f"{self.current_agent.name}: {name}({args})")

        if name not in tools_map:
            logger.error(f"Tool '{name}' not found in tools_map")
            return f"Error: Tool '{name}' not found"

        result = tools_map[name](**args)
        if asyncio.iscoroutine(result):
            result = await result
        return result

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

    def generate_final_summary(self, messages: List[Dict[str, str]], context_analysis: str) -> str:
        summary_prompt = f"""
        Based on the context analysis: '{context_analysis}' and all the information provided, create a comprehensive and optimized user story. Follow these guidelines:

        1. Start with 'As a user, I want... so that...'. Ensure this reflects the main intent of the original user story.
        2. Improve the content based on your analysis of which insights from all agents (Technical, UX, QA, and Stakeholder Liaison) to take into account
        3. Provide a focused list of acceptance criteria that directly relate to the main intent of the user story.
        4. Ensure each acceptance criterion is specific, measurable, and relevant to the user story.
        5. Do not repeat the user story in the acceptance criteria.
        6. Address key points raised by each specialist while staying true to the original context.
        7. Avoid introducing unrelated processes or requirements.
        8. Do not add unnecessary phrases like 'so that I can complete my task efficiently'.
        9. Ensure the final output is cohesive and well-structured.
        10. Consider the epic context (if provided) to ensure the user story aligns with the broader project goals.

        Format the output as follows:
        As a user, I want [improved action] so that [improved outcome].

        Acceptance Criteria:
        1. [Specific criterion 1]
        2. [Specific criterion 2]
        3. [Specific criterion 3]
        ...

        Ensure at least 3-5 acceptance criteria are provided, covering different aspects of the user story.
        """

        summary_message = [{"role": "user", "content": summary_prompt}]
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                logger.info(f"Generating final summary: Attempt {attempt + 1}")
                summary_response = self.master_agent.get_completion(summary_message + messages, [])
                final_response = summary_response.choices[0].message.content
                
                logger.info(f"Generated response: {final_response[:100]}...")
                
                if self.validate_final_response(final_response):
                    logger.info(f"Successfully generated user story on attempt {attempt + 1}")
                    return final_response
                else:
                    logger.warning(f"Attempt {attempt + 1} failed to generate proper user story format")
                    messages.append({"role": "user", "content": "The previous response did not meet the required format and quality standards. Please try again, ensuring you follow all the guidelines provided."})
            except Exception as e:
                logger.error(f"Error in generate_final_summary attempt {attempt + 1}: {str(e)}")
        
        logger.error("Failed to generate a proper user story after multiple attempts. Returning a basic user story.")
        original_message = messages[0]['content']
        return f"As a user, I want {original_message} so that I can complete my task effectively.\n\nAcceptance Criteria:\n1. The system should provide a clear interface for the user action.\n2. The process should be efficient and user-friendly.\n3. The system should provide clear feedback on the success or failure of the action."

    def validate_final_response(self, response: str) -> bool:
        if not response.startswith("As a user, I want"):
            return False
        if "so that" not in response:
            return False
        if "Acceptance Criteria:" not in response:
            return False
        criteria = response.split("Acceptance Criteria:")[1].strip().split("\n")
        if len(criteria) < 3:
            return False
        if any(criterion.strip().startswith("The system should allow me to As a user,") for criterion in criteria):
            return False
        return True
