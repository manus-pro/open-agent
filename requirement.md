```markdown
# Python Agent Requirements and Implementation Guide

## Overview
This Python Agent is a modular and extensible system designed to autonomously or semi-autonomously execute various tasks. The agent leverages an LLM (e.g., OpenAI) and tools orchestrated via the LangChain framework to:
- Generate PDFs
- Generate Markdown files
- Create code base artifacts
- Execute browser tasks using Selenium
- Conduct web research using the Firecrawl API

The design draws inspiration from the modularity and multi-modal task execution of the [Owl Project](https://github.com/camel-ai/owl.git) and [OpenManus](https://github.com/mannaandpoem/OpenManus). This project has been refactored into **OpenAgent**.

---

## Functional Requirements

1. **Task Interpretation**
   - Interpret natural language descriptions provided by users.
   - Utilize an LLM (e.g., OpenAI API) to parse tasks and determine the required actions.

2. **Document Generation**
   - **PDF Generation:** Convert text or data into a PDF file with basic formatting using libraries like `reportlab`.
   - **Markdown Generation:** Create Markdown files from text/data and save them to specified paths.

3. **Code Base Artifact Generation**
   - Generate Python scripts or modules based on task descriptions or research findings.
   - Ensure the generated code is functional and stored at a designated location.

4. **Browser Task Execution**
   - Automate browser tasks such as navigating web pages, clicking elements, or filling forms using Selenium.
   - Optionally, use the LLM to generate specific Selenium actions for complex workflows.

5. **Web Research with Firecrawl API**
   - Conduct research by crawling websites with the Firecrawl API.
   - Retrieve clean Markdown or structured data from the crawled content for further processing.

---

## Non-Functional Requirements

- **Modularity and Extensibility**
  - Structure the agent with separate components for each task (e.g., document generation, code generation, browser automation, research).
  - Ensure new tools and functionalities can be easily integrated.

- **Security**
  - Handle API keys and sensitive data securely via environment variables.
  - Avoid executing arbitrary code in production environments; use sandboxing or predefined actions.

- **Performance and Robustness**
  - Ensure efficient processing, even when handling large datasets.
  - Implement robust error handling for API failures and invalid inputs.

---

## File Structure Considerations

The following directory structure is suggested to maintain a clear separation of concerns, inspired by [OpenManus](https://github.com/mannaandpoem/OpenManus):

```
└── open-agent/
    ├── README.md
    ├── LICENSE
    ├── README_zh.md
    ├── main.py
    ├── requirements.txt
    ├── run_flow.py
    ├── setup.py
    ├── .pre-commit-config.yaml
    ├── app/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── exceptions.py
    │   ├── llm.py
    │   ├── logger.py
    │   ├── schema.py
    │   ├── agent/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── manus.py
    │   │   ├── planning.py
    │   │   ├── react.py
    │   │   ├── swe.py
    │   │   └── toolcall.py
    │   ├── flow/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── flow_factory.py
    │   │   └── planning.py
    │   ├── prompt/
    │   │   ├── __init__.py
    │   │   ├── manus.py
    │   │   ├── planning.py
    │   │   ├── swe.py
    │   │   └── toolcall.py
    │   └── tool/
    │       ├── __init__.py
    │       ├── base.py
    │       ├── bash.py
    │       ├── browser_use_tool.py
    │       ├── create_chat_completion.py
    │       ├── file_saver.py
    │       ├── google_search.py
    │       ├── planning.py
    │       ├── python_execute.py
    │       ├── run.py
    │       ├── str_replace_editor.py
    │       ├── terminate.py
    │       └── tool_collection.py
    ├── assets/
    └── config/
        └── config.example.toml
```

This structure ensures that:
- **Agent logic** is organized under `app/agent`.
- **Flow and orchestration** logic resides in `app/flow`.
- **Prompt templates** and configurations are under `app/prompt`.
- **Tools and integrations** are maintained in `app/tool`.
- **Configuration files and assets** are isolated for easy management.

---

## Step-by-Step Implementation Plan

### Step 1: Environment Setup
- **Install Required Libraries**
  ```bash
  pip install langchain openai firecrawl selenium reportlab
  ```
- **Set Up API Keys**
  ```bash
  export OPENAI_API_KEY="your_openai_key"
  export FIRECRAWL_API_KEY="your_firecrawl_key"
  ```
- **Install Web Driver**
  - Download and configure a compatible web driver (e.g., ChromeDriver) for Selenium.

### Step 2: Define Tools
- **Firecrawl Research Tool**
  - Crawl a website using the Firecrawl API and return Markdown content.
- **PDF Generation Tool**
  - Use `reportlab` to convert text input into a PDF file.
- **Markdown Generation Tool**
  - Create and save Markdown files from given text.
- **Code Generator Tool**
  - Generate Python scripts or modules using an LLM based on task descriptions.
- **Browser Task Tool**
  - Automate browser actions using Selenium for tasks like navigation and form submissions.

### Step 3: Integrate Tools with the LangChain Agent
- **LLM Initialization**
  - Use the OpenAI API via LangChain to initialize the LLM.
- **Tool Registration**
  - Register all the tools (research, PDF, Markdown, code, browser) with the LangChain agent.
- **Agent Setup**
  - Configure the agent (e.g., using `AgentType.ZERO_SHOT_REACT_DESCRIPTION`) for task interpretation and execution.

### Step 4: Task Execution Flow
- **User Input**
  - Accept natural language task descriptions.
- **Task Parsing**
  - Utilize the LLM to interpret and break down the task into actionable steps.
- **Sequential Processing**
  - Allow for multi-step tasks, e.g., research a URL, generate Markdown, then produce a PDF report.
- **Logging and Debugging**
  - Provide detailed logging for debugging and task tracking.

### Step 5: Testing and Validation
- **Unit Testing**
  - Validate each tool individually (e.g., test PDF generation with sample text).
- **Integration Testing**
  - Execute complete workflows that span multiple tools.
- **Error Handling**
  - Incorporate robust error handling to manage API failures and unexpected inputs.

### Step 6: Documentation and Maintenance
- **Comprehensive README**
  - Include setup instructions, usage examples, and directory structure details.
- **Inline Documentation**
  - Comment code thoroughly to assist future development and troubleshooting.
- **Security Reviews**
  - Regularly update security practices, especially concerning API key management and dynamic code execution.

---

## References

- [Owl Project on GitHub](https://github.com/camel-ai/owl.git)
- [OpenManus Project on GitHub](https://github.com/mannaandpoem/OpenManus)

---

python env is created by uv and use
```
uv pip install ...
```