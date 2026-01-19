"""
Unit tests for OpenAgent tool framework.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.tool.base import BaseTool, ToolRegistry


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input text"}
                },
                "required": ["input"]
            }
        )
    
    def _run(self, input: str = "", **kwargs) -> dict:
        return {"result": f"Processed: {input}"}


class TestBaseTool:
    """Tests for BaseTool abstract class."""
    
    def test_tool_initialization(self):
        """Test tool initialization with parameters."""
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "A mock tool for testing"
        assert "properties" in tool.parameters
    
    def test_tool_run(self):
        """Test tool execution."""
        tool = MockTool()
        result = tool.run(input="test data")
        assert result["result"] == "Processed: test data"
    
    def test_tool_safe_run(self):
        """Test safe_run method for LangChain compatibility."""
        tool = MockTool()
        result = tool.safe_run(input="safe test")
        assert "result" in result
    
    def test_tool_to_dict(self):
        """Test conversion to dictionary."""
        tool = MockTool()
        tool_dict = tool.to_dict()
        assert tool_dict["name"] == "mock_tool"
        assert tool_dict["description"] == "A mock tool for testing"
        assert "parameters" in tool_dict
    
    def test_tool_to_openai_function(self):
        """Test conversion to OpenAI function format."""
        tool = MockTool()
        func = tool.to_openai_function()
        assert func["name"] == "mock_tool"
        assert "description" in func
        assert "parameters" in func
    
    def test_tool_error_handling(self):
        """Test error handling in tool execution."""
        class FailingTool(BaseTool):
            def __init__(self):
                super().__init__(name="failing", description="Fails")
            
            def _run(self, **kwargs):
                raise ValueError("Intentional failure")
        
        tool = FailingTool()
        with pytest.raises(Exception):
            tool.run()


class TestToolRegistry:
    """Tests for ToolRegistry singleton."""
    
    def test_singleton_pattern(self):
        """Test that registry follows singleton pattern."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        assert registry1 is registry2
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        registry.clear()  # Clear for clean test
        
        tool = MockTool()
        registry.register(tool)
        
        assert registry.get("mock_tool") is tool
    
    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        result = registry.get("nonexistent_tool_xyz")
        assert result is None
    
    def test_list_tools(self):
        """Test listing all registered tools."""
        registry = ToolRegistry()
        registry.clear()
        
        tool = MockTool()
        registry.register(tool)
        
        tools = registry.list_tools()
        assert len(tools) >= 1
        assert any(t["name"] == "mock_tool" for t in tools)
    
    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)
        
        registry.clear()
        assert registry.get("mock_tool") is None


class TestToolParameterHandling:
    """Tests for tool parameter handling edge cases."""
    
    def test_safe_run_with_single_string(self):
        """Test safe_run handles single string argument."""
        tool = MockTool()
        # Mock the behavior for single string input
        result = tool.safe_run(input="single string")
        assert "result" in result
    
    def test_safe_run_with_kwargs(self):
        """Test safe_run with keyword arguments."""
        tool = MockTool()
        result = tool.safe_run(input="kwarg test", extra="ignored")
        assert "result" in result
    
    def test_default_parameters_schema(self):
        """Test default parameters schema generation."""
        class MinimalTool(BaseTool):
            def __init__(self):
                super().__init__(name="minimal", description="Minimal tool")
            
            def _run(self, **kwargs):
                return {}
        
        tool = MinimalTool()
        assert tool.parameters["type"] == "object"
        assert tool.parameters["properties"] == {}


class TestToolLogging:
    """Tests for tool logging functionality."""
    
    def test_tool_has_logger(self):
        """Test that tools have a logger attached."""
        tool = MockTool()
        assert hasattr(tool, 'logger')
        assert tool.logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
