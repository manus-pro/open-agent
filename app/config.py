import os
import toml
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for OpenAgent."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to the config file. If None, default paths will be checked.
        """
        self.config_data: Dict[str, Any] = {}
        
        # Default config paths to check
        default_paths = [
            os.path.join(os.getcwd(), "config", "config.toml"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.toml"),
            os.path.expanduser("~/.config/open-agent/config.toml"),
        ]
        
        # Load config file
        if config_path:
            self.load_config(config_path)
        else:
            # Try default paths
            for path in default_paths:
                if os.path.exists(path):
                    self.load_config(path)
                    break
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Create required directories
        self._create_required_directories()
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from a TOML file.
        
        Args:
            config_path (str): Path to the config file
        """
        try:
            self.config_data = toml.load(config_path)
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the config."""
        # API keys
        if os.environ.get("OPENAI_API_KEY"):
            self.set_nested_value(["api", "openai_api_key"], os.environ["OPENAI_API_KEY"])
        
        if os.environ.get("FIRECRAWL_API_KEY"):
            self.set_nested_value(["api", "firecrawl_api_key"], os.environ["FIRECRAWL_API_KEY"])
        
        # LLM model
        if os.environ.get("OPENAI_MODEL"):
            self.set_nested_value(["llm", "model"], os.environ["OPENAI_MODEL"])
    
    def _create_required_directories(self) -> None:
        """Create required directories specified in the config."""
        # Document output directories
        for dir_key in ["pdf_output_dir", "markdown_output_dir", "code_output_dir"]:
            dir_path = self.get_nested_value(["document", dir_key])
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Log directory
        log_file = self.get_nested_value(["logging", "file"])
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    def get_nested_value(self, keys: list, default: Any = None) -> Any:
        """
        Get a nested value from the config data using a list of keys.
        
        Args:
            keys (list): List of keys to traverse
            default (Any, optional): Default value if key is not found
            
        Returns:
            Any: The value at the specified key path or default if not found
        """
        value = self.config_data
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]
        return value
    
    def set_nested_value(self, keys: list, value: Any) -> None:
        """
        Set a nested value in the config data using a list of keys.
        
        Args:
            keys (list): List of keys to traverse
            value (Any): Value to set
        """
        if not keys:
            return
        
        # Navigate to the parent dictionary
        current = self.config_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a top-level value from the config.
        
        Args:
            key (str): Config key
            default (Any, optional): Default value if key not found
            
        Returns:
            Any: The value or default if not found
        """
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a top-level value in the config.
        
        Args:
            key (str): Config key
            value (Any): Value to set
        """
        self.config_data[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-like access to config values."""
        return self.config_data[key]
    
    def get_timestamp(self) -> str:
        """
        Get a formatted timestamp string for use in artifacts and logs.
        
        Returns:
            str: ISO format timestamp string
        """
        import datetime
        return datetime.datetime.now().isoformat()


# Global config instance
config = Config()
