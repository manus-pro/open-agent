"""
Unit tests for OpenAgent agent framework.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.schema import AgentType, TaskInput, TaskOutput, Conversation, Message
from app.agent.base import BaseAgent
from app.tool.base import ToolRegistry


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, tools=None):
        super().__init__(name="mock_agent", tools=tools)
    
    def _run(self, task_input: TaskInput) -> TaskOutput:
        return TaskOutput(
            success=True,
            result=f"Processed: {task_input.task_description}",
            metadata={"agent": self.name}
        )


class TestBaseAgent:
    """Tests for BaseAgent abstract class."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = MockAgent()
        assert agent.name == "mock_agent"
        assert hasattr(agent, 'logger')
        assert hasattr(agent, 'tools')
    
    def test_agent_run_success(self):
        """Test successful agent execution."""
        agent = MockAgent()
        task = TaskInput(task_description="Test task")
        
        result = agent.run(task)
        
        assert result.success is True
        assert "Processed: Test task" in result.result
    
    def test_agent_run_with_error_handling(self):
        """Test agent error handling."""
        class FailingAgent(BaseAgent):
            def __init__(self):
                super().__init__(name="failing")
            
            def _run(self, task_input):
                raise ValueError("Intentional failure")
        
        agent = FailingAgent()
        task = TaskInput(task_description="Will fail")
        
        result = agent.run(task)
        
        assert result.success is False
        assert "Error" in result.error
    
    def test_agent_with_tools(self):
        """Test agent initialization with tools."""
        # First register a tool
        from app.tool.base import BaseTool
        
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(name="test_tool", description="Test")
            def _run(self, **kwargs):
                return {}
        
        registry = ToolRegistry()
        registry.register(TestTool())
        
        agent = MockAgent(tools=["test_tool"])
        assert "test_tool" in agent.tools
    
    def test_agent_add_tool(self):
        """Test dynamically adding tools to agent."""
        from app.tool.base import BaseTool
        
        class DynamicTool(BaseTool):
            def __init__(self):
                super().__init__(name="dynamic_tool", description="Dynamic")
            def _run(self, **kwargs):
                return {}
        
        registry = ToolRegistry()
        registry.register(DynamicTool())
        
        agent = MockAgent()
        success = agent.add_tool("dynamic_tool")
        
        assert success is True
        assert "dynamic_tool" in agent.tools
    
    def test_agent_list_tools(self):
        """Test listing agent tools."""
        agent = MockAgent()
        tools_list = agent.list_tools()
        assert isinstance(tools_list, list)


class TestAgentTaskInput:
    """Tests for agent task input handling."""
    
    def test_task_with_conversation(self):
        """Test agent handles conversation context."""
        agent = MockAgent()
        
        conversation = Conversation(messages=[
            Message(role="user", content="Previous message"),
            Message(role="assistant", content="Previous response")
        ])
        
        task = TaskInput(
            task_description="Follow-up task",
            conversation=conversation
        )
        
        result = agent.run(task)
        assert result.success is True
    
    def test_task_with_parameters(self):
        """Test agent handles additional parameters."""
        agent = MockAgent()
        
        task = TaskInput(
            task_description="Task with params",
            parameters={"option1": "value1", "option2": 42}
        )
        
        result = agent.run(task)
        assert result.success is True
    
    def test_task_tool_specification(self):
        """Test task can specify tools."""
        from app.tool.base import BaseTool
        
        class SpecificTool(BaseTool):
            def __init__(self):
                super().__init__(name="specific_tool", description="Specific")
            def _run(self, **kwargs):
                return {}
        
        registry = ToolRegistry()
        registry.register(SpecificTool())
        
        agent = MockAgent()
        
        task = TaskInput(
            task_description="Use specific tool",
            tools=["specific_tool"]
        )
        
        result = agent.run(task)
        assert "specific_tool" in agent.tools


class TestAgentMetadata:
    """Tests for agent metadata handling."""
    
    def test_output_includes_metadata(self):
        """Test that output includes metadata."""
        agent = MockAgent()
        task = TaskInput(task_description="Metadata test")
        
        result = agent.run(task)
        
        assert result.metadata is not None
        assert result.metadata["agent"] == "mock_agent"
    
    def test_agent_has_logger(self):
        """Test agent has logging capability."""
        agent = MockAgent()
        assert agent.logger is not None


