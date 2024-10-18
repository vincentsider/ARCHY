from typing import List, Dict, Any, Tuple
from .agent import Agent
import json
import asyncio
import time
import logging
import re

logger = logging.getLogger(__name__)

class Response:
    def __init__(self, agent: Agent, messages: List[Dict[str, Any]], decision: str = ""):
        self.agent = agent
        self.messages = messages
        self.decision = decision

class Swarm:
    def __init__(self, agents: List[Agent], config: Any):
        self.agents = {agent.name: agent for agent in agents}
        self.master_agent = self.agents.get("Master Agent")
        if not self.master_agent:
            raise ValueError("Master Agent not found in the list of agents")
        self.current_agent = self.master_agent
        self.max_iterations = 5  # Default value, can be adjusted
        self.early_stopping_threshold = 0.8  # Quality threshold for early stopping
        self.config = config
        logger.info(f"Swarm initialized with {len(agents)} agents")

    async def analyze_context(self, message: str) -> str:
        logger.info("Starting context analysis")
        context_prompt = f"Analyze the following user story and provide a brief summary of its main intent, focusing on the specific task or goal the user wants to achieve. Avoid introducing additional processes or requirements not explicitly mentioned:\n\n{message}"
        try:
            context_response = await self.master_agent.get_completion([{"role": "user", "content": context_prompt}], [])
            logger.info("Context analysis completed successfully")
            return context_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in context analysis: {str(e)}")
            raise

    async def triage_user_story(self, user_story: str, context_analysis: str) -> List[str]:
        logger.info("Starting user story triage")
        triage_prompt = f"Based on the following user story and context analysis, determine which specialist agents (Technical Requirements, User Experience, Quality Assurance, Stakeholder Liaison, Pega Specialist) are most relevant. Return a comma-separated list of the most relevant agent names:\n\nUser Story: {user_story}\n\nContext Analysis: {context_analysis}"
        try:
            triage_response = await self.master_agent.get_completion([{"role": "user", "content": triage_prompt}], [])
            relevant_agents = triage_response.choices[0].message.content.split(", ")
            logger.info(f"Triage completed. Relevant agents: {relevant_agents}")
            return [agent.strip() for agent in relevant_agents if agent.strip() in self.agents]
        except Exception as e:
            logger.error(f"Error in user story triage: {str(e)}")
            raise

    async def process_message(self, message: str, tools_map: Dict, context_analysis: str) -> Tuple[str, List[Dict], Dict[str, Any]]:
        logger.info("Starting message processing")
        start_time = time.time()
        messages = [{"role": "user", "content": message}]
        agent_interactions = []
        
        messages.append({"role": "system", "content": f"Context Analysis: {context_analysis}"})
        
        try:
            relevant_agents = await self.triage_user_story(message, context_analysis)
            
            logger.info("Swarm Workflow: Starting agent collaboration")
            for agent_name in relevant_agents:
                logger.info(f"Swarm Workflow: Processing with agent: {agent_name}")
                agent = self.agents[agent_name]
                response = await self.run_agent(agent, messages + [{"role": "user", "content": f"As the {agent_name}, please provide your specific input for optimizing this user story, focusing only on aspects directly related to the main intent: {context_analysis}"}], tools_map)
                agent_interactions.extend(response.messages)
                messages.extend(response.messages)
                logger.info(f"Swarm Workflow: {agent_name} completed processing")

            logger.info("Swarm Workflow: Starting feedback loop")
            max_clarification_rounds = self.config.max_clarification_rounds
            for round in range(max_clarification_rounds):
                logger.info(f"Swarm Workflow: Feedback loop round {round + 1}")
                final_response = await self.generate_final_summary(messages, context_analysis)
                quality_score = self.assess_quality(final_response)
                
                if quality_score >= self.config.quality_threshold:
                    logger.info(f"Swarm Workflow: Quality threshold met. Score: {quality_score}")
                    break
                
                clarification_needed = await self.master_agent.get_completion([
                    {"role": "user", "content": f"Analyze this response and determine if any clarification is needed from specialists:\n\n{final_response}"}
                ], [])
                
                if "No clarification needed" in clarification_needed.choices[0].message.content:
                    logger.info("Swarm Workflow: No further clarification needed")
                    break
                
                logger.info("Swarm Workflow: Requesting clarifications from agents")
                for agent_name in relevant_agents:
                    agent = self.agents[agent_name]
                    clarification = await self.request_clarification(agent, clarification_needed.choices[0].message.content)
                    messages.append({"role": "assistant", "content": clarification, "name": agent_name})
                    logger.info(f"Swarm Workflow: Received clarification from {agent_name}")

            end_time = time.time()
            execution_time = end_time - start_time

            performance_metrics = {
                "execution_time": execution_time,
                "iterations_used": len(relevant_agents),
                "quality_score": self.assess_quality(final_response)
            }

            logger.info(f"Swarm Workflow: Message processing completed. Execution time: {execution_time:.2f}s")
            return final_response, agent_interactions, performance_metrics
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            raise

    async def run_agent(self, agent: Agent, messages: List[Dict[str, str]], tools_map: Dict) -> Response:
        logger.info(f"Swarm Workflow: Running agent: {agent.name}")
        tool_schemas = [agent.function_to_schema(tool) for tool in agent.tools]
        
        try:
            response = await agent.get_completion(messages, tool_schemas)
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
                logger.info(f"Swarm Workflow: {agent.name} response: {message.content[:100]}...")

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
                        logger.info(f"Swarm Workflow: Handoff from {agent.name} to {new_agent_name}")
                        break
                    elif isinstance(result, str) and result.startswith("CONSULTATION:"):
                        consultation_result = await self.handle_consultation(result, agent, tools_map)
                        new_messages.extend(consultation_result)
                        logger.info(f"Swarm Workflow: Consultation requested by {agent.name}")
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
                        logger.info(f"Swarm Workflow: {agent.name} used tool: {tool_call.function.name}")

            return Response(agent=new_agent, messages=new_messages, decision=decision)
        except Exception as e:
            logger.error(f"Error in run_agent for {agent.name}: {str(e)}")
            raise

    async def execute_tool_call(self, tool_call, tools_map, agent_name):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        logger.info(f"Swarm Workflow: {agent_name} executing tool: {name}({args})")

        try:
            result = tools_map[name](**args)
            if asyncio.iscoroutine(result):
                result = await result
            logger.info(f"Swarm Workflow: Tool execution completed: {name}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            raise

    async def handle_consultation(self, consultation_request: str, requesting_agent: Agent, tools_map: Dict) -> List[Dict[str, Any]]:
        _, target_agent_name, question = consultation_request.split(":", 2)
        target_agent = self.agents[target_agent_name.strip()]
        
        logger.info(f"Swarm Workflow: Handling consultation: {requesting_agent.name} -> {target_agent_name}")
        
        consultation_messages = [
            {"role": "system", "content": f"You are assisting the {requesting_agent.name} with a question."},
            {"role": "user", "content": question.strip()}
        ]
        
        try:
            consultation_response = await self.run_agent(target_agent, consultation_messages, tools_map)
            logger.info("Swarm Workflow: Consultation completed successfully")
            return [
                {
                    "role": "assistant",
                    "content": f"Consultation request from {requesting_agent.name} to {target_agent_name}:\n{question.strip()}",
                    "agent_name": requesting_agent.name,
                    "decision": "Requested consultation",
                    "tools_used": []
                },
                *consultation_response.messages
            ]
        except Exception as e:
            logger.error(f"Error in handle_consultation: {str(e)}")
            raise

    async def request_clarification(self, agent: Agent, question: str) -> str:
        logger.info(f"Swarm Workflow: Requesting clarification from {agent.name}")
        clarification_prompt = f"Please provide clarification on the following: {question}"
        try:
            clarification_response = await agent.get_completion([{"role": "user", "content": clarification_prompt}], [])
            logger.info(f"Swarm Workflow: Clarification received from {agent.name}")
            return clarification_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in request_clarification from {agent.name}: {str(e)}")
            raise

    def assess_quality(self, final_response: str) -> float:
        logger.info("Swarm Workflow: Assessing quality of final response")
        score = 0.0
        
        # Check for correct format
        if final_response.startswith("As a user, I want"):
            score += 0.2
        if "so that" in final_response:
            score += 0.2
        if "Acceptance Criteria:" in final_response:
            score += 0.2
        
        # Check for comprehensive acceptance criteria
        criteria = final_response.split("Acceptance Criteria:")[1].strip().split("\n") if "Acceptance Criteria:" in final_response else []
        criteria_count = len(criteria)
        if 3 <= criteria_count <= 5:
            score += 0.2
        elif criteria_count > 5:
            score += 0.1
        
        # Check for specificity in criteria
        specific_criteria = sum(1 for c in criteria if any(keyword in c.lower() for keyword in ['must', 'should', 'will', 'can']))
        score += min(specific_criteria * 0.05, 0.2)
        
        # Check for coverage of different aspects
        aspects = ['technical', 'ux', 'business', 'quality', 'pega']
        covered_aspects = sum(1 for aspect in aspects if aspect.lower() in final_response.lower())
        score += covered_aspects * 0.04
        
        final_score = min(score, 1.0)
        logger.info(f"Swarm Workflow: Quality assessment completed. Score: {final_score:.2f}")
        return final_score

    async def generate_final_summary(self, messages: List[Dict[str, str]], context_analysis: str) -> str:
        logger.info("Swarm Workflow: Generating final summary")
        summary_prompt = f"""
        Based on the context analysis: '{context_analysis}' and all the information provided, create a comprehensive and optimized user story. Follow these guidelines strictly:

        1. Start with EXACTLY 'As a user, I want... so that...'. Ensure this reflects the main intent of the original user story.
        2. Improve the content based on your analysis of which insights from all agents (Technical, UX, QA, Stakeholder Liaison, and Pega Specialist) to take into account
        3. Provide a focused list of acceptance criteria that directly relate to the main intent of the user story.
        4. Ensure each acceptance criterion is specific, measurable, and relevant to the user story.
        5. Do not repeat the user story in the acceptance criteria.
        6. Address key points raised by each specialist while staying true to the original context.
        7. Avoid introducing unrelated processes or requirements.
        8. Do not add unnecessary phrases like 'so that I can complete my task efficiently'.
        9. Ensure the final output is cohesive and well-structured.
        10. Include Pega-specific considerations in the acceptance criteria where relevant.

        Format the output EXACTLY as follows:
        As a user, I want [improved action] so that [improved outcome].

        Acceptance Criteria:
        1. [Specific criterion 1]
        2. [Specific criterion 2]
        3. [Specific criterion 3]
        ...

        Provide EXACTLY 3-5 acceptance criteria, covering different aspects of the user story.

        IMPORTANT: Your response should ONLY contain the user story and acceptance criteria in the format specified above. Do not include any additional text, explanations, or comments.
        """

        summary_message = [{"role": "user", "content": summary_prompt}]
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                logger.info(f"Swarm Workflow: Generating final summary: Attempt {attempt + 1}")
                summary_response = await self.master_agent.get_completion(summary_message + messages, [])
                final_response = summary_response.choices[0].message.content
                
                logger.info(f"Swarm Workflow: Generated response: {final_response[:100]}...")
                
                if self.validate_final_response(final_response):
                    logger.info(f"Swarm Workflow: Successfully generated user story on attempt {attempt + 1}")
                    return final_response
                else:
                    logger.warning(f"Swarm Workflow: Attempt {attempt + 1} failed to generate proper user story format")
                    messages.append({"role": "user", "content": "The previous response did not meet the required format and quality standards. Please try again, ensuring you follow all the guidelines provided, especially starting with EXACTLY 'As a user, I want...' and including EXACTLY 3-5 acceptance criteria. Do not include any additional text or explanations."})
            except Exception as e:
                logger.error(f"Error in generate_final_summary attempt {attempt + 1}: {str(e)}")
        
        logger.error("Swarm Workflow: Failed to generate a proper user story after multiple attempts. Returning a basic user story.")
        original_message = messages[0]['content']
        return f"As a user, I want {original_message} so that I can complete my task effectively.\n\nAcceptance Criteria:\n1. The system should provide a clear interface for the user action.\n2. The process should be efficient and user-friendly.\n3. The system should provide clear feedback on the success or failure of the action."

    def validate_final_response(self, response: str) -> bool:
        logger.info("Swarm Workflow: Validating final response")
        
        # Check if the response starts with exactly "As a user, I want"
        if not re.match(r'^As a user, I want', response):
            logger.warning("Swarm Workflow: Final response does not start with exactly 'As a user, I want'")
            return False
        
        # Check for "so that" in the user story
        if "so that" not in response.split("\n")[0]:
            logger.warning("Swarm Workflow: First line does not contain 'so that'")
            return False
        
        # Check for "Acceptance Criteria:" header
        if "Acceptance Criteria:" not in response:
            logger.warning("Swarm Workflow: Final response does not contain 'Acceptance Criteria:'")
            return False
        
        # Split the response into user story and acceptance criteria
        user_story, criteria_section = response.split("Acceptance Criteria:", 1)
        
        # Check the number of acceptance criteria
        criteria = criteria_section.strip().split("\n")
        if not (3 <= len(criteria) <= 5):
            logger.warning(f"Swarm Workflow: Final response has {len(criteria)} acceptance criteria, expected 3-5")
            return False
        
        # Check if each criterion is numbered and not empty
        for i, criterion in enumerate(criteria, 1):
            if not re.match(rf'^{i}\.\s+\S', criterion):
                logger.warning(f"Swarm Workflow: Acceptance criterion {i} is not properly formatted or is empty")
                return False
        
        logger.info("Swarm Workflow: Final response validation successful")
        return True

    def update_max_iterations(self, new_max_iterations: int):
        logger.info(f"Swarm Workflow: Updating max iterations to {new_max_iterations}")
        self.max_iterations = new_max_iterations

    def update_early_stopping_threshold(self, new_threshold: float):
        if 0 <= new_threshold <= 1:
            logger.info(f"Swarm Workflow: Updating early stopping threshold to {new_threshold}")
            self.early_stopping_threshold = new_threshold
        else:
            logger.error(f"Invalid early stopping threshold: {new_threshold}")
            raise ValueError("Early stopping threshold must be between 0 and 1")

    def get_max_iterations(self) -> int:
        return self.max_iterations
