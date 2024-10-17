from typing import List, Dict, Any, Tuple
from .agent import Agent
import json
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class Response:
    def __init__(self, agent: Agent, messages: List[Dict[str, Any]], decision: str = ""):
        self.agent = agent
        self.messages = messages
        self.decision = decision

class Swarm:
    def __init__(self, agents: List[Agent]):
        self.agents = {agent.name: agent for agent in agents}
        self.master_agent = self.agents.get("Master Agent")
        if not self.master_agent:
            raise ValueError("Master Agent not found in the list of agents")
        self.current_agent = self.master_agent
        self.max_iterations = 5  # Default value, can be adjusted
        self.early_stopping_threshold = 0.8  # Quality threshold for early stopping

    async def analyze_context(self, message: str) -> str:
        context_prompt = f"Analyze the following user story and provide a brief summary of its main intent, focusing on the specific task or goal the user wants to achieve. Avoid introducing additional processes or requirements not explicitly mentioned:\n\n{message}"
        context_response = self.master_agent.get_completion([{"role": "user", "content": context_prompt}], [])
        return context_response.choices[0].message.content

    async def process_message(self, message: str, tools_map: Dict, context_analysis: str) -> Tuple[str, List[Dict], Dict[str, Any]]:
        start_time = time.time()
        messages = [{"role": "user", "content": message}]
        agent_interactions = []
        final_response = ""
        
        # Add context analysis to messages
        messages.append({"role": "system", "content": f"Context Analysis: {context_analysis}"})
        
        # Consult all agents
        for agent_name in ["Technical Requirements Agent", "User Experience Agent", "Quality Assurance Agent", "Stakeholder Liaison Agent"]:
            agent = self.agents[agent_name]
            response = await self.run_agent(agent, messages + [{"role": "user", "content": f"As the {agent_name}, please provide your specific input for optimizing this user story, focusing only on aspects directly related to the main intent: {context_analysis}"}], tools_map)
            agent_interactions.extend(response.messages)
            messages.extend(response.messages)

        # Generate final summary
        final_response = self.generate_final_summary(messages, context_analysis)

        end_time = time.time()
        execution_time = end_time - start_time

        performance_metrics = {
            "execution_time": execution_time,
            "iterations_used": len(self.agents),
            "quality_score": self.assess_quality(final_response)
        }

        return final_response, agent_interactions, performance_metrics

    async def run_agent(self, agent: Agent, messages: List[Dict[str, str]], tools_map: Dict) -> Response:
        tool_schemas = [agent.function_to_schema(tool) for tool in agent.tools]
        
        response = agent.get_completion(messages, tool_schemas)
        message = response.choices[0].message
        
        new_messages = []
        new_agent = agent
        decision = "No decision recorded"

        if message.content:
            new_messages.append({
                "role": "assistant",
                "content": message.content,
                "agent_name": agent.name,
                "decision": decision,
                "tools_used": []
            })
            logger.info(f"{agent.name}: {message.content}")

        if message.tool_calls:
            for tool_call in message.tool_calls:
                result = await self.execute_tool_call(tool_call, tools_map, agent.name)
                
                if isinstance(result, str) and result.startswith("HANDOFF:"):
                    new_agent_name = result.split(":", 1)[1]
                    decision = f"Transferred to {new_agent_name}"
                    new_messages.append({
                        "role": "system",
                        "content": f"Transferred to {new_agent_name}. Adopt persona immediately.",
                        "agent_name": agent.name,
                        "decision": decision,
                        "tools_used": [tool_call.function.name]
                    })
                    break
                else:
                    new_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call.model_dump()],
                        "agent_name": agent.name,
                        "decision": "Used tool",
                        "tools_used": [tool_call.function.name]
                    })
                    new_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                        "agent_name": agent.name,
                        "decision": "Tool response",
                        "tools_used": []
                    })

        return Response(agent=new_agent, messages=new_messages, decision=decision)

    async def execute_tool_call(self, tool_call, tools_map, agent_name):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        logger.info(f"{agent_name}: {name}({args})")

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
        
        # Count the number of unique aspects covered
        aspects = ['technical', 'ux', 'business', 'quality']
        covered_aspects = sum(1 for aspect in aspects if aspect.lower() in final_response.lower())
        score += covered_aspects * 0.075  # Increased weight for aspect coverage
        
        # Evaluate the detail level
        criteria_count = final_response.count("\n") - 1  # Rough estimate of criteria count
        score += min(criteria_count * 0.025, 0.25)  # Up to 0.25 for detailed criteria
        
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
                summary_response = self.master_agent.get_completion(summary_message + messages, [])  # No tool schemas
                final_response = summary_response.choices[0].message.content
                
                logger.info(f"Generated response: {final_response[:100]}...")  # Log the first 100 characters
                
                if self.validate_final_response(final_response):
                    logger.info(f"Successfully generated user story on attempt {attempt + 1}")
                    return final_response
                else:
                    logger.warning(f"Attempt {attempt + 1} failed to generate proper user story format")
                    messages.append({"role": "user", "content": "The previous response did not meet the required format and quality standards. Please try again, ensuring you follow all the guidelines provided."})
            except Exception as e:
                logger.error(f"Error in generate_final_summary attempt {attempt + 1}: {str(e)}")
        
        # If we still don't have a proper user story, return a basic one based on the original message
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

    def update_max_iterations(self, new_max_iterations: int):
        self.max_iterations = new_max_iterations

    def update_early_stopping_threshold(self, new_threshold: float):
        if 0 <= new_threshold <= 1:
            self.early_stopping_threshold = new_threshold
        else:
            raise ValueError("Early stopping threshold must be between 0 and 1")
