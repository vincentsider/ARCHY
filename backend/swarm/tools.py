import inspect
from typing import Callable, Dict, Any

def function_to_schema(func: Callable) -> Dict[str, Any]:
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
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
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

def look_up_item(search_query: str) -> str:
    """Use to find item ID. Search query can be a description or keywords."""
    # Simulating a database lookup
    return f"item_id_for_{search_query.replace(' ', '_')}"

def execute_refund(item_id: str, reason: str = "not provided") -> str:
    """Execute a refund for the given item ID."""
    # Simulating a refund process
    return f"Refund executed for item {item_id}. Reason: {reason}"

def transfer_to_technical_requirements():
    """Transfer to the Technical Requirements Agent."""
    return "HANDOFF:Technical Requirements Agent"

def transfer_to_ux():
    """Transfer to the User Experience Agent."""
    return "HANDOFF:User Experience Agent"

def transfer_to_qa():
    """Transfer to the Quality Assurance Agent."""
    return "HANDOFF:Quality Assurance Agent"

def transfer_to_stakeholder_liaison():
    """Transfer to the Stakeholder Liaison Agent."""
    return "HANDOFF:Stakeholder Liaison Agent"

def transfer_to_master():
    """Transfer to the Master Agent."""
    return "HANDOFF:Master Agent"
