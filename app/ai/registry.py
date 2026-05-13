from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

@dataclass
class FunctionDef:
    name: str
    description: str
    parameters: dict[str, Any]
    required_permission: str
    handler: Callable[..., Coroutine[Any, Any, str]]

_registry: dict[str, FunctionDef] = {}


def register(
    name: str,
    description: str,
    parameters: dict[str, Any],
    required_permission: str,
    handler: Callable[..., Coroutine[Any, Any, str]],
) -> None:
    _registry[name] = FunctionDef(
        name=name,
        description=description,
        parameters=parameters,
        required_permission=required_permission,
        handler=handler,
    )


def get_function(name: str) -> FunctionDef | None:
    return _registry.get(name)


def list_functions() -> list[FunctionDef]:
    return list(_registry.values())


def list_function_names_for_user(is_admin: bool) -> list[str]:
    names: list[str] = []
    for fn in _registry.values():
        if fn.required_permission == "require_login":
            names.append(fn.name)
        elif fn.required_permission == "require_admin" and is_admin:
            names.append(fn.name)
    return names
