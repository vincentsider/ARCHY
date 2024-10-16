from typing import List, Dict, Any, Tuple, Optional
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

    async def process_message(self, message: str, tools_map: Dict) -> Tuple[str, List[Dict], Dict[str, Any]]:
        start_time = time.time()
        messages = [{"role": "user", "content": message}]
        agent_interactions = []
        final_response = ""
        
        # Consult all agents
        for agent_name in ["Master Agent", "Technical Requirements Agent", "User Experience Agent", "Quality Assurance Agent", "Stakeholder Liaison Agent"]:
            agent = self.agents[agent_name]
            response = await self.run_agent(agent, messages + [{"role": "user", "content": f"As the {agent_name}, please provide your specific input for optimizing this user story."}], tools_map)
            agent_interactions.extend(response.messages)
            messages.extend(response.messages)

        # Generate final summary
        final_response = await self.generate_final_summary(messages)

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

    async def generate_final_summary(self, messages: List[Dict[str, str]]) -> str:
        summary_message = [{"role": "user", "content": "As the Master Agent, synthesize all the information provided into a final, optimized user story. Start with 'As a user, I want... so that...'. Then, provide a comprehensive list of acceptance criteria that cover technical, UX, business, and quality assurance aspects. Ensure the final output is cohesive, incorporates insights from all agents, and addresses key points raised by each specialist. This is the final output, so make it complete and ready for implementation."}]
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                logger.info(f"Generating final summary: Attempt {attempt + 1}")
                summary_response = self.master_agent.get_completion(summary_message + messages, [])  # No tool schemas
                final_response = summary_response.choices[0].message.content
                
                logger.info(f"Generated response: {final_response[:100]}...")  # Log the first 100 characters
                
                if final_response.startswith("As a user, I want") and "Acceptance Criteria:" in final_response:
                    logger.info(f"Successfully generated user story on attempt {attempt + 1}")
                    return final_response
                else:
                    logger.warning(f"Attempt {attempt + 1} failed to generate proper user story format")
                    messages.append({"role": "user", "content": "The previous response was not in the correct format. Please try again to synthesize the information into a proper user story format, starting with 'As a user, I want...', followed by comprehensive acceptance criteria. Ensure you address technical, UX, business, and quality assurance aspects."})
            except Exception as e:
                logger.error(f"Error in generate_final_summary attempt {attempt + 1}: {str(e)}")
        
        # If we still don't have a proper user story, return a basic one based on the original message
        logger.error("Failed to generate a proper user story after multiple attempts. Returning a basic user story.")
        original_message = messages[0]['content']
        return f"As a user, I want {original_message} so that I can complete my task efficiently.\n\nAcceptance Criteria:\n1. The system should allow me to {original_message}.\n2. The process should be user-friendly and intuitive.\n3. The system should provide feedback on the success or failure of the action."

    def update_max_iterations(self, new_max_iterations: int):
        self.max_iterations = new_max_iterations

    def update_early_stopping_threshold(self, new_threshold: float):
        if 0 <= new_threshold <= 1:
            self.early_stopping_threshold = new_threshold
        else:
            raise ValueError("Early stopping threshold must be between 0 and 1")
