"""
SWEAgent: Software Engineering Agent specialized for code-related tasks.

The SWEAgent implements a structured workflow for software engineering:
1. UNDERSTAND - Analyze task requirements and existing code
2. PLAN - Break down implementation into steps
3. IMPLEMENT - Generate or edit code using tools
4. VERIFY - Execute and test the implementation
5. ITERATE - Fix issues based on test results

This agent is optimized for:
- Code generation in multiple languages
- Bug fixing and debugging
- Code refactoring
- Test writing and execution
- File editing and manipulation
"""
from typing import Any, Dict, List, Optional, Tuple
import re
import json

from app.agent.base import BaseAgent
from app.schema import AgentType, TaskInput, TaskOutput
from app.llm import llm_manager
from app.prompt.swe import (
    SWE_SYSTEM_PROMPT,
    SWE_TASK_PROMPT,
    SWE_CODE_GENERATION_PROMPT,
    SWE_TOOL_SELECTION_PROMPT,
    SWE_DEBUG_PROMPT
)


class SWEAgent(BaseAgent):
    """
    Software Engineering agent specialized in code generation and software development tasks.

    Implements the SWE workflow:
    - UNDERSTAND: Analyze requirements and context
    - PLAN: Create implementation plan
    - IMPLEMENT: Execute code generation/editing
    - VERIFY: Run tests and validate
    - ITERATE: Fix issues if needed
    """

    def __init__(
        self,
        tools: Optional[List[str]] = None,
        max_iterations: int = 5,
        auto_execute: bool = True,
        verbose: bool = True
    ):
        """
        Initialize the SWE agent.

        Args:
            tools (List[str], optional): List of tool names to use
            max_iterations (int): Maximum fix iterations for test failures
            auto_execute (bool): Whether to automatically execute generated code
            verbose (bool): Whether to log detailed execution traces
        """
        super().__init__(name=AgentType.SWE.value, tools=tools)
        self.max_iterations = max_iterations
        self.auto_execute = auto_execute
        self.verbose = verbose

        # Define default tools if none provided
        if not tools:
            default_tools = [
                "code_generator",
                "markdown_generator",
                "bash",
                "python_execute",
                "file_saver",
                "str_replace_editor"
            ]
            for tool_name in default_tools:
                self.add_tool(tool_name)

    def _format_tools_description(self) -> str:
        """Format available tools into a description string."""
        tool_descriptions = []
        for tool_name, tool in self.tools.items():
            params_info = ""
            if hasattr(tool, 'parameters') and tool.parameters:
                props = tool.parameters.get('properties', {})
                if props:
                    param_names = list(props.keys())
                    params_info = f" (Parameters: {', '.join(param_names)})"

            tool_descriptions.append(f"- {tool_name}: {tool.description}{params_info}")

        return "\n".join(tool_descriptions)

    def _understand_task(self, task: str) -> Dict[str, Any]:
        """
        Analyze the task to understand requirements.

        Args:
            task (str): Task description

        Returns:
            Dict with task analysis
        """
        prompt = f"""Analyze the following software engineering task and extract key information:

Task: {task}

Please provide:
1. TASK_TYPE: One of [code_generation, bug_fix, refactoring, testing, documentation, other]
2. LANGUAGE: Primary programming language (if applicable)
3. REQUIREMENTS: List of specific requirements
4. COMPLEXITY: One of [simple, moderate, complex]
5. DEPENDENCIES: Any external dependencies or context needed

Format your response as:
TASK_TYPE: [type]
LANGUAGE: [language or "not specified"]
REQUIREMENTS:
- [requirement 1]
- [requirement 2]
COMPLEXITY: [complexity]
DEPENDENCIES: [dependencies or "none"]"""

        response = llm_manager.generate_text(prompt, system_prompt=SWE_SYSTEM_PROMPT)

        # Parse the response
        analysis = {
            "task_type": "code_generation",
            "language": "python",
            "requirements": [],
            "complexity": "moderate",
            "dependencies": []
        }

        # Extract task type
        type_match = re.search(r'TASK_TYPE:\s*(\w+)', response, re.IGNORECASE)
        if type_match:
            analysis["task_type"] = type_match.group(1).lower()

        # Extract language
        lang_match = re.search(r'LANGUAGE:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if lang_match:
            analysis["language"] = lang_match.group(1).strip()

        # Extract complexity
        complex_match = re.search(r'COMPLEXITY:\s*(\w+)', response, re.IGNORECASE)
        if complex_match:
            analysis["complexity"] = complex_match.group(1).lower()

        # Extract requirements
        req_match = re.search(r'REQUIREMENTS:\s*\n((?:[-*]\s*.+\n?)+)', response, re.IGNORECASE)
        if req_match:
            reqs = req_match.group(1)
            analysis["requirements"] = [
                r.strip().lstrip('-*').strip()
                for r in reqs.split('\n')
                if r.strip()
            ]

        return analysis

    def _create_plan(self, task: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Create an implementation plan based on task analysis.

        Args:
            task (str): Original task
            analysis (Dict): Task analysis from _understand_task

        Returns:
            List of implementation steps
        """
        prompt = f"""Create a detailed implementation plan for the following task:

Task: {task}
Task Type: {analysis['task_type']}
Language: {analysis['language']}
Complexity: {analysis['complexity']}

Requirements:
{chr(10).join('- ' + r for r in analysis['requirements'])}

Create a step-by-step plan. Each step should be specific and actionable.
Number each step. Maximum 10 steps.

PLAN:"""

        response = llm_manager.generate_text(prompt, system_prompt=SWE_SYSTEM_PROMPT)

        # Parse plan steps
        steps = []
        for line in response.split('\n'):
            line = line.strip()
            # Match numbered steps like "1.", "1)", "Step 1:", etc.
            if re.match(r'^(\d+[\.\):]|Step\s+\d+)', line, re.IGNORECASE):
                step = re.sub(r'^(\d+[\.\):]|Step\s+\d+:?)\s*', '', line)
                if step:
                    steps.append(step)

        # Fallback: if no numbered steps found, split by sentences
        if not steps:
            steps = [s.strip() for s in response.split('.') if s.strip()][:5]

        return steps[:10]  # Limit to 10 steps

    def _select_tool_for_step(self, step: str, context: str) -> Tuple[str, Dict[str, Any]]:
        """
        Select the appropriate tool for a plan step.

        Args:
            step (str): Plan step description
            context (str): Execution context

        Returns:
            Tuple of (tool_name, parameters)
        """
        tools_desc = self._format_tools_description()

        prompt = SWE_TOOL_SELECTION_PROMPT.format(
            step=step,
            context=context,
            tools=tools_desc
        )

        response = llm_manager.generate_text(prompt, system_prompt=SWE_SYSTEM_PROMPT)

        # Parse tool selection
        tool_match = re.search(r'TOOL:\s*(\w+)', response, re.IGNORECASE)
        params_match = re.search(r'PARAMETERS:\s*(\{.+?\}|\[.+?\])', response, re.IGNORECASE | re.DOTALL)

        tool_name = tool_match.group(1) if tool_match else "code_generator"
        params = {}

        if params_match:
            try:
                params = json.loads(params_match.group(1))
            except json.JSONDecodeError:
                pass

        # Fuzzy match tool name
        for available_tool in self.tools.keys():
            if tool_name.lower() == available_tool.lower():
                return available_tool, params
            elif tool_name.lower() in available_tool.lower():
                return available_tool, params

        # Default to code_generator
        return "code_generator", params

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with parameters.

        Args:
            tool_name (str): Tool name
            params (Dict): Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found", "success": False}

        tool = self.tools[tool_name]

        try:
            self.logger.debug(f"Executing tool '{tool_name}' with params: {params}")
            result = tool.safe_run(**params)

            if isinstance(result, dict):
                result["success"] = result.get("success", "error" not in result)
            else:
                result = {"result": str(result), "success": True}

            return result

        except Exception as e:
            self.logger.error(f"Tool execution error: {str(e)}")
            return {"error": str(e), "success": False}

    def _verify_implementation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify the implementation by running tests or executing code.

        Args:
            context (Dict): Execution context with generated code/files

        Returns:
            Verification result
        """
        verification = {
            "success": True,
            "output": "",
            "errors": []
        }

        # If we have generated Python code and auto_execute is enabled
        if self.auto_execute and "python_execute" in self.tools:
            code = context.get("generated_code", "")
            language = context.get("language", "").lower()

            if code and language in ["python", "py"]:
                self.logger.info("Auto-executing generated Python code for verification")

                result = self._execute_tool("python_execute", {"code": code})

                if result.get("success"):
                    verification["output"] = result.get("result", result.get("output", ""))
                else:
                    verification["success"] = False
                    verification["errors"].append(result.get("error", "Execution failed"))

        return verification

    def _iterate_on_errors(
        self,
        task: str,
        context: Dict[str, Any],
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        Attempt to fix errors in the implementation.

        Args:
            task (str): Original task
            context (Dict): Current execution context
            errors (List[str]): List of errors to fix

        Returns:
            Updated context with fixes
        """
        code = context.get("generated_code", "")
        language = context.get("language", "python")

        prompt = SWE_DEBUG_PROMPT.format(
            language=language,
            code=code,
            error="\n".join(errors)
        )

        response = llm_manager.generate_text(prompt, system_prompt=SWE_SYSTEM_PROMPT)

        # Extract fixed code from response
        code_match = re.search(r'```(?:\w+)?\s*\n(.+?)\n```', response, re.DOTALL)
        if code_match:
            fixed_code = code_match.group(1)
            context["generated_code"] = fixed_code
            context["fix_applied"] = True
            context["fix_explanation"] = response

        return context

    def _run(self, task_input: TaskInput) -> TaskOutput:
        """
        Execute the SWE agent with the given task input.

        Implements the full SWE workflow:
        UNDERSTAND -> PLAN -> IMPLEMENT -> VERIFY -> ITERATE

        Args:
            task_input (TaskInput): Task input containing the task description

        Returns:
            TaskOutput: Task output with result and artifacts
        """
        task_description = task_input.task_description
        self.logger.info(f"SWE agent received task: {task_description}")

        # Execution context
        context = {
            "task": task_description,
            "generated_code": "",
            "generated_files": [],
            "language": "python",
            "execution_trace": []
        }

        # Phase 1: UNDERSTAND
        self.logger.info("Phase 1: UNDERSTAND - Analyzing task")
        analysis = self._understand_task(task_description)
        context["analysis"] = analysis
        context["language"] = analysis.get("language", "python")
        context["execution_trace"].append({
            "phase": "UNDERSTAND",
            "result": analysis
        })

        if self.verbose:
            self.logger.debug(f"Task analysis: {analysis}")

        # Phase 2: PLAN
        self.logger.info("Phase 2: PLAN - Creating implementation plan")
        plan = self._create_plan(task_description, analysis)
        context["plan"] = plan
        context["execution_trace"].append({
            "phase": "PLAN",
            "result": plan
        })

        if self.verbose:
            self.logger.debug(f"Implementation plan: {plan}")

        # Phase 3: IMPLEMENT
        self.logger.info("Phase 3: IMPLEMENT - Executing plan steps")
        step_results = []

        for i, step in enumerate(plan):
            self.logger.info(f"Executing step {i + 1}/{len(plan)}: {step[:50]}...")

            # Select tool for this step
            tool_name, params = self._select_tool_for_step(
                step,
                json.dumps(context.get("analysis", {}))
            )

            # Add task context to params if using code_generator
            if tool_name == "code_generator" and "description" not in params:
                params["description"] = step
                if context["language"] and context["language"] != "not specified":
                    params["language"] = context["language"]

            # Execute tool
            result = self._execute_tool(tool_name, params)
            step_results.append({
                "step": step,
                "tool": tool_name,
                "params": params,
                "result": result
            })

            # Update context with results
            if result.get("success"):
                if "content" in result:
                    context["generated_code"] = result["content"]
                if "artifact_path" in result:
                    context["generated_files"].append(result["artifact_path"])

        context["step_results"] = step_results
        context["execution_trace"].append({
            "phase": "IMPLEMENT",
            "result": step_results
        })

        # Phase 4: VERIFY
        self.logger.info("Phase 4: VERIFY - Testing implementation")
        verification = self._verify_implementation(context)
        context["verification"] = verification
        context["execution_trace"].append({
            "phase": "VERIFY",
            "result": verification
        })

        # Phase 5: ITERATE (if needed)
        iteration = 0
        while not verification["success"] and iteration < self.max_iterations:
            iteration += 1
            self.logger.info(f"Phase 5: ITERATE - Fixing errors (attempt {iteration})")

            context = self._iterate_on_errors(
                task_description,
                context,
                verification["errors"]
            )

            # Re-verify
            verification = self._verify_implementation(context)
            context["verification"] = verification
            context["execution_trace"].append({
                "phase": f"ITERATE_{iteration}",
                "result": verification
            })

        # Generate final summary
        summary = self._generate_summary(context)

        return TaskOutput(
            success=verification["success"] or len(context["generated_files"]) > 0,
            result=summary,
            conversation=task_input.conversation,
            metadata={
                "agent_type": self.name,
                "analysis": context["analysis"],
                "plan": context["plan"],
                "generated_files": context["generated_files"],
                "verification": context["verification"],
                "iterations": iteration
            }
        )

    def _generate_summary(self, context: Dict[str, Any]) -> str:
        """
        Generate a summary of the SWE execution.

        Args:
            context (Dict): Execution context

        Returns:
            Summary string
        """
        analysis = context.get("analysis", {})
        plan = context.get("plan", [])
        verification = context.get("verification", {})
        files = context.get("generated_files", [])

        summary_parts = []

        # Task summary
        summary_parts.append(f"## Task Analysis")
        summary_parts.append(f"- Type: {analysis.get('task_type', 'N/A')}")
        summary_parts.append(f"- Language: {analysis.get('language', 'N/A')}")
        summary_parts.append(f"- Complexity: {analysis.get('complexity', 'N/A')}")

        # Plan summary
        summary_parts.append(f"\n## Implementation Plan")
        for i, step in enumerate(plan, 1):
            summary_parts.append(f"{i}. {step}")

        # Generated files
        if files:
            summary_parts.append(f"\n## Generated Files")
            for f in files:
                summary_parts.append(f"- {f}")

        # Verification status
        summary_parts.append(f"\n## Verification")
        if verification.get("success"):
            summary_parts.append("Status: SUCCESS")
            if verification.get("output"):
                summary_parts.append(f"Output: {verification['output'][:500]}")
        else:
            summary_parts.append("Status: NEEDS REVIEW")
            if verification.get("errors"):
                summary_parts.append(f"Issues: {', '.join(verification['errors'][:3])}")

        # Generated code preview
        code = context.get("generated_code", "")
        if code:
            summary_parts.append(f"\n## Generated Code Preview")
            preview = code[:500] + "..." if len(code) > 500 else code
            summary_parts.append(f"```{context.get('language', '')}\n{preview}\n```")

        return "\n".join(summary_parts)
