from openai import OpenAI
import os
from typing import List, Dict, Any, Callable
import logging
import json
import inspect

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name: str, api_key: str, model: str = "gpt-4o", instructions: str = "", tools: List[Callable] = None):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.tools = tools or []
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Agent {name} initialized with model {model}")

    async def get_completion(self, messages: List[Dict[str, str]], tool_schemas: List[Dict[str, Any]]) -> Any:
        logger.info(f"Agent {self.name}: Getting completion")

        # Add the instructions as the first system message if not already present
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": self.instructions})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }

        if tool_schemas:
            kwargs["tools"] = tool_schemas
            kwargs["tool_choice"] = "auto"

        try:
            logger.debug(f"Agent {self.name}: Sending request to OpenAI API")
            response = self.client.chat.completions.create(**kwargs)
            logger.info(f"Agent {self.name}: Received response from OpenAI API")
            return response
        except Exception as e:
            logger.error(f"Agent {self.name}: Error in get_completion: {str(e)}")
            raise

    def function_to_schema(self, func: Callable) -> Dict[str, Any]:
        logger.debug(f"Agent {self.name}: Converting function to schema: {func.__name__}")
        
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }

        try:
            signature = inspect.signature(func)
        except ValueError as e:
            raise ValueError(f"Failed to get signature for function {func.__name__}: {str(e)}")

        parameters = {}
        for param in signature.parameters.values():
            try:
                param_type = type_map.get(param.annotation, "string")
            except KeyError as e:
                raise KeyError(f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}")
            parameters[param.name] = {"type": param_type}

        required = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect._empty
        ]

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": (func.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }

    async def request_consultation(self, question: str, target_agent: 'Agent') -> str:
        logger.info(f"Agent {self.name}: Requesting consultation from {target_agent.name}")
        consultation_prompt = f"As {self.name}, I need your input on the following: {question}"
        try:
            consultation_response = await target_agent.get_completion([{"role": "user", "content": consultation_prompt}], [])
            logger.info(f"Agent {self.name}: Received consultation response from {target_agent.name}")
            return consultation_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Agent {self.name}: Error in request_consultation: {str(e)}")
            raise

    async def provide_clarification(self, question: str) -> str:
        logger.info(f"Agent {self.name}: Providing clarification")
        clarification_prompt = f"Please provide clarification on the following: {question}"
        try:
            clarification_response = await self.get_completion([{"role": "user", "content": clarification_prompt}], [])
            logger.info(f"Agent {self.name}: Clarification provided")
            return clarification_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Agent {self.name}: Error in provide_clarification: {str(e)}")
            raise

    async def process_tool_calls(self, message, tools_map: Dict[str, Any], swarm: Any):
        logger.info(f"Agent {self.name}: Processing tool calls")
        new_messages = []
        for tool_call in message.tool_calls:
            if tool_call.function.name.startswith("request_consultation_"):
                logger.info(f"Agent {self.name}: Requesting consultation")
                target_agent_name = tool_call.function.name.split("_")[-1]
                question = json.loads(tool_call.function.arguments)["question"]
                consultation_result = await self.request_consultation(question, swarm.agents[target_agent_name])
                new_messages.append({
                    "role": "function",
                    "name": tool_call.function.name,
                    "content": consultation_result
                })
            else:
                logger.info(f"Agent {self.name}: Executing tool call {tool_call.function.name}")
                result = await swarm.execute_tool_call(tool_call, tools_map, self.name)
                new_messages.append({
                    "role": "function",
                    "name": tool_call.function.name,
                    "content": str(result)
                })
        logger.info(f"Agent {self.name}: Finished processing tool calls")
        return new_messages

    async def run(self, messages: List[Dict[str, str]], tools_map: Dict[str, Any], swarm: Any) -> Dict[str, Any]:
        logger.info(f"Agent {self.name}: Starting run")
        tool_schemas = [self.function_to_schema(tool) for tool in self.tools]
        try:
            response = await self.get_completion(messages, tool_schemas)
            message = response.choices[0].message

            new_messages = []
            if message.content:
                new_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "agent_name": self.name,
                    "decision": "No decision recorded",
                    "tools_used": []
                })

            if message.tool_calls:
                tool_messages = await self.process_tool_calls(message, tools_map, swarm)
                new_messages.extend(tool_messages)

            logger.info(f"Agent {self.name}: Finished run")
            return {
                "agent": self,
                "messages": new_messages,
                "decision": "No decision recorded"
            }
        except Exception as e:
            logger.error(f"Agent {self.name}: Error in run: {str(e)}")
            raise
