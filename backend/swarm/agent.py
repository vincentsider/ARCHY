from openai import OpenAI
import os
from typing import List, Dict, Any

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Agent:
    def __init__(self, name: str, instructions: str, tools: List[Any], model: str = "gpt-4-0613"):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.model = model

    def get_completion(self, messages: List[Dict[str, str]], tool_schemas: List[Dict[str, Any]]) -> Any:
        messages = [{"role": "system", "content": self.instructions}] + messages

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
        }

        if tool_schemas:
            kwargs["tools"] = tool_schemas
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        return response

    def function_to_schema(self, func):
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
