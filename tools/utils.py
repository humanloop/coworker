from inspect import signature
from pprint import pprint
from typing import Callable, List

from docstring_parser import parse


class Message:
    role: str
    name: str
    content: str


def parse_function(func: Callable):
    """Creates JSON Schema from docstring and type annotations.

    Args:
        func (Callable): The function to parse
    """
    docs = parse(func.__doc__)
    param_docs = {p.arg_name: p for p in docs.params}
    sig = signature(func)
    # Drop any parameters that are private (with leading `_`)
    parameters = {k: v for k, v in sig.parameters.items() if not k.startswith("_")}

    required = [k for k, v in parameters.items() if v.kind == v.POSITIONAL_OR_KEYWORD]

    properties = {
        name: parse_parameter(p.annotation, param_docs.get(name))
        for name, p in parameters.items()
        if not name.startswith("_")
    }
    descriptor = {
        "name": func.__name__,
        "description": docs.short_description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }
    return descriptor


def parse_parameter(annotation, docs):
    """Convert the parameter signature and docstring to JSONSchema."""
    type_name = convert_type(annotation.__name__)
    return {
        "type": type_name,
        "description": docs.description if docs is not None else "",
    }


def convert_type(annotation_type: str):
    """Convert the Python type annotation to a JSONSchema type string."""
    # TODO how to reliably map python type hint to json type?
    return {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "List": "array",
        "list": "array",
    }[annotation_type]


def call_tool(tool_name: str, args: dict, tools: List[Callable], say: Callable):
    """Takes a a tool_names and list of tools and calls the appropriate function."""
    for tool in tools:
        if tool.__name__ == tool_name:
            try:
                # If the tool has a say argument, pass the say function to it
                if "_say" in signature(tool).parameters:
                    result = tool(**args, _say=say)
                else:
                    result = tool(**args)

            except ValueError as err:
                result = f"Error: {err}"
            return result
    return RuntimeError("Function not found")


if __name__ == "__main__":
    from tools.linear import create_linear_issue, list_linear_teams

    functions = [list_linear_teams, create_linear_issue]
    parsed = parse_function(create_linear_issue)
    pprint(parsed)
