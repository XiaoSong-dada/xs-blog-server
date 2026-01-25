from typing import Any ,Optional
def is_none(value: Any) -> bool:
    """
    Checks if the given value is None.

    Args:
        value: The value to be checked.

    Returns:
        bool: True if value is None, otherwise False.
    """
    return value is None

def is_empty_string(value: str) -> bool:
    """
    Checks if the given string is empty or contains only whitespace.

    Args:
        value: The string to be checked.

    Returns:
        bool: True if value is empty or contains only whitespace, otherwise False.
    """
    return not value.strip()

def is_of_type(value: Any, expected_type: type) -> bool:
    """
    Checks if the given value is of the expected type.

    Args:
        value: The value to be checked.
        expected_type: The expected type.

    Returns:
        bool: True if value is of the expected type, otherwise False.
    """
    return isinstance(value, expected_type)


def is_null_or_empty(value: Optional[str]) -> bool:
    return value is None or value.strip() == ""
