"""
OpenAgent Python Agent Package
"""
import os
import sys
from app.logger import get_logger

# Set up logger
logger = get_logger("open-agent")

# Import and initialize tool registry
from app.tool.tool_collection import registry

# Log that tools are registered
logger.info(f"Registered {len(registry.tools)} tools in the tool registry")