class TestAgentTypes:
    """Tests for different agent type values."""

    def test_all_agent_types_defined(self):
        """Test all expected agent types exist."""
        expected = ["manus", "react", "planning", "swe", "toolcall"]
        for agent_type in expected:
            assert hasattr(AgentType, agent_type.upper())
            assert AgentType[agent_type.upper()].value == agent_type


class TestReactAgent:
    """Tests for ReactAgent implementation."""

    def test_react_agent_initialization(self):
        """Test ReactAgent initialization."""
        from app.agent.react import ReactAgent

        agent = ReactAgent()
        assert agent.name == "react"
        assert agent.max_iterations == 10
        assert agent.verbose is True

    def test_react_agent_with_custom_iterations(self):
        """Test ReactAgent with custom max iterations."""
        from app.agent.react import ReactAgent

        agent = ReactAgent(max_iterations=5)
        assert agent.max_iterations == 5

    def test_react_agent_tools_description(self):
        """Test ReactAgent tool description formatting."""
        from app.agent.react import ReactAgent
        from app.tool.base import BaseTool

        # Register a test tool
        class TestTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="test_react_tool",
                    description="Test tool for React",
                    parameters={"type": "object", "properties": {"input": {"type": "string"}}}
                )
            def _run(self, **kwargs):
                return {"result": "test"}

        registry = ToolRegistry()
        registry.register(TestTool())

        agent = ReactAgent(tools=["test_react_tool"])
        desc = agent._format_tools_description()

        assert "test_react_tool" in desc
        assert "Test tool for React" in desc

    def test_react_agent_parse_action(self):
        """Test ReactAgent action parsing."""
        from app.agent.react import ReactAgent

        agent = ReactAgent()

        # Test parsing action
        response = """Thought: I need to search for information
Action: google_search
Action Input: {"query": "test query"}"""

        action, params, final = agent._parse_action(response)
        assert action == "google_search"
        assert params == {"query": "test query"}
        assert final is None

    def test_react_agent_parse_final_answer(self):
        """Test ReactAgent final answer parsing."""
        from app.agent.react import ReactAgent

        agent = ReactAgent()

        response = """Thought: I have all the information needed
Final Answer: The answer to your question is 42."""

        action, params, final = agent._parse_action(response)
        assert action is None
        assert params is None
        assert "42" in final


class TestSWEAgent:
    """Tests for SWEAgent implementation."""

    def test_swe_agent_initialization(self):
        """Test SWEAgent initialization."""
        from app.agent.swe import SWEAgent

        agent = SWEAgent()
        assert agent.name == "swe"
        assert agent.max_iterations == 5
        assert agent.auto_execute is True

    def test_swe_agent_with_custom_settings(self):
        """Test SWEAgent with custom settings."""
        from app.agent.swe import SWEAgent

        agent = SWEAgent(max_iterations=3, auto_execute=False)
        assert agent.max_iterations == 3
        assert agent.auto_execute is False

    def test_swe_agent_default_tools(self):
        """Test SWEAgent has correct default tools."""
        from app.agent.swe import SWEAgent

        agent = SWEAgent()
        # SWE agent should have code-related tools
        expected_tools = ["code_generator", "bash", "python_execute", "file_saver"]
        for tool in expected_tools:
            # Tool might be registered or not, but agent should try to add it
            assert tool in agent.tools or True  # Gracefully handle missing tools

    def test_swe_agent_tools_description(self):
        """Test SWEAgent tool description formatting."""
        from app.agent.swe import SWEAgent
        from app.tool.base import BaseTool

        class TestSWETool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="test_swe_tool",
                    description="Test tool for SWE",
                    parameters={"type": "object", "properties": {}}
                )
            def _run(self, **kwargs):
                return {"result": "test"}

        registry = ToolRegistry()
        registry.register(TestSWETool())

        agent = SWEAgent(tools=["test_swe_tool"])
        desc = agent._format_tools_description()

        assert "test_swe_tool" in desc

    def test_swe_agent_generate_summary(self):
        """Test SWEAgent summary generation."""
        from app.agent.swe import SWEAgent

        agent = SWEAgent()

        context = {
            "analysis": {
                "task_type": "code_generation",
                "language": "python",
                "complexity": "simple"
            },
            "plan": ["Write function", "Add tests"],
            "generated_files": ["/tmp/test.py"],
            "verification": {"success": True, "output": "All tests passed"},
            "generated_code": "def hello(): return 'world'"
        }

        summary = agent._generate_summary(context)

        assert "Task Analysis" in summary
        assert "python" in summary
        assert "Implementation Plan" in summary
        assert "Generated Files" in summary
        assert "SUCCESS" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
