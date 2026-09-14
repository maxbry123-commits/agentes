import inspect
import re
import json
import hashlib
from typing import (
    Callable,
    Any,
    List,
    Dict,
    Optional,
    Union,
)  # Added more specific types

# --- Type Aliases for Clarity ---
JsonType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
FunctionSchema = Dict[str, Any]  # Type alias for the schema structure
InputListType = List[Any]  # Generic list for split_list input
ChunkedListType = List[List[Any]]  # Generic chunked list for split_list output
DictContent = Dict[str, Any]
ExcludeFields = Optional[List[str]]


def function_to_schema(func: Callable[..., Any]) -> FunctionSchema:
    """
    Converts a Python function into an LLM-compatible tool schema.

    This schema typically follows a format similar to OpenAI's function calling
    schema, detailing the function's name, description (from its docstring),
    and parameters (derived from its signature and type annotations).

    Supported Python types for parameters are mapped to JSON schema types:
    `str` -> "string", `int` -> "integer", `float` -> "number",
    `bool` -> "boolean", `list` -> "array", `dict` -> "object",
    `NoneType` -> "null". Unannotated parameters or parameters with
    unsupported annotations default to "string".

    Parameter descriptions are basic and include type and default value if present.

    :param func: The callable function to convert. It should ideally have type hints
                 for its parameters and a docstring for its description.
    :type func: typing.Callable[..., typing.Any]
    :return: A dictionary representing the tool schema.
    :rtype: FunctionSchema
    :raises ValueError: If the function signature cannot be inspected (e.g., for some built-ins)
                        or if a parameter's type annotation is of a type that
                        cannot be directly mapped and is not a common built-in.
    """
    type_map: Dict[type, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",  # Note: Does not specify item types for the array.
        dict: "object",  # Note: Does not specify properties for the object.
        type(None): "null",  # For NoneType
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:  # e.g., for built-in functions in C
        raise ValueError(
            f"Failed to get signature for function '{func.__name__}': {e}"
        ) from e

    parameters_properties: Dict[str, Dict[str, str]] = {}
    for param in signature.parameters.values():
        # Skip 'self' for methods, and varargs/varkwargs for simplicity in schema
        if (
            param.name == "self"
            and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        ):
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        param_type_annotation = param.annotation
        json_type: str = "string"  # Default type if annotation is missing or unmappable

        # Handle Optional[T] (which is Union[T, NoneType]) and Union[T, None]
        # by extracting the non-NoneType part for the schema type.
        # The 'required' list will handle if the parameter itself is optional.
        if (
            hasattr(param_type_annotation, "__origin__")
            and param_type_annotation.__origin__ is Union
        ):
            # Filter out NoneType for Optional fields
            union_args = [
                arg for arg in param_type_annotation.__args__ if arg is not type(None)
            ]
            if len(union_args) == 1:  # This was Optional[X] or Union[X, None]
                param_type_annotation = union_args[0]
            # else: complex Union, defaults to "string" or requires more sophisticated handling

        if param_type_annotation is not inspect.Parameter.empty:
            json_type = type_map.get(
                param_type_annotation, "string"
            )  # Default to string if type not in map

        # Create a basic description for the parameter
        param_description = f"Parameter '{param.name}'."
        # Adding type information to description can be helpful for LLMs
        if param_type_annotation is not inspect.Parameter.empty:
            param_description += f" Expected type: {getattr(param_type_annotation, '__name__', str(param_type_annotation))}."
        if param.default != inspect.Parameter.empty:
            param_description += f" Default value: {param.default!r}."

        parameters_properties[param.name] = {
            "type": json_type,
            "description": param_description.strip(),
        }

    required: List[str] = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect.Parameter.empty
        and param.name != "self"  # Ensure self is not in required
        and param.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]

    # Use function's docstring for description, default if none.
    func_description = (
        func.__doc__ or f"No description provided for function {func.__name__}."
    ).strip()
    # Take only the first line of the docstring for a concise description, if multi-line.
    # Or process it further if a more detailed description is desired.
    concise_description = func_description.split("\n", 1)[0]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": concise_description,  # Using concise description
            "parameters": {
                "type": "object",
                "properties": parameters_properties,
                "required": sorted(required),  # Sort for consistent schema output
            },
        },
    }


