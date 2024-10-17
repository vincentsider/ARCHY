from openai import OpenAI
import os
from typing import List, Dict, Any, Callable
import inspect
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Agent:
    def __init__(self, name: str, instructions: str, tools: List[Callable], model: str):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.model = model

    def get_completion(self, messages: List[Dict[str, str]], tool_schemas: List[Dict[str, Any]]):
        completion_args = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.instructions},
                *messages
            ],
        }
        
        if tool_schemas:
            completion_args["tools"] = tool_schemas

        return client.chat.completions.create(**completion_args)

    def function_to_schema(self, func: Callable) -> Dict[str, Any]:
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null",
        }

        signature = inspect.signature(func)
        parameters = {}
        for param in signature.parameters.values():
            param_type = type_map.get(param.annotation, "string")
            parameters[param.name] = {"type": param_type}

        required = [
            param.name
            for param in signature.parameters.values()
            if param.default == inspect.Parameter.empty
        ]

        # Ensure the function name is valid
        func_name = re.sub(r'[^a-zA-Z0-9_-]', '_', func.__name__)

        return {
            "type": "function",
            "function": {
                "name": func_name,
                "description": (func.__doc__ or "").strip(),
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required,
                },
            },
        }
