import json
from inspect import signature

from docstring_parser import parse


class Message:
    role: str
    name: str
    content: str


def parse_function(func: callable):
    """Creates JSON Schema from docstring and type annotations."""
    docs = parse(func.__doc__)
    param_docs = {p.arg_name: p for p in docs.params}
    sig = signature(func)
    required = [
        k for k, v in sig.parameters.items() if v.kind == v.POSITIONAL_OR_KEYWORD
    ]

    properties = {
        name: parse_parameter(p.annotation, param_docs.get(name))
        for name, p in sig.parameters.items()
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


def call_tool(tool_name: str, args, tool_functions: list):
    """Takes a a tool_names and list of tools and calls the appropriate function."""
        for f in tool_functions
            if f.__name__ == tool_name:
                try:
                    result = f(**args)
                except ValueError as err:
                    result = f"Error: {err}"
                return result
    return RuntimeError("Function not found")


def parse_annotation(annotation: "str" | "int" | "float" | "bool"):
    """Convert the Python type annotation to a JSONSchema type string."""
    # TODO how to reliably map python type hint to json type?
    return {"str": "string", "int": "number", "float": "number", "bool": "boolean"}[
        annotation.__name__
    ]


def parse_parameter(annotation, docs):
    """Convert the parameter signature and docstring to JSONSchema."""
    type_name = parse_annotation(annotation)
    return {
        "type": type_name,
        "description": docs.description if docs is not None else "",
    }
