"""
Unit tests for OpenAgent schema definitions.
"""
import pytest
from app.schema import (
    AgentType, ToolType, DocumentFormat, WebDriverType,
    Message, Conversation, TaskInput, TaskOutput,
    WebResearchInput, BrowserTaskInput, CodeGenerationInput,
    VisualizationData, DataTable, DocumentGenerationOptions
)


class TestEnums:
    """Tests for enumeration types."""
    
    def test_agent_types(self):
        """Test that all expected agent types are defined."""
        assert AgentType.MANUS.value == "manus"
        assert AgentType.REACT.value == "react"
        assert AgentType.PLANNING.value == "planning"
        assert AgentType.SWE.value == "swe"
        assert AgentType.TOOLCALL.value == "toolcall"
    
    def test_tool_types(self):
        """Test that all expected tool types are defined."""
        expected_tools = [
            "pdf_generator", "markdown_generator", "code_generator",
            "browser", "firecrawl", "bash", "python_execute",
            "file_saver", "google_search", "create_chat_completion",
            "str_replace_editor", "terminate"
        ]
        for tool in expected_tools:
            assert hasattr(ToolType, tool.upper())
    
    def test_document_formats(self):
        """Test supported document formats."""
        assert DocumentFormat.PDF.value == "pdf"
        assert DocumentFormat.MARKDOWN.value == "markdown"
        assert DocumentFormat.HTML.value == "html"
        assert DocumentFormat.TEXT.value == "text"
    
    def test_webdriver_types(self):
        """Test supported browser types."""
        assert WebDriverType.CHROME.value == "chrome"
        assert WebDriverType.FIREFOX.value == "firefox"


class TestMessage:
    """Tests for Message model."""
    
    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_message_roles(self):
        """Test different message roles."""
        for role in ["system", "user", "assistant"]:
            msg = Message(role=role, content="test")
            assert msg.role == role


class TestConversation:
    """Tests for Conversation model."""
    
    def test_empty_conversation(self):
        """Test creating an empty conversation."""
        conv = Conversation()
        assert conv.messages == []
    
    def test_conversation_with_messages(self):
        """Test conversation with message list."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]
        conv = Conversation(messages=messages)
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"


class TestTaskInput:
    """Tests for TaskInput model."""
    
    def test_minimal_task_input(self):
        """Test task input with only required field."""
        task = TaskInput(task_description="Generate a report")
        assert task.task_description == "Generate a report"
        assert task.conversation is None
        assert task.tools is None
    
    def test_task_input_with_tools(self):
        """Test task input with specified tools."""
        task = TaskInput(
            task_description="Create PDF",
            tools=["pdf_generator", "markdown_generator"]
        )
        assert len(task.tools) == 2
        assert "pdf_generator" in task.tools
    
    def test_task_input_with_agent_type(self):
        """Test task input specifying agent type."""
        task = TaskInput(
            task_description="Plan and execute",
            agent_type=AgentType.PLANNING
        )
        assert task.agent_type == AgentType.PLANNING


class TestTaskOutput:
    """Tests for TaskOutput model."""
    
    def test_successful_output(self):
        """Test successful task output."""
        output = TaskOutput(success=True, result="Task completed")
        assert output.success is True
        assert output.result == "Task completed"
        assert output.error is None
    
    def test_failed_output(self):
        """Test failed task output."""
        output = TaskOutput(success=False, error="Tool execution failed")
        assert output.success is False
        assert output.error == "Tool execution failed"
    
    def test_output_with_metadata(self):
        """Test output with metadata."""
        output = TaskOutput(
            success=True,
            result="Done",
            metadata={"tool_calls": 3, "artifacts": ["report.pdf"]}
        )
        assert output.metadata["tool_calls"] == 3


class TestWebResearchInput:
    """Tests for WebResearchInput model."""
    
    def test_default_values(self):
        """Test default configuration values."""
        input_data = WebResearchInput(query="AI agents")
        assert input_data.output_format == DocumentFormat.MARKDOWN
        assert input_data.max_depth == 1
        assert input_data.max_pages == 10
        assert input_data.include_visualizations is True


class TestBrowserTaskInput:
    """Tests for BrowserTaskInput model."""
    
    def test_browser_input(self):
        """Test browser task input creation."""
        input_data = BrowserTaskInput(
            url="https://example.com",
            actions=[{"type": "click", "selector": "#button"}]
        )
        assert input_data.url == "https://example.com"
        assert len(input_data.actions) == 1
        assert input_data.headless is True  # Default


class TestCodeGenerationInput:
    """Tests for CodeGenerationInput model."""
    
    def test_code_gen_input(self):
        """Test code generation input."""
        input_data = CodeGenerationInput(
            description="Create a sorting function",
            language="python"
        )
        assert input_data.description == "Create a sorting function"
        assert input_data.language == "python"
        assert input_data.execute_code is True  # Default


class TestVisualizationData:
    """Tests for VisualizationData model."""
    
    def test_visualization_creation(self):
        """Test visualization data creation."""
        viz = VisualizationData(
            title="Sales Chart",
            visualization_type="bar_chart",
            data={"labels": ["Q1", "Q2"], "values": [100, 150]}
        )
        assert viz.title == "Sales Chart"
        assert viz.visualization_type == "bar_chart"


class TestDataTable:
    """Tests for DataTable model."""
    
    def test_data_table_creation(self):
        """Test data table creation."""
        table = DataTable(
            title="Results",
            columns=["Name", "Score"],
            rows=[["Alice", 95], ["Bob", 87]]
        )
        assert table.title == "Results"
        assert len(table.columns) == 2
        assert len(table.rows) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
