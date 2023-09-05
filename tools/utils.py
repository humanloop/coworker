import json
from inspect import signature
from pprint import pprint

from docstring_parser import parse


class Message:
    role: str
    name: str
    content: str


def parse_function(func: callable):
    """Creates JSON Schema from docstring and type annotations.

    Args:
        func (callable): The function to parse


    """
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


def call_function(response, *functions):
    """Execute the function"""
    choice = response["choices"][0]
    if choice["finish_reason"] == "function_call":
        func_data = choice["message"]["function_call"]
        try:
            args = json.loads(func_data["arguments"])
        except ValueError as err:
            print("Error parsing arguments for function call")
            print("Function call:", func_data)
            # TODO: raise an error here
            raise ValueError("Error parsing arguments for function call")
        name = func_data["name"]

        # TODO: just find the function rather than the loop
        for f in functions:
            if f.__name__ == name:
                try:
                    result = f(**args)
                except ValueError as err:
                    # TODO: raise an error here
                    result = f"Error: {err}"
                message = {
                    "role": "function",
                    "name": name,
                    "content": json.dumps(result),
                }
                return message

    return RuntimeError("Function not found")


def parse_annotation(annotation: str):
    """Convert the Python type annotation to a JSONSchema type string."""
    # TODO how to reliably map python type hint to json type?
    return {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
        "List": "array",
        "list": "array",
    }[annotation.__name__]


def parse_parameter(annotation, docs):
    """Convert the parameter signature and docstring to JSONSchema."""
    type_name = parse_annotation(annotation)
    return {
        "type": type_name,
        "description": docs.description if docs is not None else "",
    }


if __name__ == "__main__":
    from tools.linear import create_linear_issue, list_linear_teams

    functions = [list_linear_teams, create_linear_issue]
    parsed = parse_function(create_linear_issue)

    pprint(parsed)
