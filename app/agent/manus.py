from typing import Any, Dict, List, Optional
import asyncio
import os
import sys
import subprocess
import re

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.base import BaseAgent
from app.schema import AgentType, Conversation, TaskInput, TaskOutput, Message, WebResearchInput
from app.llm import llm_manager, get_llm_from_config
from app.logger import get_logger
from app.exceptions import AgentError
from app.prompt.manus import SYSTEM_PROMPT
from app.tool.pdf_generator import PDFGeneratorParams
from app.tool.markdown_generator import MarkdownGeneratorParams
from app.tool.code_generator import CodeGeneratorParams
from app.agent.planning import PlanningAgent


class ManusAgent(BaseAgent):
    """
    The primary orchestrator agent for OpenAgent.
    Uses LangChain's OpenAI Functions Agent for task execution.
    """
    
    def __init__(self, tools: Optional[List[str]] = None):
        """
        Initialize the Manus agent.
        
        Args:
            tools (List[str], optional): List of tool names to use
        """
        super().__init__(name=AgentType.MANUS.value, tools=tools)
        self.llm = llm_manager.llm
        
        # Define default tools if none provided
        if not tools:
            default_tools = [
                "pdf_generator",
                "markdown_generator",
                "browser",
                "firecrawl_research",
                "code_generator"
            ]
            for tool_name in default_tools:
                self.add_tool(tool_name)
    
    def _infer_task_and_plan(self, input_text: str) -> tuple[bool, Optional[List[str]]]:
        """
        Determine if the user input is a task and generate a plan if needed.
        
        Args:
            input_text (str): User input text
            
        Returns:
            tuple[bool, Optional[List[str]]]: (is_task, plan)
        """
        # Ask the LLM to determine if this is a task requiring a plan
        prompt = f"""
        Analyze the following user input and determine if it's a task that requires multiple steps to complete:
        
        USER INPUT: {input_text}
        
        First, determine if this is a task (requiring actions) or just a question/conversation:
        - If it's just a question or conversation, respond with "NOT_A_TASK"
        - If it's a task requiring actions, respond with "TASK" followed by a numbered list of clear, specific steps to complete it
        
        Example response for a task:
        TASK
        1. Search for information about Python memory management
        2. Generate a summary of key points
        3. Create a PDF document with the findings
        
        Example response for a non-task:
        NOT_A_TASK
        """
        
        response = llm_manager.generate_text(prompt)
        
        # Process the response
        if response.strip().startswith("TASK"):
            # Extract the plan from the response
            plan_lines = response.strip().split("\n")[1:]
            # Clean up the plan steps
            plan = [line.strip() for line in plan_lines if line.strip()]
            return True, plan
        else:
            return False, None
    
    def _create_agent_executor(self) -> AgentExecutor:
        """
        Create an agent executor with the agent's tools.
        
        Returns:
            AgentExecutor: LangChain agent executor
        """
        # Convert tools to LangChain-compatible tools
        langchain_tools = []
        for tool_name, tool in self.tools.items():
            # Get the appropriate args schema for the tool
            args_schema = None
            if tool_name == "pdf_generator":
                args_schema = PDFGeneratorParams
            elif tool_name == "markdown_generator":
                args_schema = MarkdownGeneratorParams
            elif tool_name == "code_generator":
                args_schema = CodeGeneratorParams
            elif tool_name == "firecrawl_research":
                args_schema = WebResearchInput
            
            # Create a structured tool that properly handles multiple arguments
            structured_tool = StructuredTool.from_function(
                name=tool.name,
                description=tool.description,
                func=tool.safe_run,
                args_schema=args_schema
            )
            langchain_tools.append(structured_tool)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="conversation"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_functions_agent(self.llm, langchain_tools, prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=langchain_tools,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        return agent_executor
    
    def _run(self, task_input: TaskInput) -> TaskOutput:
        """
        Run the Manus agent.
        
        Args:
            task_input (TaskInput): Task input
            
        Returns:
            TaskOutput: Task output
        """
        # Extract inputs
        task_description = task_input.task_description
        parameters = task_input.parameters or {}
        
        # Get conversation history if provided
        conversation = parameters.get("conversation", None)
        
        # Convert conversation to the format expected by the agent
        formatted_conversation = []
        if conversation and isinstance(conversation, Conversation):
            for message in conversation.messages:
                if message.role == "user":
                    formatted_conversation.append(HumanMessage(content=message.content))
                elif message.role == "assistant":
                    formatted_conversation.append(AIMessage(content=message.content))
        # If no conversation is provided, we'll use an empty list
        else:
            formatted_conversation = []
        
        # Check if we need a plan
        is_task, plan = self._infer_task_and_plan(task_description)
        
        if not is_task:
            # If this doesn't appear to be a task, handle as a regular query
            agent_executor = self._create_agent_executor()
            try:
                result = agent_executor.invoke({
                    "input": task_description,
                    "conversation": formatted_conversation
                })
                
                return TaskOutput(
                    content=result.get("output", ""),
                    success=True,
                    result=result.get("output", ""),
                    metadata={"agent_type": self.name}
                )
            except Exception as e:
                self.logger.error(f"Error in agent execution: {str(e)}")
                return TaskOutput(
                    content=f"There was an error processing your request: {str(e)}",
                    success=False,
                    result=None,
                    metadata={"agent_type": self.name, "error": str(e)}
                )
        
        # Run the agent with the task and plan
        agent_executor = self._create_agent_executor()
        
        # Format the input with the plan if available
        prompt_with_plan = task_description
        if plan:
            prompt_with_plan = f"""
Task: {task_description}

I've created a plan to help accomplish this task:
{self._format_plan_for_agent(plan)}

Please execute this plan step by step, using the available tools when needed.
For document generation, ensure high-quality, well-formatted Markdown content.
For code generation, write clean, well-documented code following best practices.
"""
        
        # Execute the agent
        try:
            self.logger.info(f"Executing task with {len(self.tools)} tools")
            result = agent_executor.invoke({
                "input": prompt_with_plan,
                "conversation": formatted_conversation
            })
            
            # Process the output
            raw_output = result.get("output", "")
            
            # Extract artifacts from the output
            artifacts = self._extract_artifacts_from_output(raw_output)
            
            # Also check for artifacts in intermediate_steps tool results
            if not artifacts and "intermediate_steps" in result:
                for action, action_result in result["intermediate_steps"]:
                    if isinstance(action_result, dict) and "artifact_path" in action_result:
                        # Found an artifact in a tool result
                        artifact_path = action_result["artifact_path"]
                        ext = os.path.splitext(artifact_path)[1][1:]  # Get extension without the dot
                        
                        # Determine artifact type based on extension
                        artifact_type = "code" if ext in ["py", "js", "ts", "jsx", "tsx", "html", "css", "sh"] else ext
                        
                        # Create or update artifacts dict
                        if not artifacts:
                            artifacts = {}
                        if artifact_type not in artifacts:
                            artifacts[artifact_type] = []
                        artifacts[artifact_type].append(artifact_path)
            
            return TaskOutput(
                success=True,
                result=raw_output,
                metadata={
                    "agent_type": self.name,
                    "plan": plan,
                    "artifacts": artifacts,
                    "tool_calls": self._count_tool_calls(result)
                }
            )
        except Exception as e:
            self.logger.error(f"Error in agent execution: {str(e)}")
            return TaskOutput(
                content=f"There was an error processing your request: {str(e)}",
                success=False,
                result=None,
                metadata={"agent_type": self.name, "error": str(e), "plan": plan}
            )
            
    def _format_plan_for_agent(self, plan: List[str]) -> str:
        """Format the plan for inclusion in the agent prompt."""
        return "\n".join([f"- {step}" for step in plan])
        
    def _extract_artifacts_from_output(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Extract artifacts information from the agent output.
        
        Args:
            output (str): Agent output
            
        Returns:
            Optional[Dict[str, Any]]: Extracted artifacts or None
        """
        # Look for file paths in the output
        file_patterns = [
            r'generated (?:file|document|code file).*?:\s*([^\s]+\.(?:py|js|html|css|pdf|md|txt|json|sh|ts|jsx|tsx))',
            r'created (?:file|document|code).*?:\s*([^\s]+\.(?:py|js|html|css|pdf|md|txt|json|sh|ts|jsx|tsx))',
            r'saved (?:to|as).*?:\s*([^\s]+\.(?:py|js|html|css|pdf|md|txt|json|sh|ts|jsx|tsx))',
            r'file (?:is at|available at).*?:\s*([^\s]+\.(?:py|js|html|css|pdf|md|txt|json|sh|ts|jsx|tsx))',
            r'output (?:file|saved to).*?:\s*([^\s]+\.(?:py|js|html|css|pdf|md|txt|json|sh|ts|jsx|tsx))',
            r'code (?:file saved as|artifact saved).*?:\s*([^\s]+\.(?:py|js|html|css|md|txt|json|sh|ts|jsx|tsx))'
        ]
        
        artifacts = {}
        
        for pattern in file_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                for match in matches:
                    file_path = match.strip()
                    # Extract file extension
                    _, ext = os.path.splitext(file_path)
                    artifact_type = ext[1:] if ext else "file"
                    
                    # Check if this is code
                    if artifact_type in ['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'sh']:
                        if 'code' not in artifacts:
                            artifacts['code'] = []
                        artifacts['code'].append(file_path)
                    else:
                        if artifact_type not in artifacts:
                            artifacts[artifact_type] = []
                        artifacts[artifact_type].append(file_path)
        
        # Additional check: see if there are artifacts in tool results from intermediate steps
        if not artifacts and hasattr(self, 'agent_executor') and hasattr(self.agent_executor, 'intermediate_steps'):
            for step in self.agent_executor.intermediate_steps:
                if isinstance(step, tuple) and len(step) == 2:
                    result = step[1]
                    if isinstance(result, dict) and 'artifact_path' in result:
                        artifact_path = result['artifact_path']
                        _, ext = os.path.splitext(artifact_path)
                        artifact_type = ext[1:] if ext else "file"
                        
                        # Classify code artifacts
                        if artifact_type in ['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'sh']:
                            if 'code' not in artifacts:
                                artifacts['code'] = []
                            artifacts['code'].append(artifact_path)
                        else:
                            if artifact_type not in artifacts:
                                artifacts[artifact_type] = []
                            artifacts[artifact_type].append(artifact_path)
                    
        if not artifacts:
            return None
            
        return artifacts
        
    def _count_tool_calls(self, result: Dict[str, Any]) -> int:
        """Count the number of tool calls made during execution."""
        if "intermediate_steps" not in result:
            return 0
            
        return len(result["intermediate_steps"])


class Manus:
    """
    Main interface class for the OpenAgent system.
    """
    
    def __init__(self):
        """Initialize the Manus interface."""
        self.agent = ManusAgent()
        self.logger = get_logger("manus")
        self.recent_artifacts = []
        self.conversation = Conversation(messages=[])
        
    async def run(self, prompt: str):
        """
        Process a user prompt asynchronously.
        
        Args:
            prompt (str): User input prompt
        """
        # Add user message to conversation
        self.conversation.messages.append(Message(role="user", content=prompt))
        
        # Check if the prompt is asking to open a previously generated artifact
        if await self._check_artifact_request(prompt):
            return
            
        # Create task input with conversation history
        task_input = TaskInput(
            task_description=prompt,
            parameters={"conversation": self.conversation}
        )
        
        try:
            # Run the agent (asynchronously)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.agent.run(task_input))
            
            # Process the result
            if result.success:
                # Get the output content
                output = result.result
                
                # Store any artifacts found in the output
                if result.metadata and "artifacts" in result.metadata:
                    await self._process_artifacts(result.metadata["artifacts"])
                
                # Display the output to the user
                print(f"\n{output}\n")
                
                # Add assistant message to conversation
                self.conversation.messages.append(Message(role="assistant", content=output))
            else:
                # Handle error case
                error_msg = f"I'm sorry, I encountered an error: {result.metadata.get('error', 'Unknown error')}"
                print(f"\n{error_msg}\n")
                
                # Add error message to conversation
                self.conversation.messages.append(Message(role="assistant", content=error_msg))
                
        except Exception as e:
            # Handle unexpected exceptions
            self.logger.error(f"Error executing Manus agent: {str(e)}")
            error_msg = f"I'm sorry, something went wrong: {str(e)}"
            print(f"\n{error_msg}\n")
            
            # Add error message to conversation
            self.conversation.messages.append(Message(role="assistant", content=error_msg))
    
    async def _check_artifact_request(self, prompt: str) -> bool:
        """
        Check if the user is requesting to open an artifact.
        
        Args:
            prompt (str): User prompt
            
        Returns:
            bool: True if the request was handled
        """
        if not self.recent_artifacts:
            return False
            
        # Check if this might be a request to open a file
        open_terms = ["open", "show", "display", "view", "run", "execute"]
        if not any(term in prompt.lower() for term in open_terms):
            return False
            
        # Get a list of artifact file paths
        artifact_paths = []
        for artifact_type, paths in self.recent_artifacts[-1].items():
            artifact_paths.extend(paths)
            
        if not artifact_paths:
            return False
            
        # Look for file names or extensions in the prompt
        for path in artifact_paths:
            filename = os.path.basename(path)
            if filename.lower() in prompt.lower() or os.path.splitext(filename)[1][1:].lower() in prompt.lower():
                await self._open_artifact(path)
                
                # Add response to conversation
                response = f"I've opened the file: {path}"
                print(f"\n{response}\n")
                self.conversation.messages.append(Message(role="assistant", content=response))
                return True
                
        return False
    
    async def _process_artifacts(self, artifacts: Dict[str, Any]):
        """
        Process and store artifacts.
        
        Args:
            artifacts (Dict[str, Any]): Artifacts information
        """
        if not artifacts:
            return
            
        # Store in recent artifacts
        self.recent_artifacts.append(artifacts)
        if len(self.recent_artifacts) > 5:  # Keep only the 5 most recent sets
            self.recent_artifacts.pop(0)
            
        # Display artifacts to the user
        print("\nGenerated files:")
        for artifact_type, paths in artifacts.items():
            for path in paths:
                print(f"- {path} ({artifact_type})")
                
        # Check if we should auto-open any artifacts
        await self._check_auto_open_artifacts(artifacts)
    
    async def _check_auto_open_artifacts(self, artifacts: Dict[str, Any]):
        """
        Check if any artifacts should be automatically opened.
        
        Args:
            artifacts (Dict[str, Any]): Artifacts information
        """
        # Auto-open PDF files if there's only one
        if "pdf" in artifacts and len(artifacts["pdf"]) == 1:
            pdf_path = artifacts["pdf"][0]
            await self._open_artifact(pdf_path)
            print(f"\nAutomatically opened: {pdf_path}\n")
            
        # Auto-open code files
        if "code" in artifacts and len(artifacts["code"]) > 0:
            code_path = artifacts["code"][0]  # Open the first code file
            await self._open_artifact(code_path)
            print(f"\nAutomatically opened code file: {code_path}\n")
    
    async def _open_artifact(self, file_path: str):
        """
        Open an artifact using the appropriate application.
        
        Args:
            file_path (str): Path to the file
        """
        if not os.path.exists(file_path):
            self.logger.error(f"File does not exist: {file_path}")
            return
            
        try:
            # Use appropriate command based on platform
            if sys.platform == "darwin":  # macOS
                subprocess.Popen(["open", file_path])
            elif sys.platform == "win32":  # Windows
                os.startfile(file_path)
            else:  # Linux
                subprocess.Popen(["xdg-open", file_path])
                
            self.logger.info(f"Opened file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error opening file: {str(e)}")
