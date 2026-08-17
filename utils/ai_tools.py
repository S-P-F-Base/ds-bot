from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, get_type_hints


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    function: Callable[..., Any]
    inject_context: bool = False  # если True, первым аргументом передаётся контекст


class ToolManager:
    """Собирает инструменты из методов класса, помеченных @tool."""

    def __init__(self, instance: Any = None):
        self.instance = instance
        self.tools: list[Tool] = []
        self._register_tools()

    def _register_tools(self):
        for name, method in inspect.getmembers(
            self.instance, predicate=inspect.ismethod
        ):
            if hasattr(method, "_tool_meta"):
                meta = method._tool_meta  # type: ignore
                params_schema = self._build_params_schema(method, meta)
                tool = Tool(
                    name=meta.get("name", name),
                    description=meta.get("description", method.__doc__ or "").strip(),
                    parameters=params_schema,
                    function=method,
                    inject_context=meta.get("inject_context", False),
                )
                self.tools.append(tool)

    def _build_params_schema(self, method, meta) -> dict:
        hints = get_type_hints(method)
        sig = inspect.signature(method)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "ctx", "context"):
                continue

            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            param_type = hints.get(param_name, str)
            json_type = self._python_type_to_json(param_type)

            param_description = ""
            if method.__doc__:
                doc_lines = method.__doc__.splitlines()
                for line in doc_lines:
                    stripped = line.strip()
                    if stripped.startswith(f":param {param_name}:"):
                        param_description = stripped.split(":", 2)[2].strip()
                        break

            property_schema = {"type": json_type}
            if param_description:
                property_schema["description"] = param_description

            if param.default is not inspect.Parameter.empty:
                property_schema["default"] = param.default

            else:
                required.append(param_name)

            properties[param_name] = property_schema

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    @staticmethod
    def _python_type_to_json(py_type) -> str:
        origin = getattr(py_type, "__origin__", None)
        if origin is list or origin is set:
            return "array"

        if py_type is int:
            return "integer"

        if py_type is float:
            return "number"

        if py_type is bool:
            return "boolean"

        return "string"

    def get_tools_schema(self) -> list[dict]:
        schemas = []
        for tool in self.tools:
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return schemas

    async def execute(
        self, tool_name: str, arguments: dict, context: dict | None = None
    ) -> Any:
        """Выполняет инструмент по имени с переданными аргументами."""
        for tool in self.tools:
            if tool.name == tool_name:
                if tool.inject_context and context is not None:
                    result = tool.function(context, **arguments)

                else:
                    result = tool.function(**arguments)

                if inspect.iscoroutine(result):
                    result = await result

                return result

        raise ValueError(f"Инструмент {tool_name} не найден")


def tool(
    name: str | None = None,
    description: str | None = None,
    inject_context: bool = False,
):
    """Декоратор для пометки метода как инструмента ИИ."""

    def decorator(func):
        func._tool_meta = {
            "name": name or func.__name__,
            "description": description,
            "inject_context": inject_context,
        }
        return func

    return decorator
