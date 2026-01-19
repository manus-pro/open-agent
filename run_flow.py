import argparse
import os
import sys
from typing import Dict, Any, Optional

from app.config import Config
from app.logger import get_logger
from app.flow.flow_factory import create_flow


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run an OpenAgent flow")
    parser.add_argument("--config", type=str, help="Path to the config file")
    parser.add_argument("--flow", type=str, required=True, help="Name of the flow to run")
    parser.add_argument("--input", type=str, help="Path to the input file")
    parser.add_argument("--output", type=str, help="Path for the output file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from the given path.
    
    Args:
        config_path (str, optional): Path to the config file
        
    Returns:
        Config: Configuration object
    """
    return Config(config_path)


def main():
    """Main entry point for running flows."""
    args = parse_args()
    
    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = get_logger("run_flow", {"logging": {"level": log_level}})
    
    try:
        # Load config
        config = load_config(args.config)
        
        # Get flow name from args
        flow_name = args.flow
        
        # Create flow
        flow = create_flow(flow_name, config)
        
        # Get input parameters
        input_params = {}
        if args.input and os.path.exists(args.input):
            with open(args.input, 'r') as f:
                content = f.read()
                input_params["content"] = content
        
        # Add output path if specified
        if args.output:
            input_params["output_path"] = args.output
        
        # Run the flow
        logger.info(f"Running flow: {flow_name}")
        result = flow.run(**input_params)
        
        # Display result
        if result.success:
            logger.info("Flow completed successfully")
            print(f"Result: {result.result}")
        else:
            logger.error(f"Flow failed: {result.error}")
            print(f"Error: {result.error}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
