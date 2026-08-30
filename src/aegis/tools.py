from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolCategory(StrEnum):
    """Categories of tools available to agents."""
    DATA_ACCESS = "data_access"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    EVIDENCE_RETRIEVAL = "evidence_retrieval"
    CLINICAL_REASONING = "clinical_reasoning"
    VISUALIZATION = "visualization"
    EXTERNAL = "external"


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


@dataclass
class ToolDefinition:
    """Definition of a tool that agents can use."""
    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter]
    returns: str
    examples: list[dict[str, Any]] = field(default_factory=list)
    requires_auth: bool = False
    cache_ttl: int = 0  # seconds, 0 = no cache


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class ToolRegistry:
    """Registry for managing tools available to agents."""

    def __init__(self):
        self._tools: dict[str, tuple[ToolDefinition, Callable]] = {}
        self._cache: dict[str, tuple[Any, float]] = {}

    def register(
        self,
        definition: ToolDefinition,
        handler: Callable,
    ) -> None:
        """Register a tool with its definition and handler."""
        self._tools[definition.name] = (definition, handler)

    def tool(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        returns: str = "Any",
        parameters: list[ToolParameter] | None = None,
        examples: list[dict[str, Any]] | None = None,
    ):
        """Decorator to register a function as a tool."""
        def decorator(func: Callable) -> Callable:
            # Auto-generate parameters from function signature
            if parameters is None:
                sig = inspect.signature(func)
                tool_params = []
                for param_name, param in sig.parameters.items():
                    if param_name in ('self', 'cls'):
                        continue
                    param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
                    required = param.default == inspect.Parameter.empty
                    default = param.default if param.default != inspect.Parameter.empty else None
                    tool_params.append(ToolParameter(
                        name=param_name,
                        type=param_type,
                        description=f"Parameter: {param_name}",
                        required=required,
                        default=default,
                    ))
            else:
                tool_params = parameters

            definition = ToolDefinition(
                name=name,
                description=description,
                category=category,
                parameters=tool_params,
                returns=returns,
                examples=examples or [],
            )

            self._tools[name] = (definition, func)
            return func
        return decorator

    def get_definition(self, name: str) -> ToolDefinition | None:
        """Get the definition of a tool."""
        if name in self._tools:
            return self._tools[name][0]
        return None

    def get_definitions_by_category(self, category: ToolCategory) -> list[ToolDefinition]:
        """Get all tool definitions in a category."""
        return [
            definition
            for definition, _ in self._tools.values()
            if definition.category == category
        ]

    def get_all_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions."""
        return [definition for definition, _ in self._tools.values()]

    def get_tools_for_prompt(self, categories: list[ToolCategory] | None = None) -> str:
        """Generate a formatted string of tools for LLM prompts."""
        tools = self.get_all_definitions()
        if categories:
            tools = [t for t in tools if t.category in categories]

        parts = []
        for tool in tools:
            params = []
            for p in tool.parameters:
                req = "required" if p.required else f"optional, default={p.default}"
                params.append(f"  - {p.name} ({p.type}, {req}): {p.description}")

            part = f"""## {tool.name}
Category: {tool.category.value}
Description: {tool.description}
Parameters:
{chr(10).join(params) if params else "  None"}
Returns: {tool.returns}"""

            if tool.examples:
                part += "\nExamples:"
                for ex in tool.examples[:2]:
                    part += f"\n  Input: {ex.get('input', {})}"
                    part += f"\n  Output: {ex.get('output', 'N/A')}"

            parts.append(part)

        return "\n\n".join(parts)

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        import time

        if name not in self._tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found",
            )

        definition, handler = self._tools[name]

        # Check cache
        cache_key = f"{name}:{str(sorted(kwargs.items()))}"
        if definition.cache_ttl > 0 and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < definition.cache_ttl:
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={"cached": True},
                )

        # Execute
        start = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(handler):
                result = await handler(**kwargs)
            else:
                result = handler(**kwargs)

            duration_ms = (time.perf_counter() - start) * 1000

            # Cache result
            if definition.cache_ttl > 0:
                self._cache[cache_key] = (result, time.time())

            return ToolResult(
                success=True,
                data=result,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                duration_ms=duration_ms,
            )

    def execute_sync(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool synchronously."""
        import time

        if name not in self._tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found",
            )

        definition, handler = self._tools[name]

        # Check cache
        cache_key = f"{name}:{str(sorted(kwargs.items()))}"
        if definition.cache_ttl > 0 and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < definition.cache_ttl:
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={"cached": True},
                )

        # Execute
        start = time.perf_counter()
        try:
            result = handler(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Cache result
            if definition.cache_ttl > 0:
                self._cache[cache_key] = (result, time.time())

            return ToolResult(
                success=True,
                data=result,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                duration_ms=duration_ms,
            )

    def clear_cache(self) -> None:
        """Clear the tool result cache."""
        self._cache.clear()


# Global tool registry
tool_registry = ToolRegistry()