def load_json_from_chat_response(chat_result: str) -> JsonType:
    """
    Extracts and parses JSON data from a chat response string.

    It looks for JSON content enclosed in markdown-style code blocks
    (e.g., ```json ... ```).

    :param chat_result: The string chat response, potentially containing JSON.
    :type chat_result: str
    :return: The parsed JSON data (dictionary or list).
    :rtype: JsonType
    :raises RuntimeError: If no JSON content in the expected format is found.
    :raises json.JSONDecodeError: If the extracted content is not valid JSON.
    """
    # Regex to find JSON content within ```json ... ``` blocks
    # re.DOTALL allows '.' to match newline characters.
    pattern = r"```(?:json)?\s*(.*?)\s*```"  # Made 'json' optional in marker, added optional whitespace
    match = re.search(
        pattern, chat_result, re.DOTALL | re.IGNORECASE
    )  # Added IGNORECASE for 'json' marker

    if match:
        json_data_str: str = match.group(1).strip()
        try:
            return json.loads(json_data_str)
        except json.JSONDecodeError as e:
            # Provide more context in the error message
            raise json.JSONDecodeError(
                f"Failed to parse extracted JSON content: {e.msg}. Extracted string: '{json_data_str[:200]}...'",
                e.doc,
                e.pos,
            ) from e
    else:
        # Fallback: try to parse the whole string if no markdown block is found
        # This is risky but might catch cases where the LLM just returns raw JSON.
        try:
            return json.loads(chat_result)
        except json.JSONDecodeError:
            # If this also fails, then raise the original error.
            raise RuntimeError(
                f"No JSON content found in markdown code blocks, "
                f"and the entire string is not valid JSON. Input: '{chat_result[:200]}...'"
            )


def split_list(input_list: InputListType, chunk_size: int) -> ChunkedListType:
    """
    Splits a list into smaller chunks of a specified maximum size.

    :param input_list: The list to be split.
    :type input_list: typing.List[typing.Any]
    :param chunk_size: The maximum size of each chunk. Must be a positive integer.
    :type chunk_size: int
    :return: A list of lists, where each inner list is a chunk.
    :rtype: typing.List[typing.List[typing.Any]]
    :raises ValueError: If `chunk_size` is not a positive integer.
    """
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if not input_list:  # Handle empty input list
        return []
    return [
        input_list[i : i + chunk_size] for i in range(0, len(input_list), chunk_size)
    ]


def md5(source: str) -> str:
    """
    Computes the MD5 hash of a given string.

    The input string is encoded to UTF-8 before hashing.

    :param source: The string to hash.
    :type source: str
    :return: The hexadecimal MD5 hash string.
    :rtype: str
    """
    if not isinstance(source, str):
        raise TypeError("Input 'source' for md5 must be a string.")
    return hashlib.md5(source.encode("utf-8")).hexdigest()


def dict_md5(dict_content: DictContent, exclude_fields: ExcludeFields = None) -> str:
    """
    Computes the MD5 hash of a dictionary's content.

    The dictionary is first serialized to a JSON string with sorted keys
    (to ensure consistent hashing regardless of initial key order) and
    `ensure_ascii=False` (to handle non-ASCII characters correctly).
    Specified fields can be excluded from the hashing process.

    :param dict_content: The dictionary whose content is to be hashed.
    :type dict_content: typing.Dict[str, typing.Any]
    :param exclude_fields: An optional list of field names (keys) to exclude
                           from the dictionary before generating the hash.
                           Defaults to None (no fields excluded).
    :type exclude_fields: typing.Optional[typing.List[str]]
    :return: The hexadecimal MD5 hash string of the dictionary's content.
    :rtype: str
    """
    if not isinstance(dict_content, dict):
        raise TypeError("Input 'dict_content' for dict_md5 must be a dictionary.")

    # Create a shallow copy to avoid modifying the original dictionary
    dict_to_hash = dict(dict_content)

    if exclude_fields:
        for field in exclude_fields:
            dict_to_hash.pop(field, None)  # Safely remove field if it exists

    # Serialize to JSON with sorted keys and ensure_ascii=False for consistent hashing
    # ensure_ascii=False is important for proper handling of unicode characters.
    try:
        sorted_json_str = json.dumps(dict_to_hash, sort_keys=True, ensure_ascii=False)
    except TypeError as e:
        # This can happen if the dictionary contains non-serializable types
        raise TypeError(f"Dictionary contains non-JSON-serializable data: {e}") from e

    return hashlib.md5(sorted_json_str.encode("utf-8")).hexdigest()
