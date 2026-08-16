"""Tool registry.

Every tool is a :class:`tools.base_tool.BaseTool` subclass. The OpenAI function
schemas sent to the model are derived from the tool classes themselves, so a
tool's schema and its implementation can never drift apart (previously both
were maintained by hand in two different places).
"""

from tools.base_tool import BaseTool
from tools.file_edit_and_show_diff import FileEditAndShowDiffTool
from tools.fs import (
    FileExistsTool,
    ListDirectoryTool,
    MakeDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)
from tools.glob_tool import GlobTool
from tools.ns_math import (
    DivTool,
    ModTool,
    MultTool,
    PowTool,
    SqrtTool,
    SubTool,
    SumTool,
)
from tools.shell import ShellExecSyncTool
from tools.web_search_and_scrape import WebPageScrapeTool, WebSearchTool

FILE_SYSTEM_TOOLS: list[BaseTool] = [
    WriteFileTool(),
    ReadFileTool(),
    MakeDirectoryTool(),
    ListDirectoryTool(),
    FileExistsTool(),
    GlobTool(),
]

MATH_TOOLS: list[BaseTool] = [
    SqrtTool(),
    SumTool(),
    SubTool(),
    MultTool(),
    DivTool(),
    PowTool(),
    ModTool(),
]

SHELL_TOOLS: list[BaseTool] = [ShellExecSyncTool()]

EDITING_TOOLS: list[BaseTool] = [FileEditAndShowDiffTool()]

WEB_TOOLS: list[BaseTool] = [WebSearchTool(), WebPageScrapeTool()]

#: All tool instances, in schema order.
ALL_TOOLS: list[BaseTool] = [
    *FILE_SYSTEM_TOOLS,
    *MATH_TOOLS,
    *SHELL_TOOLS,
    *EDITING_TOOLS,
    *WEB_TOOLS,
]

#: name -> tool instance, used by the dispatch layer (call_tool).
TOOLS: dict[str, BaseTool] = {tool.name: tool for tool in ALL_TOOLS}

#: The OpenAI function schemas sent to the model with every request.
TOOL_SET: list[dict] = [tool.to_schema() for tool in ALL_TOOLS]
