
import pytest

from aegis.tools import (
    ToolCategory,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    ToolResult,
)


@pytest.fixture
def registry():
    """Create a fresh tool registry for each test."""
    return ToolRegistry()


@pytest.fixture
def sample_tool_definition():
    """Create a sample tool definition."""
    return ToolDefinition(
        name="test_tool",
        description="A test tool",
        category=ToolCategory.DATA_ACCESS,
        parameters=[
            ToolParameter(
                name="param1",
                type="str",
                description="First parameter",
                required=True,
            ),
            ToolParameter(
                name="param2",
                type="int",
                description="Second parameter",
                required=False,
                default=42,
            ),
        ],
        returns="dict",
        examples=[
            {"input": {"param1": "test"}, "output": {"result": "ok"}},
        ],
    )


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self, registry, sample_tool_definition):
        """Test registering a tool."""
        def handler(param1, param2=42):
            return {"result": param1}
        registry.register(sample_tool_definition, handler)

        assert "test_tool" in registry._tools
        defn, _ = registry._tools["test_tool"]
        assert defn.name == "test_tool"
        assert defn.description == "A test tool"

    def test_get_definition(self, registry, sample_tool_definition):
        """Test getting a tool definition."""
        def handler(param1, param2=42):
            return {"result": param1}
        registry.register(sample_tool_definition, handler)

        defn = registry.get_definition("test_tool")
        assert defn is not None
        assert defn.name == "test_tool"

    def test_get_definition_not_found(self, registry):
        """Test getting a non-existent tool definition."""
        defn = registry.get_definition("nonexistent")
        assert defn is None

    def test_get_definitions_by_category(self, registry, sample_tool_definition):
        """Test getting tool definitions by category."""
        def handler(param1, param2=42):
            return {"result": param1}
        registry.register(sample_tool_definition, handler)

        # Add another tool in a different category
        other_def = ToolDefinition(
            name="other_tool",
            description="Another tool",
            category=ToolCategory.CLINICAL_REASONING,
            parameters=[],
            returns="str",
        )
        registry.register(other_def, lambda: "result")

        # Get tools by category
        data_tools = registry.get_definitions_by_category(ToolCategory.DATA_ACCESS)
        assert len(data_tools) == 1
        assert data_tools[0].name == "test_tool"

        clinical_tools = registry.get_definitions_by_category(ToolCategory.CLINICAL_REASONING)
        assert len(clinical_tools) == 1
        assert clinical_tools[0].name == "other_tool"

    def test_get_all_definitions(self, registry, sample_tool_definition):
        """Test getting all tool definitions."""
        def handler(param1, param2=42):
            return {"result": param1}
        registry.register(sample_tool_definition, handler)

        other_def = ToolDefinition(
            name="other_tool",
            description="Another tool",
            category=ToolCategory.CLINICAL_REASONING,
            parameters=[],
            returns="str",
        )
        registry.register(other_def, lambda: "result")

        all_defs = registry.get_all_definitions()
        assert len(all_defs) == 2

    def test_get_tools_for_prompt(self, registry, sample_tool_definition):
        """Test generating tool descriptions for prompts."""
        def handler(param1, param2=42):
            return {"result": param1}
        registry.register(sample_tool_definition, handler)

        prompt = registry.get_tools_for_prompt()
        assert "test_tool" in prompt
        assert "A test tool" in prompt
        assert "param1" in prompt

    @pytest.mark.asyncio
    async def test_execute_tool(self, registry, sample_tool_definition):
        """Test executing a tool."""
        def handler(param1, param2=42):
            return {"result": param1, "param2": param2}
        registry.register(sample_tool_definition, handler)

        result = await registry.execute("test_tool", param1="hello")
        assert result.success is True
        assert result.data["result"] == "hello"
        assert result.data["param2"] == 42

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, registry):
        """Test executing a non-existent tool."""
        result = await registry.execute("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_with_error(self, registry, sample_tool_definition):
        """Test executing a tool that raises an error."""
        def failing_handler(param1, param2=42):
            raise ValueError("Test error")

        registry.register(sample_tool_definition, failing_handler)

        result = await registry.execute("test_tool", param1="hello")
        assert result.success is False
        assert "Test error" in result.error

    def test_tool_decorator(self, registry):
        """Test the tool decorator."""
        @registry.tool(
            name="decorated_tool",
            description="A decorated tool",
            category=ToolCategory.DATA_ACCESS,
            returns="str",
        )
        def my_tool(param1: str) -> str:
            return f"Result: {param1}"

        assert "decorated_tool" in registry._tools
        defn = registry.get_definition("decorated_tool")
        assert defn is not None
        assert defn.name == "decorated_tool"

    @pytest.mark.asyncio
    async def test_cache(self, registry):
        """Test tool result caching."""
        call_count = 0

        def counting_handler(param1):
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        defn = ToolDefinition(
            name="cached_tool",
            description="A cached tool",
            category=ToolCategory.DATA_ACCESS,
            parameters=[ToolParameter(name="param1", type="str", description="Param")],
            returns="dict",
            cache_ttl=60,  # 60 seconds cache
        )
        registry.register(defn, counting_handler)

        # First call
        result1 = await registry.execute("cached_tool", param1="test")
        assert result1.success is True
        assert result1.data["count"] == 1

        # Second call should use cache
        result2 = await registry.execute("cached_tool", param1="test")
        assert result2.success is True
        assert result2.data["count"] == 1  # Same count from cache
        assert result2.metadata.get("cached") is True

    @pytest.mark.asyncio
    async def test_clear_cache(self, registry):
        """Test clearing the cache."""
        call_count = 0

        def counting_handler(param1):
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        defn = ToolDefinition(
            name="cached_tool",
            description="A cached tool",
            category=ToolCategory.DATA_ACCESS,
            parameters=[ToolParameter(name="param1", type="str", description="Param")],
            returns="dict",
            cache_ttl=60,
        )
        registry.register(defn, counting_handler)

        # First call
        await registry.execute("cached_tool", param1="test")

        # Clear cache
        registry.clear_cache()

        # Second call should not use cache
        result = await registry.execute("cached_tool", param1="test")
        assert result.data["count"] == 2


class TestToolResult:
    """Tests for ToolResult."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = ToolResult(
            success=True,
            data={"key": "value"},
            duration_ms=10.5,
        )
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.duration_ms == 10.5

    def test_failed_result(self):
        """Test creating a failed result."""
        result = ToolResult(
            success=False,
            data=None,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_metadata(self):
        """Test result metadata."""
        result = ToolResult(
            success=True,
            data="result",
            metadata={"cached": True, "source": "test"},
        )
        assert result.metadata["cached"] is True
        assert result.metadata["source"] == "test"


class TestToolDefinition:
    """Tests for ToolDefinition."""

    def test_creation(self):
        """Test creating a tool definition."""
        defn = ToolDefinition(
            name="test",
            description="Test tool",
            category=ToolCategory.DATA_ACCESS,
            parameters=[
                ToolParameter(name="p1", type="str", description="Param 1"),
                ToolParameter(name="p2", type="int", description="Param 2", required=False, default=0),
            ],
            returns="dict",
        )
        assert defn.name == "test"
        assert len(defn.parameters) == 2
        assert defn.parameters[0].required is True
        assert defn.parameters[1].required is False
        assert defn.parameters[1].default == 0

    def test_category_enum(self):
        """Test tool categories."""
        assert ToolCategory.DATA_ACCESS.value == "data_access"
        assert ToolCategory.KNOWLEDGE_GRAPH.value == "knowledge_graph"
        assert ToolCategory.EVIDENCE_RETRIEVAL.value == "evidence_retrieval"
        assert ToolCategory.CLINICAL_REASONING.value == "clinical_reasoning"
