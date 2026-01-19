"""
ReactAgent: Implementation of the ReAct (Reasoning and Acting) paradigm.

Based on: Yao et al. 2023 - "ReAct: Synergizing Reasoning and Acting in Language Models"
ICLR 2023: https://arxiv.org/abs/2210.03629

The ReAct approach interleaves reasoning traces (Thought) with task-specific actions,
enabling the agent to perform dynamic reasoning while interacting with external tools.
"""
from typing import Any, Dict, List, Optional, Tuple
import re
import json

from app.agent.base import BaseAgent
from app.schema import AgentType, TaskInput, TaskOutput, Message, Conversation
from app.llm import llm_manager
from app.prompt.react import REACT_SYSTEM_PROMPT, REACT_STEP_PROMPT, REACT_OBSERVATION_PROMPT


class ReactAgent(BaseAgent):
    """
    ReAct agent that implements the Reasoning and Acting paradigm.

    The agent follows an iterative cycle:
    1. Thought: Reason about the current state and what to do next
    2. Action: Select and invoke a tool
    3. Observation: Process the tool result
    4. Repeat until task is complete or max iterations reached

    This approach enables transparent reasoning and effective tool use
    for complex multi-step tasks.
    """

    def __init__(
        self,
        tools: Optional[List[str]] = None,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize the ReAct agent.

        Args:
            tools (List[str], optional): List of tool names to use
            max_iterations (int): Maximum number of reasoning cycles (default: 10)
            verbose (bool): Whether to log detailed execution traces
        """
        super().__init__(name=AgentType.REACT.value, tools=tools)
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Define default tools if none provided
        if not tools:
            default_tools = [
                "pdf_generator",
                "markdown_generator",
                "firecrawl_research",
                "code_generator",
                "google_search"
            ]
            for tool_name in default_tools:
                self.add_tool(tool_name)

    def _format_tools_description(self) -> str:
        """
        Format available tools into a description string for the prompt.

        Returns:
            str: Formatted tool descriptions
        """
        tool_descriptions = []
        for tool_name, tool in self.tools.items():
            # Get parameter info if available
            params_info = ""
            if hasattr(tool, 'parameters') and tool.parameters:
                props = tool.parameters.get('properties', {})
                if props:
                    param_names = list(props.keys())
                    params_info = f" (Parameters: {', '.join(param_names)})"

            tool_descriptions.append(f"- {tool_name}: {tool.description}{params_info}")

        return "\n".join(tool_descriptions)

    def _parse_action(self, response: str) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Parse the LLM response to extract action, parameters, or final answer.

        Args:
            response (str): LLM response text

        Returns:
            Tuple of (action_name, action_params, final_answer)
            - If action found: (action_name, params_dict, None)
            - If final answer: (None, None, final_answer)
            - If parse error: (None, None, None)
        """
        # Check for Final Answer
        final_answer_match = re.search(
            r'Final\s*Answer\s*:\s*(.+)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        if final_answer_match:
            return None, None, final_answer_match.group(1).strip()

        # Check for Action
        action_match = re.search(
            r'Action\s*:\s*(\w+)',
            response,
            re.IGNORECASE
        )

        if not action_match:
            return None, None, None

        action_name = action_match.group(1).strip()

        # Extract Action Input
        action_input_match = re.search(
            r'Action\s*Input\s*:\s*(.+?)(?=\n\n|\nThought:|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )

        action_params = {}
        if action_input_match:
            input_text = action_input_match.group(1).strip()

            # Try to parse as JSON
            try:
                # Handle both raw JSON and markdown-wrapped JSON
                if input_text.startswith('```'):
                    # Extract from markdown code block
                    json_match = re.search(r'```(?:json)?\s*(.+?)\s*```', input_text, re.DOTALL)
                    if json_match:
                        input_text = json_match.group(1)

                action_params = json.loads(input_text)
            except json.JSONDecodeError:
                # Try to parse as key-value pairs
                if '=' in input_text or ':' in input_text:
                    # Simple key-value parsing
                    for line in input_text.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            action_params[key.strip()] = value.strip().strip('"\'')
                        elif ':' in line and not line.strip().startswith('{'):
                            key, value = line.split(':', 1)
                            action_params[key.strip()] = value.strip().strip('"\'')
                else:
                    # Use as single 'input' parameter
                    action_params = {"input": input_text}

        return action_name, action_params, None

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name (str): Name of the tool to execute
            params (Dict[str, Any]): Parameters for the tool

        Returns:
            str: Tool execution result or error message
        """
        # Find the tool (with fuzzy matching)
        actual_tool_name = None
        for available_tool in self.tools.keys():
            if tool_name.lower() == available_tool.lower():
                actual_tool_name = available_tool
                break
            elif tool_name.lower() in available_tool.lower() or available_tool.lower() in tool_name.lower():
                actual_tool_name = available_tool
                break

        if not actual_tool_name:
            return f"Error: Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"

        tool = self.tools[actual_tool_name]

        try:
            self.logger.debug(f"Executing tool '{actual_tool_name}' with params: {params}")
            result = tool.safe_run(**params)

            # Format result for observation
            if isinstance(result, dict):
                if 'error' in result:
                    return f"Tool Error: {result['error']}"
                elif 'content' in result:
                    # Truncate long content
                    content = str(result['content'])
                    if len(content) > 2000:
                        content = content[:2000] + "... [truncated]"
                    return content
                elif 'result' in result:
                    return str(result['result'])
                else:
                    return json.dumps(result, indent=2)
            else:
                return str(result)

        except Exception as e:
            self.logger.error(f"Tool execution error: {str(e)}")
            return f"Tool Execution Error: {str(e)}"

    def _run(self, task_input: TaskInput) -> TaskOutput:
        """
        Execute the ReAct agent with the given task input.

        Implements the ReAct loop:
        1. Generate Thought + Action (or Final Answer)
        2. If Action, execute tool and get Observation
        3. Repeat until Final Answer or max iterations

        Args:
            task_input (TaskInput): Task input containing the task description

        Returns:
            TaskOutput: Task output with result and execution trace
        """
        task_description = task_input.task_description
        self.logger.info(f"ReAct agent received task: {task_description}")

        # Build execution trace
        trace: List[Dict[str, str]] = []
        history_text = ""

        # Get tool descriptions
        tools_description = self._format_tools_description()

        for iteration in range(self.max_iterations):
            self.logger.info(f"ReAct iteration {iteration + 1}/{self.max_iterations}")

            # Build prompt for this iteration
            prompt = REACT_STEP_PROMPT.format(
                task=task_description,
                tools=tools_description,
                history=history_text
            )

            # Generate response from LLM
            response = llm_manager.generate_text(
                prompt,
                system_prompt=REACT_SYSTEM_PROMPT
            )

            if self.verbose:
                self.logger.debug(f"LLM Response:\n{response}")

            # Extract thought
            thought_match = re.search(
                r'Thought\s*:\s*(.+?)(?=\nAction|\nFinal\s*Answer|$)',
                response,
                re.IGNORECASE | re.DOTALL
            )
            thought = thought_match.group(1).strip() if thought_match else ""

            # Parse action or final answer
            action_name, action_params, final_answer = self._parse_action(response)

            # Record in trace
            trace_entry = {"thought": thought}

            if final_answer:
                # Task complete
                trace_entry["final_answer"] = final_answer
                trace.append(trace_entry)

                self.logger.info(f"ReAct completed with final answer after {iteration + 1} iterations")

                return TaskOutput(
                    success=True,
                    result=final_answer,
                    conversation=task_input.conversation,
                    metadata={
                        "agent_type": self.name,
                        "iterations": iteration + 1,
                        "trace": trace,
                        "tools_used": [t.get("action") for t in trace if "action" in t]
                    }
                )

            if action_name:
                # Execute tool
                trace_entry["action"] = action_name
                trace_entry["action_input"] = action_params

                observation = self._execute_tool(action_name, action_params or {})
                trace_entry["observation"] = observation
                trace.append(trace_entry)

                # Update history for next iteration
                history_text += f"\nThought: {thought}"
                history_text += f"\nAction: {action_name}"
                history_text += f"\nAction Input: {json.dumps(action_params)}"
                history_text += f"\nObservation: {observation}\n"

                if self.verbose:
                    self.logger.info(f"Action: {action_name}")
                    self.logger.debug(f"Observation: {observation[:200]}...")
            else:
                # No valid action or final answer - try to recover
                trace.append(trace_entry)

                # Add a hint for the next iteration
                history_text += f"\nThought: {thought}"
                history_text += "\n[System: Please provide either an Action with Action Input, or a Final Answer]\n"

                self.logger.warning("No valid action or final answer parsed, continuing...")

        # Max iterations reached without final answer
        self.logger.warning(f"ReAct reached max iterations ({self.max_iterations})")

        # Generate a summary from the trace
        summary = self._generate_summary(task_description, trace)

        return TaskOutput(
            success=True,
            result=summary,
            conversation=task_input.conversation,
            metadata={
                "agent_type": self.name,
                "iterations": self.max_iterations,
                "trace": trace,
                "completed": False,
                "reason": "max_iterations_reached"
            }
        )

    def _generate_summary(self, task: str, trace: List[Dict]) -> str:
        """
        Generate a summary when max iterations are reached.

        Args:
            task (str): Original task description
            trace (List[Dict]): Execution trace

        Returns:
            str: Summary of what was accomplished
        """
        # Collect key information from trace
        thoughts = [t.get("thought", "") for t in trace if t.get("thought")]
        observations = [t.get("observation", "") for t in trace if t.get("observation")]

        summary_prompt = f"""Based on the following task and execution trace, provide a comprehensive summary of what was accomplished:

Task: {task}

Key Observations:
{chr(10).join(observations[-3:])}

Please provide a helpful summary response for the user."""

        summary = llm_manager.generate_text(summary_prompt)
        return summary
