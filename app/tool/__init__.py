"""
Tool module for OpenAgent.
"""
from app.tool.base import BaseTool, ToolRegistry
from app.tool.file_saver import FileSaverTool
from app.tool.browser_use_tool import BrowserTool

# Try/except imports for tools that have external dependencies
registry = ToolRegistry()

# Register core tools
registry.register(FileSaverTool())
registry.register(BrowserTool())

# Try to import and register other tools with external dependencies
try:
    from app.tool.pdf_generator import PDFGeneratorTool, create_pdf_generator_from_input
    registry.register(PDFGeneratorTool())
except ImportError as e:
    print(f"Warning: Could not import PDFGeneratorTool: {e}")

try:
    from app.tool.markdown_generator import MarkdownGeneratorTool, create_markdown_from_input
    registry.register(MarkdownGeneratorTool())
except ImportError as e:
    print(f"Warning: Could not import MarkdownGeneratorTool: {e}")

try:
    from app.tool.code_generator import CodeGeneratorTool, generate_code_from_input
    registry.register(CodeGeneratorTool())
except ImportError as e:
    print(f"Warning: Could not import CodeGeneratorTool: {e}")

try:
    from app.tool.firecrawl_research import FirecrawlResearchTool, conduct_web_research
    registry.register(FirecrawlResearchTool())
except ImportError as e:
    print(f"Warning: Could not import FirecrawlResearchTool: {e}")

try:
    from app.tool.google_search import GoogleSearchTool
    registry.register(GoogleSearchTool())
except ImportError as e:
    print(f"Warning: Could not import GoogleSearchTool: {e}")

__all__ = [
    'BaseTool', 'ToolRegistry', 'registry',
    'FileSaverTool', 'BrowserTool',
    # These may or may not be available depending on imports
    'MarkdownGeneratorTool', 'PDFGeneratorTool', 'CodeGeneratorTool',
    'FirecrawlResearchTool', 'GoogleSearchTool', 'CreateChatCompletionTool',
    # Functions for direct usage
    'create_markdown_from_input', 'create_pdf_generator_from_input',
    'generate_code_from_input', 'conduct_web_research'
]
