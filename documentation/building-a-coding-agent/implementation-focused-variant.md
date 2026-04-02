# Building a Coding Agent from Scratch

A Comprehensive Guide to Building Local LLM-Powered AI Coding Assistants

---

## Table of Contents

1. [Introduction and Executive Summary](#introduction-and-executive-summary)
2. [Minimal Architecture Overview](#minimal-architecture-overview)
3. [Terminal User Interface Implementation](#terminal-user-interface-implementation)
4. [Tool Calling Loop Implementation](#tool-calling-loop-implementation)
5. [Model Context Protocol Integration](#model-context-protocol-integration)
6. [File Editing at Arbitrary Positions](#file-editing-at-arbitrary-positions)
7. [Error Recovery and Hallucination Protection](#error-recovery-and-hallucination-protection)
8. [Vision Capabilities and Local LLM Integration](#vision-capabilities-and-local-llm-integration)
9. [Structured Output and JSON Schema Enforcement](#structured-output-and-json-schema-enforcement)
10. [Getting Started and Minimal Implementation](#getting-started-and-minimal-implementation)

---
# Chapter 1: Introduction and Executive Summary

Building a coding agent from scratch is one of the most ambitious software engineering projects you can undertake. It sits at the intersection of several complex domains: natural language understanding, program analysis, file system operations, terminal interfaces, and the delicate art of error handling when things inevitably go wrong. This comprehensive guide will walk you through everything you need to know to build a minimal but functional coding agent using a local LLM with vision capabilities.

The landscape of AI coding assistants has evolved dramatically in recent years. Tools like Claude Code, Aider, OpenCode, and Cursor have demonstrated that local AI agents can be surprisingly capable partners in software development. They can read your codebase, suggest edits, run tests, fix bugs, and even tackle large projects like writing an operating system. What makes them work is not magic but a carefully orchestrated combination of several key components working in harmony.

At its core, a coding agent is a loop that looks deceptively simple. The model receives a user request along with context about the codebase. It reasons about what needs to be done and decides which tools to use. The tools execute actions like reading files, running commands, or making edits. The results of those actions feed back into the model, which then decides what to do next. This cycle repeats until the task is complete or the user intervenes. This ReAct pattern, standing for Reason and Act, forms the backbone of most modern coding agents.

What sets good agents apart from bad ones is not the sophistication of their orchestration but the quality of their individual components and how well they handle the messy reality of working with code and file systems. File paths change. Commands fail with cryptic error messages. The model might hallucinate a tool that does not exist or produce malformed output that breaks the parsing logic. Your agent needs to recover from all of these failures gracefully, or at minimum, fail safely and provide clear feedback to the user about what went wrong.

This guide assumes you want to build something minimal that actually works. You do not need to replicate every feature of Claude Code or Aider on day one. You need a working loop that can read files, make edits, run commands, and recover from errors. You need a terminal interface that shows you what the agent is doing and lets you intervene when necessary. You need confidence that when the agent edits your code, it does so reliably and the changes are what you expected.

The approach outlined here prioritizes working code over theoretical elegance. We will use Python because it is good enough for all the components you need: the terminal interface, the LLM client, the tool executor, and even the MCP integration. We will leverage existing libraries wherever possible rather than reinventing the wheel. And we will focus on the patterns that have been proven to work in production coding agents.

By the end of this guide, you will have a complete mental model of how a coding agent works from the inside out. You will understand the tradeoffs between different approaches to file editing, the mechanics of structured output generation, and the strategies for error recovery that keep your agent from spinning in infinite loops of failure. Most importantly, you will have the knowledge to start building your own agent with confidence that you are making the right architectural decisions from the beginning.


---

# Chapter 2: Minimal Architecture Overview

The most important architectural decision you will make when building a coding agent is to keep it simple. After analyzing the architectures of leading coding agents including Claude Code, Aider, OpenCode, and Cursor, a clear pattern emerges. The most effective agents follow what is known as the `while(tool_call)` loop pattern, a minimal architecture that trusts the model to make the right decisions rather than trying to build complex orchestration systems around it.

Claude Code represents perhaps the purest expression of this philosophy. It implements a loop with no intent classifier, no task router, no RAG pipeline, no directed acyclic graph orchestrator, and no planner-executor split. The model itself decides everything. The architecture looks like this: while the response contains a tool call, execute that tool call and send the result back to the model. When no more tool calls are needed, return the final text response. This simplicity is not accidental. It reflects a fundamental insight that the model's native reasoning capabilities are often better than any hand-crafted orchestration logic you might build.

The core components of a minimal coding agent are straightforward. You need a tool layer that exposes capabilities like reading files, writing files, executing shell commands, searching the codebase, and managing a task list. You need a context manager that tracks the conversation history along with all the tool results and enforces a token budget. You need a mechanism for session persistence that allows the user to resume interrupted work. And you need a terminal user interface that displays what the agent is doing and lets the user provide input or intervene.

The tool layer in a minimal implementation should include at least eight core tools. A bash tool for executing shell commands is essential for running tests, compiling code, or invoking development tools. A read tool for viewing file contents allows the model to understand the codebase. A write tool for creating or replacing files is necessary for adding new code or making significant changes. An edit tool for performing SEARCH and REPLACE operations on existing files is more token-efficient for incremental changes. A grep tool for text searching across the codebase helps the model find relevant code. A glob tool for file pattern matching helps discover files. A task tool for creating sub-agents with isolated context helps handle multi-step problems. And a todo list tool for tracking progress on complex tasks helps maintain organization across long sessions.

Context management is where many coding agents fail. You must track a shared token budget that spans the system prompt, the conversation history, all tool results, and the response buffer. When the budget is approaching its limit, you must implement compaction strategies. Auto-compaction that triggers when the context reaches between 75 and 92 percent capacity is common, but you must be aware that quality degrades significantly when compaction happens repeatedly. A better approach is to implement manual compaction commands that users can trigger at logical breakpoints, and to warn users when the context is getting large so they can take action before quality drops.

Session persistence is another critical component that is often overlooked. Users expect to be able to interrupt an agent session and resume it later. Session files stored in a hidden directory like dot claude store the conversation history, tool call results, session metadata, and the working directory. When a user resumes a session, the agent reloads this state and continues from where it left off. This persistence layer must be robust enough to handle crashes and incomplete sessions, and it must not persist live tool states or file locks that could cause problems on resume.

The terminal user interface should be built using Textual, a modern Python TUI framework that provides reactive programming patterns, CSS-like styling, and built-in widgets for all the interaction patterns you need. Textual integrates Rich for rendering, which means you get syntax highlighting for code, colored output for logs, and proper diff display without writing any of the low-level rendering logic yourself. The interface should display the agent's thinking process, the tools it is calling, and their results in real time. It should provide keyboard shortcuts for common actions and a command palette for discoverable features.

For long-term tasks like writing an operating system or performing extensive testing, you need mechanisms beyond the basic loop. Sub-agents with depth one isolation allow the model to spawn child sessions with their own context for tackling specific sub-problems. The parent agent maintains the overall plan while the child agents work on their assigned tasks. Repository maps provide efficient codebase context without token exhaustion. These maps use graph ranking algorithms on the file dependency graph to select the most important code portions that fit within a token budget, typically around one thousand tokens by default.

The architecture should also support the Model Context Protocol for extensibility. MCP allows external tools and data sources to be integrated into the agent through a standardized protocol. You can implement MCP servers that expose custom tools, and the agent can discover and use those tools dynamically. This extensibility is important for production systems where you might want to add tools for interacting with databases, cloud services, or other external systems.

Error handling must be built into every layer of the architecture. When a tool call fails, the error message should be formatted in a way that the model can understand and use to recover. This means including the command that was run, the output that was produced, and suggestions for what might have gone wrong. When the model hallucinates a tool that does not exist, the agent should report the error clearly and provide the list of available tools so the model can try again with valid tool names. When the model produces malformed output, validation layers should catch the error and trigger retries with corrected prompts.

Python is more than adequate for implementing all of these components. The Textual library provides the TUI capabilities you need. The Ollama or vLLM Python SDKs handle LLM communication. The subprocess module handles shell command execution. The pathlib module handles file operations. The MCP Python SDK handles protocol integration. And libraries like Instructor, Tenacity, and pybreaker handle structured output, retry logic, and circuit breaker patterns. You do not need to use multiple languages or introduce unnecessary complexity. Python is the right tool for this job.

The complete minimal architecture can be visualized as a set of interconnected modules. The TUI module handles all user interaction and displays output using Textual and Rich. The LLM client module communicates with your local inference server using the Ollama or vLLM API. The tool executor module implements the core tools and handles their execution. The context manager module tracks token usage and implements compaction strategies. The session manager module handles persistence and resume capability. The MCP client module integrates external tools through the Model Context Protocol. And the error handler module implements retry logic, validation, and recovery patterns across all components.

This architecture is minimal but complete. It provides all the functionality you need to build a coding agent that works reliably for both short interactions and long-term tasks. The key is to implement each component carefully with attention to error handling and user feedback. When you get the architecture right, the agent becomes a powerful partner that can help you write code, fix bugs, and tackle projects that would be overwhelming to handle alone.


---

# Chapter 3: Terminal User Interface Implementation

The terminal user interface is your agent's face to the world. It is where users interact with the system, where they watch the agent think and act, and where they provide input and intervention when needed. A well-designed TUI transforms a technical tool into a usable product. The bad news is that building TUIs in Python has historically been difficult. The good news is that modern libraries have made this dramatically easier while maintaining full power and flexibility.

Textual is unequivocally the best choice for building a coding agent interface. With over 35,000 GitHub stars and active development by the same team behind Rich, Textual combines modern web development patterns with powerful terminal capabilities. It provides a DOM-like widget architecture, CSS-like styling through TCSS, reactive programming with var and watch methods, and runs on asyncio for non-blocking operations. Textual can even render in a web browser, providing future-proofing as your application evolves. The real validation comes from the fact that Toad, built by Textualize founder Will McGugan himself, is a unified interface for AI coding tools including Claude Code, OpenHands, and Gemini CLI.

The foundation of your TUI will be Textual with Rich for rendering. Rich handles all the low-level formatting work including syntax highlighting, tables, progress bars, and styled text. Textual provides the interactive widgets and event handling. When combined, you get a professional-grade interface without writing any terminal escape sequence code yourself.

Start by setting up the basic application structure. Textual apps inherit from the App class and implement a compose method that yields widgets. For a coding agent, you will want a vertical scroll container for the chat history, an input field at the bottom for user commands, and a status bar showing context information like token usage and session state.

For chat history with keyboard navigation, you need to implement a custom message widget that renders both user and assistant messages with appropriate styling. User messages should be highlighted in blue or another distinctive color, while assistant messages use green. Each message widget should be added to the chat container as a child and automatically scrolled into view.

Keyboard navigation through command history requires maintaining a list of previous commands and using the up and down arrow keys to cycle through them. When the user presses up on an empty input, load the previous command. When they press down, go to the next command or clear the input if at the end of history.

For persistent history that survives application restarts, integrate with prompt_toolkit's FileHistory class. This provides file-based storage with built-in search functionality and supports the same up and down navigation pattern.

Diff display is essential for code review workflows. When the agent suggests file edits, users need to see exactly what changes will be made before accepting them. Rich provides excellent diff rendering through its Syntax class with lexer set to diff. You can generate unified diff output using Python's built-in difflib module and display it with syntax highlighting.

For live terminal output streaming, Textual provides the RichLog widget which is designed specifically for this purpose. RichLog automatically scrolls to show new content, supports Rich styling, and handles buffering efficiently. You can write log messages from any asyncio task and they will appear in real time in the terminal.

The command palette feature in Textual provides a discoverable interface for all available commands. This is especially useful for users who do not know about keyboard shortcuts. You can register custom commands and they will appear automatically in the command palette.

Status information is critical for user awareness. You should display token usage, context window percentage, current tool being executed, and any warnings about approaching limits. Textual widgets can be reactive, updating automatically when the underlying data changes.

For mouse support, Textual automatically handles click events on widgets. You can add click handlers to message widgets to enable features like expanding collapsed tool output or reopening diff previews.

The complete TUI for a coding agent integrates all these components into a cohesive interface. Messages appear in the scrollable chat container, the input field at the bottom accepts user commands, RichLog displays streaming tool output, and the status bar shows context information. Keyboard shortcuts provide quick access to common operations, and the command palette makes features discoverable. With Textual, you get all this with a clean API that does not require you to become a terminal graphics expert.


---

# Chapter 4: Tool Calling Loop Implementation

The tool calling loop is the beating heart of your coding agent. It is the ReAct pattern in action: the model reasons about the current state, decides which tool to call, executes that tool, observes the result, and repeats until the task is complete. This loop is simpler than it sounds, but it requires careful implementation to handle edge cases, failures, and the reality that models sometimes produce malformed output or call tools that do not exist.

Start by defining your available tools. A minimal coding agent needs at least eight core tools that cover the essential operations of code development. The bash tool executes shell commands and is essential for running tests, building code, or invoking development tools. The read tool displays file contents so the model can understand the codebase. The write tool creates or completely replaces files for adding new code or making significant changes. The edit tool performs SEARCH and REPLACE operations on existing files, which is more token-efficient for incremental changes. The grep tool searches for text patterns across the codebase to find relevant code. The glob tool matches file patterns to discover files in directories. The task tool creates sub-agents with isolated context for handling multi-step problems. And the todo list tool tracks progress on complex tasks to maintain organization.

Each tool must have a clear description and a well-defined input schema. The description is how the model understands when to use the tool. It should be concise but specific about what the tool does and when it is appropriate to use it. The input schema defines the parameters the tool accepts. Use JSON schema or Pydantic models to specify types, required fields, and descriptions for each parameter. The model uses this schema to generate valid tool calls.

Tool definitions should include examples when possible. Adding usage examples to tool schemas improves parameter handling accuracy from 72 percent to 90 percent according to benchmark testing. Examples show the model exactly what valid inputs look like and help it understand the expected format. This is especially important for tools with complex parameters or tools that have multiple ways of being used.

The loop itself follows a straightforward pattern. First, prepare the messages list with the system prompt, conversation history, and any tool results from previous iterations. Then send the messages to the model with the list of available tools. Parse the model response to extract any tool calls. If tool calls are present, execute each one and format the results. Add the tool results back to the messages list and repeat. If no tool calls are present, extract the final text response and return it to the user.

```python
class ToolExecutor:
    def __init__(self, available_tools: Dict[str, Callable]):
        self.tools = available_tools
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {list(self.tools.keys())}"
        try:
            result = await self.tools[tool_name](**arguments)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
```

Structured output enforcement is critical for reliable tool calling. You have several options depending on your LLM and infrastructure. The Instructor library provides a unified interface across Ollama, vLLM, and many other providers. It uses Pydantic models to define expected output formats and automatically retries with corrected prompts when validation fails. This approach works well because it does not require special model support and handles edge cases like malformed JSON gracefully.

Ollama provides native JSON schema support through the format parameter. When you pass a JSON schema to the format parameter, Ollama constrains the model output to match that schema. This is more efficient than Instructor because the constraint is applied at the token level rather than through retries. However, it requires using Ollama specifically and works best with models that have been fine-tuned for structured output.

vLLM supports structured outputs through its structured_outputs parameter. You can specify JSON schema, regex patterns, or a set of choices. The implementation uses token masking to guarantee the output follows the specified format. Like Ollama, this approach is more efficient than retry-based validation but requires specific infrastructure setup.

When using Instructor with Ollama, the integration looks like this. First, install the library with pip install instructor ollama pydantic. Then create a client configured for your provider. Define a Pydantic model for the tool call structure with fields for tool name and arguments. Call the client with your messages and specify the response model. Instructor handles validation and retries automatically, returning a validated Pydantic model or raising an error after exhausting retries.

```python
import instructor
from pydantic import BaseModel, Field
from typing import List, Optional
from ollama import chat

client = instructor.from_provider(
    "ollama/qwen2.5vl:7b",
    mode=instructor.Mode.JSON,
)

class ToolCall(BaseModel):
    tool_name: str = Field(..., description="Name of tool to call")
    arguments: dict = Field(..., description="Arguments for the tool")

class AgentResponse(BaseModel):
    thoughts: str = Field(..., description="Reasoning about what to do")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools to execute")
    final_response: Optional[str] = Field(default=None, description="Final answer if no tools needed")

response = client.chat.completions.create(
    model="qwen2.5vl:7b",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant with access to tools."},
        {"role": "user", "content": "Read the file main.py"}
    ],
    response_model=AgentResponse,
    max_retries=3,
    timeout=60.0,
)
```

Error handling must be built into every level of the tool calling loop. At the schema validation level, Instructor will retry when the output does not match the Pydantic model. At the tool execution level, catch exceptions and return error messages that the model can understand. At the loop level, implement a maximum iteration limit to prevent infinite loops when the model keeps requesting tools without making progress.

When a tool call fails, format the error message so the model can learn from it. Include the command that was run, the output that was produced, and the type of error that occurred. For example, if a bash command fails with permission denied, include the command, the stderr output, and a note about permissions. This contextual information helps the model understand what went wrong and try a different approach.

When the model hallucinates a tool that does not exist, the error message should clearly list the available tools. This is different from a tool execution error because it indicates the model does not know what tools it has access to. Include the full tool definitions with descriptions so the model can update its understanding.

Token counting and budget management is essential for production use. Track tokens used by the system prompt, each message in the conversation, tool results, and the response buffer. When approaching the budget limit, implement compaction strategies. Auto-compaction that triggers at 85 percent is safer than waiting until 95 percent because it preserves more quality. But warn users when the context is getting large so they can manually trigger compaction or start a new session.

The loop should also track iteration count and implement a maximum iteration limit. Complex tasks might require many tool calls, but endless loops usually indicate a problem. A typical limit is 50 to 100 iterations. When the limit is reached, inform the user that the task is incomplete and suggest manual intervention.

For sub-agent tasks, implement depth-based isolation. When the task tool is used, create a new session with its own context. Limit sub-agent depth to one level to prevent runaway context growth. The sub-agent reports back to the parent when complete, and the parent incorporates the results into its ongoing work.


---

# Chapter 5: Model Context Protocol Integration

The Model Context Protocol, or MCP, is an open standard that enables seamless integration between AI applications and external data sources, tools, and capabilities. Think of MCP as a USB-C port for AI applications. Just as USB-C standardizes how hardware devices connect to computers, MCP standardizes how AI models connect to the context they need to perform tasks effectively. This standardization is transformative because it means you can build one client that works with any MCP server, and one server that works with any MCP client.

MCP uses a client-server architecture with JSON-RPC 2.0 messaging. The host application, which is your coding agent in this case, acts as the MCP client. It initiates connections to MCP servers that provide tools, resources, and prompts. The protocol supports both local communication through STDIO for servers that run as child processes, and remote communication through Streamable HTTP for network-accessible services. The latest specification from November 2025 adds OAuth 2.1 support, enhanced security features, and improved server capabilities.

The protocol defines three main types of server capabilities. Tools are functions that the AI can execute to perform actions like reading files, running commands, or querying databases. Resources provide context and data that the AI can read but not modify, such as file contents, database records, or external API responses. Prompts are templated messages that standardize how the AI should interact with certain capabilities, providing consistent workflows for common tasks.

To create an MCP server for your coding agent, start with the Python FastMCP library. FastMCP provides a simple decorator-based API for defining tools, resources, and prompts. You can install it with pip install mcp and begin building servers immediately.

### Creating MCP Servers

The Python SDK provides FastMCP which uses decorators to define tools. Here is the pattern for defining a file reading tool:

```python
from mcp.server.fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("File System Tools")

@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file with path validation."""
    allowed_dirs = [Path("/home/user/projects")]
    file_path = Path(path).resolve()
    
    for allowed in allowed_dirs:
        try:
            file_path.relative_to(allowed)
            with open(file_path, 'r') as f:
                return f.read()
        except ValueError:
            continue
    raise ValueError(f"Access denied: path outside allowed directories")

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

The key elements are the decorator, the docstring for the tool description, and input validation for security. Path validation prevents directory traversal attacks by checking that the resolved path is within allowed directories.

### Creating MCP Clients

To integrate MCP into your coding agent, create a client that connects to servers and manages tool discovery:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.session = None
        self.tools = {}
    
    async def connect_to_server(self, server_script_path: str):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                for tool in response.tools:
                    self.tools[tool.name] = tool
                print(f"Connected. Available tools: {[t.name for t in response.tools]}")
    
    async def call_tool(self, name: str, arguments: dict):
        response = await self.session.call_tool(name, arguments)
        return response.content
```

### Unified Tool Registry

Combine MCP tools with built-in tools using a unified registry:

```python
class UnifiedToolRegistry:
    def __init__(self):
        self.built_in_tools = {}
        self.mcp_clients = []
    
    def register_builtin(self, name: str, tool):
        self.built_in_tools[name] = tool
    
    def register_mcp_client(self, client):
        self.mcp_clients.append(client)
    
    async def list_all_tools(self):
        tools = []
        for name, tool in self.built_in_tools.items():
            tools.append({"name": name, "source": "builtin"})
        for client in self.mcp_clients:
            tools.extend([{"name": t.name, "source": "mcp"} for t in client.tools.values()])
        return tools
    
    async def execute_tool(self, name: str, source: str, arguments: dict):
        if source == "builtin":
            return await self.built_in_tools[name](**arguments)
        elif source == "mcp":
            for client in self.mcp_clients:
                if name in client.tools:
                    return await client.call_tool(name, arguments)
        raise ValueError(f"Tool not found: {name}")
```

### Security Considerations

Security is critical for MCP servers that handle file system and shell access. Implement path validation to prevent directory traversal attacks. Use command whitelisting to restrict which shell commands can execute. Require user consent for high-risk actions before execution. All security controls should be at the server level, not delegated to clients or LLMs.

### Lazy Loading

MCP supports lazy loading for large tool sets through tool search patterns. Load only matching tools on demand to reduce context overhead by up to 85 percent. The client first queries a search tool, then loads matched tools as needed.

MCP provides a standardized way to extend your coding agent with custom tools and external capabilities. By building around this protocol, you gain compatibility with the growing ecosystem of MCP servers and the ability to integrate new features without modifying core agent code.


---

# Chapter 6: File Editing at Arbitrary Positions

One of the most critical capabilities for a coding agent is the ability to edit files at any position, not just at the beginning or end. When an agent suggests a code change, it typically needs to insert a function in the middle of a file, modify a specific class method, or replace a single line in a block of code. Naive approaches that only append or prepend text are completely insufficient for real software development work. This chapter covers the patterns and techniques that enable reliable file editing at arbitrary positions.

The SEARCH and REPLACE block pattern is the most widely used approach in coding agents. This pattern uses a format similar to git merge conflict markers to identify both the code to find and the code to replace it with. The format looks like this: two angle brackets and SEARCH at the top, followed by the original code. Then two angle brackets and REPLACE at the bottom, followed by the new code. The agent searches for the SEARCH block in the file and replaces it with the REPLACE block. This approach is used by Aider, Cline, RooCode, and many other tools.

The accuracy of SEARCH and REPLACE blocks depends heavily on file size and code complexity. For small files under 100 lines, accuracy reaches 85 percent. For medium files between 100 and 300 lines, accuracy drops to 75 percent. For large files over 300 lines, accuracy falls to 60 percent. When there are multiple similar patterns in the file, accuracy can drop as low as 40 percent because the model might match the wrong occurrence. These limitations are why many production systems layer multiple matching strategies.

Layered matching starts with exact string matching. If the SEARCH block matches exactly, apply the replacement immediately. If not, try whitespace-insensitive matching where extra spaces or tabs are ignored. If that fails, try indentation-preserving matching where line structure is maintained but exact spacing varies. As a last resort, try fuzzy matching using difflib or similar libraries. Each failed attempt should provide detailed error feedback to the model showing what actually matched versus what was expected, enabling the model to adjust its SEARCH block on retry.

```python
import difflib

class SearchReplaceEditor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        with open(file_path, 'r') as f:
            self.content = f.read()
    
    def find_exact_match(self, search_block: str) -> tuple:
        start = self.content.find(search_block)
        if start >= 0:
            end = start + len(search_block)
            return (start, end)
        return None
    
    def find_fuzzy_match(self, search_block: str, threshold: float = 0.85) -> tuple:
        lines = search_block.split('\n')
        best_match = None
        best_score = 0
        best_start = -1
        best_end = -1
        
        for i in range(len(self.content.split('\n'))):
            window = '\n'.join(self.content.split('\n')[i:i+len(lines)])
            matcher = difflib.SequenceMatcher(None, search_block, window)
            score = matcher.ratio()
            if score > best_score and score >= threshold:
                best_score = score
                best_match = window
                best_start = i
                best_end = i + len(lines)
        
        if best_match and best_score >= threshold:
            return (best_start, best_end, best_score)
        return None
    
    def apply_replace(self, search_block: str, replace_block: str, match_range: tuple):
        start, end = match_range[:2]
        new_content = self.content[:start] + replace_block + self.content[end:]
        return new_content
```

For Python-specific editing, AST-based approaches with libraries like LibCST achieve much higher accuracy. LibCST stands for Concrete Syntax Tree and preserves the exact formatting of your code including whitespace, comments, and parentheses. This means you can transform code semantically without worrying about changing the style. The library uses a visitor pattern where you define transformations as methods that fire when the visitor encounters specific AST nodes.

LibCST is recommended for production codebases because it achieves over 98 percent accuracy even on large, complex files. The approach is more sophisticated than pattern matching because it understands code structure rather than just text. You can add imports, modify function signatures, rename variables, or refactor entire classes while preserving the original code style.

```python
import libcst as cst

class AddImportTransformer(cst.CSTTransformer):
    def __init__(self, import_name: str):
        self.import_name = import_name
    
    def leave_Module(self, original_node, updated_node):
        new_body = [cst.SimpleStatementLine([cst.Import([cst.ImportAlias(name=cst.Name(self.import_name))])]), cst.Newline()]
        new_body.extend(updated_node.body)
        return updated_node.with_changes(body=new_body)

with open('file.py', 'r') as f:
    source = f.read()
tree = cst.parse_module(source)
transformer = AddImportTransformer('collections')
new_tree = tree.visit(transformer)
with open('file.py', 'w') as f:
    f.write(new_tree.code)
```

Diff-based editing using the OpenAI patch format provides another robust approach. This format uses context lines for anchoring instead of line numbers, which makes it resilient to code changes. The format includes three lines of context before and after the actual change, with lines starting with space for unchanged content, minus for removed content, and plus for added content. This approach is similar to git unified diff and is widely understood by version control systems.

```python
from difflib import unified_diff

def generate_patch(old_content: str, new_content: str, filename: str) -> str:
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = list(unified_diff(old_lines, new_lines, fromfile=f'old/{filename}', tofile=f'new/{filename}', lineterm=''))
    return ''.join(diff)
```

Ambiguous matches occur when the same SEARCH block appears multiple times in a file. The resolver must use context to identify which occurrence the agent intended. Middle-out fuzzy matching starts from the expected location based on surrounding context and expands outward, scoring each potential match with Levenshtein distance. Line hints provided by the agent as optional metadata help narrow the search to specific regions. Detailed error feedback showing all matches found helps the agent refine its request.

Multi-file editing coordination becomes essential when a single logical change affects multiple files. A spec-driven decomposition approach uses a shared document that defines the overall task and allows multiple agents to poll for updates. File locking prevents concurrent edits to the same file by acquiring and releasing locks before modifying. Dependency ordering tracks which files depend on others and applies changes in topological order. Quality gates like running linters after each file ensure that changes do not break the codebase.

```python
import fcntl

class FileLock:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock_file = f"{file_path}.lock"
    
    def acquire(self):
        self.lock = open(self.lock_file, 'w')
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX)
    
    def release(self):
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
        self.lock.close()
        import os
        os.remove(self.lock_file)
```

Displaying diffs to users for review is essential for trust and quality control. When an agent suggests file edits, users need to see exactly what changes will be made. Rich and Textual provide excellent diff rendering with syntax highlighting for the diff format. Side-by-side comparison view shows old and new content in parallel columns. Inline comments allow users to annotate specific changes. Accept or reject individual hunks enables selective application of edits.

The minimum viable file editing implementation should use SEARCH and REPLACE blocks with layered matching for simplicity. Add LibCST for Python-specific operations once the basic approach is stable. Implement context line anchoring to avoid line number fragility. Provide clear error messages when matches fail. And always show diffs before applying changes in an interactive session.


---

# Chapter 7: Error Recovery and Hallucination Protection

When building an AI coding agent, the real challenge is not making the happy path work but handling the inevitable failures gracefully. Models hallucinate tool names. Tool calls fail with cryptic error messages. File permissions prevent edits. Network timeouts interrupt API calls. Your agent must detect these failures, classify them correctly, and recover in ways that maintain progress or fail safely rather than spiraling into endless error loops.

The failure modes unique to LLM-based agents include rate limits that hit unpredictably based on tokens per minute quotas, context window overflow that causes silent degradation as the agent accumulates history, content policy rejections that vary between providers, response format drift when model updates change output structure, and partial or malformed responses that break downstream parsing. These failures require specialized handling that goes beyond traditional software error management.

A progressive failure hierarchy establishes the response strategy. First attempt self-correction where the agent detects the error and retries or adjusts its approach. When self-correction fails, fall back to an alternative strategy or simplified version of the task. If the fallback also fails, degrade gracefully by delivering partial results rather than complete failure. Finally, escalate to human intervention with sufficient context so the user can make an informed decision.

Error classification determines which recovery strategy to apply. Transient errors like rate limits and timeouts should trigger retry with exponential backoff. Permanent errors like invalid tool names or missing files should fail immediately with clear error messages. Degraded errors like context overflow should switch to compacted context or alternative processing. The classification function examines the error type, status codes, and error messages to assign the appropriate category.

Exponential backoff with jitter is the standard retry strategy for transient errors. Each retry attempt waits longer than the previous one, typically doubling the wait time. Adding random jitter prevents thundering herd problems when multiple agents retry simultaneously. A maximum delay cap prevents waiting indefinitely for very long failures. Tenacity is a Python library that implements this pattern with clean decorators and flexible configuration.

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
)
def resilient_api_call(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

Circuit breakers prevent cascading failures when dependencies are consistently unavailable. The circuit breaker tracks failure counts and transitions to an open state when failures exceed a threshold. In the open state, all calls fail immediately without attempting the actual operation. After a recovery timeout, the circuit transitions to half-open and allows a test request. If the test succeeds, the circuit closes and normal operation resumes.

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = max(0, self.failure_count - 1)
        if self.state == CircuitState.HALF_OPEN and self.failure_count == 0:
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

Validation layers catch malformed or dangerous outputs before they cause problems. Schema validation ensures tool calls match the expected structure and types. Security validation blocks dangerous patterns like file deletion commands or arbitrary code execution. Output sanitization removes or escapes potentially harmful content. The composite validator runs multiple validators in sequence and fails fast when strict mode is enabled.

```python
import jsonschema
from pydantic import BaseModel

class ToolCallSchema(BaseModel):
    name: str
    arguments: dict
    
    class Config:
        extra = "forbid"

def validate_tool_call(tool_call: dict) -> tuple:
    try:
        ToolCallSchema.model_validate(tool_call)
        return True, ""
    except Exception as e:
        return False, str(e)

class SecurityValidator:
    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf\s+/", "Destructive file operation"),
        (r"chmod\s+777", "Insecure permissions"),
        (r"eval\s*\(", "Dangerous eval usage")
    ]
    
    def validate(self, output: str) -> tuple:
        errors = []
        sanitized = output
        for pattern, message in self.DANGEROUS_PATTERNS:
            import re
            if re.search(pattern, sanitized, re.IGNORECASE):
                errors.append(message)
                sanitized = re.sub(pattern, "[BLOCKED]", sanitized)
        return sanitized, len(errors) == 0, errors
```

Human-in-the-loop escalation triggers when the agent reaches a point where automated recovery is insufficient or risky. Common escalation triggers include low confidence scores below 60 percent, high-risk actions like file deletion or deployment, content policy violations, and repeated validation failures. The escalation handler gathers context including task description, current state, attempted actions, error messages, and confidence score before presenting to the user.

```python
from dataclasses import dataclass
from enum import Enum

class EscalationReason(Enum):
    LOW_CONFIDENCE = "low_confidence"
    POLICY_VIOLATION = "policy_violation"
    HIGH_RISK_ACTION = "high_risk_action"
    VALIDATION_FAILURE = "validation_failure"

@dataclass
class EscalationContext:
    task_description: str
    current_state: dict
    attempted_actions: list
    error_messages: list
    confidence_score: float
    escalation_reason: EscalationReason

class ConsoleApprovalProvider:
    def request_approval(self, context: EscalationContext) -> tuple:
        print("=" * 60)
        print("ESCALATION REQUIRED - Human Approval Needed")
        print(f"Task: {context.task_description}")
        print(f"Confidence: {context.confidence_score}")
        print(f"Reason: {context.escalation_reason.value}")
        print(f"Errors: {context.error_messages}")
        choice = input("Approve? (y/n/skip): ").lower()
        if choice == 'y':
            return True, "Approved by human"
        elif choice == 'n':
            return False, "Rejected by human"
        return True, "Skipped"
```

Claude Code implements hook-based error handling where pre-tool-use hooks validate permissions and post-tool-use hooks log execution and capture failures. Failed tool results are formatted as text and fed back to the agent so it can reason about what went wrong and try a different approach. Git-based recovery checkpoints allow the agent to restore to a known good state after failed edits by resetting to the last commit.

Aider uses automatic linting and testing after code changes to catch errors immediately. The --lint-cmd and --test-cmd flags run external tools after edits. Retry logic attempts search and replace up to three times before failing. The /run command allows users to share error output directly with the agent for context.

OpenCode uses severity-based error classification with info, warning, error, and fatal levels. Retryable errors trigger automatic retries while non-retryable errors fail immediately. Session-based error tracking maintains a history of failures to detect patterns and escalate proactively.

Graceful degradation strategies provide fallback behavior when the primary approach fails. The primary service handles the normal case. Fallback services provide alternative implementations. When all services fail, default values or partial results are returned with a degraded flag. This pattern ensures the system always responds rather than crashing.

Testing error recovery paths requires deliberate injection of failures. Simulate rate limits by returning 429 responses. Test context overflow by artificially capping context size. Inject malformed JSON to test parsing resilience. Verify that escalation triggers fire at the correct thresholds. Monitor circuit breaker state transitions to ensure proper recovery behavior.

A complete error handling configuration specifies retry parameters, circuit breaker thresholds, escalation triggers, and validation rules. For production systems, configure max retries to three, base delay to one second, max delay to thirty seconds, confidence threshold for escalation to 0.6, and circuit breaker failure threshold to five. Enable strict validation mode and sanitize all tool outputs.


---

# Chapter 8: Vision Capabilities and Local LLM Integration

Adding vision capabilities to your coding agent unlocks powerful use cases that text-only models cannot handle. When a user shares a screenshot of code, the agent can analyze it for bugs, review it for style issues, or even reproduce the code from the image. UI screenshots allow the agent to understand web interfaces and generate matching HTML and CSS. Architecture diagrams and flow charts help the agent reason about system design. Error messages captured as images can be parsed and the underlying issues diagnosed.

For local deployment, several vision-capable models are available. Qwen2.5-VL-7B-Instruct offers the best balance for coding tasks, combining strong code understanding with reasonable resource requirements. LLaVA-OneVision-7B excels at processing code screenshots and diagrams. Llama 3.2 Vision-11B provides good general vision capabilities. Pixtral-12B offers superior instruction following. For lightweight OCR and document processing, Qwen2.5-VL-3B works well.

Hardware requirements depend on model size and precision. A 7B model in INT4 quantization needs 6 to 8 GB VRAM, making it accessible on consumer GPUs like the RTX 3060 with 12 GB. The same model in BF16 precision requires 14 to 16 GB VRAM. An 11 to 13B model in INT4 needs 10 to 12 GB VRAM while BF16 requires 24 to 28 GB. For 32B models, INT4 needs 20 to 24 GB and BF16 needs 64 to 70 GB, requiring professional hardware like the RTX 4090 or A100.

Ollama provides the simplest setup for local vision models. Install Ollama from its website, then pull the desired model with a command like ollama pull qwen2.5vl:7b. The API runs on localhost colon 11434 and accepts chat requests with images included as base64 data or file paths.

```python
import ollama
from pathlib import Path

def analyze_code_screenshot(image_path: str, prompt: str = '') -> str:
    default_prompt = 'Review this code for bugs and suggest improvements.'
    response = ollama.chat(
        model='qwen2.5vl:7b',
        messages=[
            {
                'role': 'user',
                'content': prompt or default_prompt,
                'images': [str(Path(image_path).absolute())]
            }
        ]
    )
    return response['message']['content']

result = analyze_code_screenshot('code_screenshot.png')
print(result)
```

vLLM provides higher throughput for production deployments. Start a vLLM server with the vision model, then use the OpenAI-compatible API endpoint to send requests.

```python
from openai import OpenAI

client = OpenAI(api_key='EMPTY', base_url='http://localhost:8000/v1')

response = client.chat.completions.create(
    model='llava-hf/llava-1.5-7b-hf',
    messages=[{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'What bugs are in this code?'},
            {'type': 'image_url', 'image_url': {'url': 'file:///path/to/code.png'}}
        ]
    }]
)
print(response.choices[0].message.content)
```

For code review from screenshots, use LLaVA-OneVision-7B or Qwen2.5-VL-7B. Both models understand code structure and can identify common bugs. For UI and UX understanding, Qwen2.5-VL-7B or Pixtral-12B excel at identifying interface elements and spatial relationships. For diagram and architecture understanding, Qwen2.5-VL-7B or IBM Granite 3.2 Vision-2B are specialized for chart interpretation. For OCR and documentation, Qwen2.5-VL-3B offers lightweight OCR capabilities.

Integration patterns for vision in coding agents include direct image analysis where users upload images and receive text responses, multimodal chat where conversation history includes both text and images, automated screenshot capture for error debugging, and continuous monitoring where the agent periodically captures and analyzes screens.

A vision-enabled coding agent workflow might look like this. User shares a screenshot of an error. The agent analyzes the image to extract the error message. It searches the codebase for the source of the error. It reads relevant files to understand the context. It suggests fixes based on its analysis. Throughout this process, the agent can reference both text from the conversation and visual information from the screenshot.

```python
class VisionCodingAgent:
    def __init__(self, model='qwen2.5vl:7b'):
        self.model = model
    
    def analyze_error_screenshot(self, image_path: str) -> str:
        prompt = '''Extract the error message from this screenshot and identify its likely cause.
Then suggest specific code changes to fix it.'''
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
        )
        return response['message']['content']
    
    def review_ui_screenshot(self, image_path: str) -> str:
        prompt = '''Analyze this UI screenshot. Identify the layout structure, 
UI components, and suggest improvements for accessibility and user experience.'''
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}]
        )
        return response['message']['content']
```

Performance considerations include token usage for images. Vision models encode images as many tokens, so a single screenshot can consume hundreds or thousands of tokens of context. Be mindful of this when designing long conversations with frequent image exchanges. Flash Attention 2 enables 30 to 50 percent speed improvement for inference. INT4 quantization provides 70 to 80 percent of full precision performance with 50 percent less VRAM.

For development, use Ollama with LLaVA-1.6-7B for quick iteration. For production API deployment, use vLLM with Qwen2.5-VL-7B. For maximum accuracy with vision input on large codebases, use LLaVA-OneVision-34B with vLLM on multi-GPU systems with 48 GB or more VRAM.

Vision capabilities transform a text-based coding agent into a versatile tool that can understand screenshots, diagrams, and visual interfaces. This makes the agent more natural to work with since developers often think visually about code structure and UI design. When implementing vision, start with simple use cases like error screenshot analysis, then expand to more complex tasks like UI generation from wireframes and architecture diagram interpretation.


---

# Chapter 9: Structured Output and JSON Schema Enforcement

Reliable tool calling depends entirely on the model producing well-formed structured output. When the model outputs malformed JSON, includes unexpected fields, or ignores the schema entirely, your tool execution pipeline breaks. This chapter covers the techniques and libraries that guarantee valid structured output from local LLMs.

You have several options for enforcing structured output. The Instructor library provides a unified interface across Ollama, vLLM, and many other providers. It uses Pydantic models to define expected output formats and automatically retries with corrected prompts when validation fails. This approach works well because it does not require special model support and handles edge cases gracefully.

Ollama provides native JSON schema support through the format parameter. When you pass a JSON schema to the format parameter, Ollama constrains the model output to match that schema at the token level. This is more efficient than retry-based validation because constraints are enforced during generation rather than after. However, it requires using Ollama specifically.

vLLM supports structured outputs through its structured_outputs parameter. You can specify JSON schema, regex patterns, or a set of choices. The implementation uses token masking to guarantee the output follows the specified format. Like Ollama, this approach is more efficient but requires specific infrastructure.

The Outlines library offers cross-platform compatibility with token masking that works with OpenAI, Ollama, vLLM, Transformers, and llama.cpp. It supports JSON Schema, Pydantic models, TypedDict, regex, and context-free grammars. The overhead is microseconds compared to seconds for retry approaches.

Guidance with its llguidance backend is the fastest constrained decoding solution. JSON schema is treated as a context-free grammar that constrains token selection during generation. It works with vLLM as a backend and outperforms other frameworks on efficiency, coverage, and quality benchmarks.

```python
import instructor
from pydantic import BaseModel, Field
from typing import List, Optional
from ollama import chat

client = instructor.from_provider(
    "ollama/qwen2.5vl:7b",
    mode=instructor.Mode.JSON,
)

class ToolCall(BaseModel):
    tool_name: str = Field(..., description="Name of tool to call")
    arguments: dict = Field(..., description="Arguments for the tool")

class AgentResponse(BaseModel):
    thoughts: str = Field(..., description="Reasoning about what to do")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools to execute")
    final_response: Optional[str] = Field(default=None, description="Final answer if no tools needed")

response = client.chat.completions.create(
    model="qwen2.5vl:7b",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Read the file main.py"}
    ],
    response_model=AgentResponse,
    max_retries=3,
    timeout=60.0,
)
```

The example above shows the complete pattern for Instructor with Ollama. You define Pydantic models that represent the expected output structure. The client wraps the LLM API and handles validation and retries automatically. The max_retries parameter controls how many attempts are made before giving up. The timeout parameter sets the maximum total time for all retries combined.

Native JSON schema enforcement in Ollama looks like this.

```python
from ollama import chat

response = chat(
    model='qwen2.5vl:7b',
    messages=[{'role': 'user', 'content': 'Extract information from this text'}],
    format={
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'},
            'skills': {'type': 'array', 'items': {'type': 'string'}}
        },
        'required': ['name', 'age']
    }
)
data = response['message']['content']
```

The format parameter accepts a full JSON schema object. The model output will be valid JSON matching this schema. This approach is more efficient than Instructor but requires Ollama specifically.

For vLLM, the structured outputs configuration looks like this.

```python
from vllm import LLM
from vllm.sampling_params import SamplingParams

llm = LLM(model="mistralai/Mistral-7B-Instruct-v0.3")

sampling_params = SamplingParams(
    temperature=0.7,
    structured_outputs={
        'json': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'}
            }
        }
    }
)

outputs = llm.generate(prompts, sampling_params)
```

Prompt engineering techniques improve structured output reliability even without constrained decoding. Schema grounding includes the expected schema in the system prompt with explicit instructions to return only valid JSON. Field descriptions help the model understand what each field should contain. Concrete examples in few-shot prompting show the exact format expected.

```python
system_prompt = '''You are a helpful assistant that always returns valid JSON matching the following schema.
Do not include any text outside the JSON object.

Schema:
{
    "type": "object",
    "properties": {
        "tool_name": {"type": "string"},
        "arguments": {"type": "object"}
    },
    "required": ["tool_name", "arguments"]
}
'''
```

When choosing between constrained decoding and post-hoc validation, consider the tradeoffs. Constrained decoding guarantees syntactic validity at generation time with microsecond overhead but may reduce model confidence on complex tasks. Post-hoc validation allows full model freedom during generation with better task accuracy but requires retries that add seconds of latency.

Benchmark results from JSONSchemaBench show that Guidance leads in efficiency and coverage, followed by Outlines for cross-platform compatibility, then XGrammar and llama.cpp. For production deployments, Instructor plus Ollama provides the most practical solution with automatic retries and Pydantic validation.

```python
# Complete tool calling implementation with Instructor
import instructor
from pydantic import BaseModel
from typing import List, Dict, Any
from ollama import chat

class ToolSchema(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    thoughts: str
    tool_calls: List[ToolSchema] = []
    response: str = ""

client = instructor.from_provider("ollama/qwen2.5vl:7b", mode=instructor.Mode.TOOLS)

def execute_tool_loop(user_input: str, available_tools: List[Dict]) -> str:
    messages = [
        {"role": "system", "content": "You have access to tools. Choose appropriately."},
        {"role": "user", "content": user_input}
    ]
    
    while True:
        response = client.chat.completions.create(
            model="qwen2.5vl:7b",
            messages=messages,
            tools=available_tools,
            response_model=ToolCallResponse,
            max_retries=3,
        )
        
        if not response.tool_calls:
            return response.response
        
        # Execute tool calls and append results
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call.name, tool_call.arguments)
            messages.append({"role": "assistant", "tool_calls": [tool_call.dict()]})
            messages.append({"role": "tool", "content": result})
```

The implementation above combines structured output enforcement with a complete tool calling loop. Instructor handles validation and retries, while the loop continues executing tools until the model decides it has the final answer. Error messages from tool failures are fed back into the conversation so the model can adjust its approach.


---

# Chapter 10: Getting Started and Minimal Implementation

Now that you understand all the components of a coding agent, this chapter provides a concrete path to building your first working implementation. We will focus on the minimum viable features that demonstrate the core capabilities without unnecessary complexity.

Start with the hardware and infrastructure setup. For local deployment, you need a GPU with at least 8 GB VRAM to run a 7B model with INT4 quantization. An RTX 3060 with 12 GB is the minimum recommended. For faster inference, use an RTX 3090 or 4090 with 24 GB. Install Ollama from its official website and pull the Qwen2.5-VL-7B model with the command ollama pull qwen2.5vl:7b. Verify the installation by running ollama run qwen2.5vl:7b and asking a simple question.

Set up your Python environment with the following dependencies. Create a virtual environment with python -m venv agent-env and activate it with source agent-env/bin/activate on Unix or agent-env\Scripts\activate on Windows. Install the core libraries with pip install textual rich ollama instructor pydantic tenacity mcp libcst. These provide the TUI framework, LLM client, structured output, error handling, MCP protocol, and file editing capabilities.

The project structure should look like this. Create a root directory for your agent. Inside it, create a src folder for source code, a config folder for configuration files, a sessions folder for persistent session data, and a logs folder for operation logs. Your main entry point is src/main.py. The core components live in src/agent.py for the main loop, src/tools.py for tool definitions, src/tui.py for the terminal interface, and src/context.py for context management.

The minimal tool set includes five core capabilities. A bash tool for executing shell commands with a whitelist of allowed operations. A read tool for viewing file contents with path validation. A write tool for creating or replacing files. An edit tool for SEARCH and REPLACE operations. And a grep tool for searching text patterns. Start with these five and add more as needed.

```python
# Minimal tool definitions
from pathlib import Path
import subprocess
import shlex

class MinimalTools:
    ALLOWED_COMMANDS = ["ls", "cat", "pwd", "echo", "grep", "find", "git"]
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
    
    def bash(self, command: str) -> str:
        parts = shlex.split(command)
        if parts[0] not in self.ALLOWED_COMMANDS:
            return f"Error: Command not allowed. Allowed: {self.ALLOWED_COMMANDS}"
        result = subprocess.run(parts, capture_output=True, text=True, timeout=30, cwd=str(self.base_dir))
        return result.stdout + result.stderr
    
    def read(self, path: str) -> str:
        file_path = (self.base_dir / path).resolve()
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def write(self, path: str, content: str) -> str:
        file_path = (self.base_dir / path).resolve()
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    def edit(self, path: str, search: str, replace: str) -> str:
        file_path = (self.base_dir / path).resolve()
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            if search not in content:
                return f"Error: Search pattern not found in {path}"
            new_content = content.replace(search, replace, 1)
            with open(file_path, 'w') as f:
                f.write(new_content)
            return f"Successfully edited {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"
    
    def grep(self, pattern: str, path: str = ".") -> str:
        file_path = (self.base_dir / path).resolve()
        try:
            result = subprocess.run(["grep", "-r", pattern, str(file_path)], capture_output=True, text=True)
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error searching: {str(e)}"
```

The main agent loop is straightforward. Initialize the LLM client with Instructor for structured output. Define your tool schemas. Enter the loop where you send messages to the model, extract tool calls, execute them, append results, and repeat until the model provides a final response.

```python
import instructor
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class AgentResponse(BaseModel):
    thoughts: str
    tool_calls: List[ToolCall] = []
    final_response: Optional[str] = None

class MinimalAgent:
    def __init__(self, model: str = "qwen2.5vl:7b"):
        self.client = instructor.from_provider(f"ollama/{model}", mode=instructor.Mode.TOOLS)
        self.tools = MinimalTools(".")
        self.message_history = []
    
    def run(self, user_input: str) -> str:
        self.message_history.append({"role": "user", "content": user_input})
        
        while True:
            response = self.client.chat.completions.create(
                model="qwen2.5vl:7b",
                messages=self.message_history,
                response_model=AgentResponse,
                max_retries=3,
                timeout=60.0,
            )
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    result = self.execute_tool(tool_call)
                    self.message_history.append({"role": "assistant", "tool_calls": [tool_call.dict()]})
                    self.message_history.append({"role": "tool", "content": result})
            else:
                return response.final_response or "No response generated"
    
    def execute_tool(self, tool_call: ToolCall) -> str:
        try:
            tool = getattr(self.tools, tool_call.name)
            return tool(**tool_call.arguments)
        except Exception as e:
            return f"Tool execution error: {str(e)}"
```

The terminal interface wraps the agent loop with Textual for interactive chat. Display messages in the chat container, capture user input, stream tool execution output to RichLog, and show status information in the footer.

```python
from textual.app import App, ComposeResult
from textual.widgets import Static, Input, RichLog
from textual.containers import VerticalScroll

class AgentTUI(App):
    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="chat")
        yield RichLog(id="output", markup=True, highlight=True)
        yield Input(placeholder="Ask the agent...", id="input")
    
    async def on_input_submitted(self, event: Input.Submitted):
        user_text = event.value
        self.query_one("#chat", VerticalScroll).mount(Static(f"You: {user_text}"))
        self.query_one("#input", Input).value = ""
        
        result = await self.agent.run(user_text)
        self.query_one("#chat", VerticalScroll).mount(Static(f"Agent: {result}"))
```

Session persistence stores the message history and working state to JSON files. Before exiting or on timeout, serialize the message history to a session file. On startup, check for existing session files and offer to resume.

```python
import json
from pathlib import Path
from datetime import datetime

class SessionManager:
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
    
    def save_session(self, session_id: str, messages: List[dict], working_dir: str):
        session_file = self.session_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump({"messages": messages, "working_dir": working_dir, "timestamp": datetime.now().isoformat()}, f)
    
    def load_session(self, session_id: str) -> dict:
        session_file = self.session_dir / f"{session_id}.json"
        with open(session_file, 'r') as f:
            return json.load(f)
    
    def list_sessions(self) -> List[str]:
        return [f.stem for f in self.session_dir.glob("*.json")]
```

Configuration management separates environment-specific settings from code. Use a YAML or JSON config file for model selection, tool permissions, and context limits.

```yaml
# config.yaml
llm:
  model: qwen2.5vl:7b
  base_url: http://localhost:11434

context:
  max_tokens: 200000
  compaction_threshold: 0.85

tools:
  allowed_commands: [ls, cat, pwd, echo, grep, find, git]
  allowed_directories: [/home/user/projects]

session:
  directory: sessions
  auto_save: true
  save_interval_seconds: 300
```

Testing your minimal agent involves both unit tests and integration tests. Test each tool independently with various inputs and edge cases. Test the agent loop with predefined scenarios to verify correct tool selection and error handling. Test session persistence by saving and restoring state. Test the TUI for responsive interaction.

Start with the following test scenarios. A simple file read to verify basic tool execution. A multi-step task that requires reading multiple files and running a command. An error scenario where a tool fails and the agent recovers. A context overflow scenario that tests compaction. And a session persistence scenario that saves and resumes.

Common pitfalls to avoid include not implementing proper error handling which leads to silent failures, ignoring context limits which causes quality degradation, providing insufficient tool descriptions which leads to poor tool selection, and failing to show diffs which prevents user trust in file edits.

The roadmap for extending beyond minimal includes adding MCP integration for external tools, implementing repository maps for codebase context, adding sub-agent support for parallel work, integrating git for version control and rollback, implementing automated testing and linting after edits, and adding vision support for screenshot analysis.

Your minimal implementation should demonstrate the core loop: receive input, select and execute tools, show results, and produce a final answer. When this works reliably with proper error handling and user feedback, you have the foundation for a capable coding agent.


---

