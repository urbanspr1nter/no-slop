FILE_SYSTEM_TOOLS = [
    {
        "type": "function",
        "name": "write_file",
        "description": "Writes a file with contents given a filepath within the sandbox directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "filepath relative to the sandbox root. If no sandbox root is prepended, it will be done so automatically.",
                },
                "content": {
                    "type": "string",
                    "description": "contents to write to the file",
                },
                "mode": {
                    "type": "string",
                    "description": "file operation mode. default: 'w'.",
                },
            },
            "required": ["filepath", "content"],
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Reads a file and gets contents as a string given the filepath within the sandbox root.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "filepath relative to the sandbox root. If no sandbox root is prepended, it will be done so automatically.",
                },
                "mode": {
                    "type": "string",
                    "description": "file operation mode. default: 'r'.",
                },
            },
            "required": ["filepath"],
        },
    },
    {
        "type": "function",
        "name": "make_directory",
        "description": "Creates a directory at the filepath within the sandbox root.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "filepath relative to the sandbox root. If no sandbox root is prepended, it will be done so automatically.",
                },
                "create_parent_if_not_exists": {
                    "type": "boolean",
                    "description": "Create all parent directories if true. Default false.",
                },
            },
            "required": ["filepath"],
        },
    },
    {
        "type": "function",
        "name": "list_directory",
        "description": "Gets the filenames at the current directory specified by the filepath within the sandbox root.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "filepath relative to the sandbox root. If no sandbox root is prepended, it will be done so automatically.",
                }
            },
            "required": ["filepath"],
        },
    },
    {
        "type": "function",
        "name": "file_exists",
        "description": "Checks if the file exists specified by the filepath within the sandbox root.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "filepath relative to the sandbox root. If no sandbox root is prepended, it will be done so automatically.",
                }
            },
            "required": ["filepath"],
        },
    },
    {
        "type": "function",
        "name": "get_root_dir",
        "description": "Gets the filepath to the sandbox root.",
    },
]

MATH_TOOLS = [
    {
        "type": "function",
        "name": "sqrt",
        "description": "Computes the square root of a given number.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The number you want to square root.",
                }
            },
            "required": ["x"],
        },
    },
    {
        "type": "function",
        "name": "sum",
        "description": "Computes the sum of 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "sub",
        "description": "Computes the difference between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "mult",
        "description": "Computes the product between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "div",
        "description": "Computes the quotient between 2 numbers. Raises a ZeroDivisionError if attempting to divide by 0.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "pow",
        "description": "Computes x raised to y power.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "mod",
        "description": "Computes the modulo between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
]

SHELL_TOOLS = [
    {
        "type": "function",
        "name": "shell_exec_sync",
        "description": 'Run a shell command synchronously. Parameters are "program" (string) and "arguments" (array). Example: program="ls" arguments=["-la", "/etc"]',
        "parameters": {
            "type": "object",
            "properties": {
                "program": {
                    "type": "string",
                    "description": "Program or builtin to run.",
                },
                "arguments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of arguments including switches/options.",
                },
                "env": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Environment variables to set (key-value pairs). OS environment will be extended with this.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Maximum number of seconds to execute the shell command. Default=120 seconds if not provided.",
                },
            },
            "required": ["program"],
        },
    }
]

TOOL_SET = []
TOOL_SET.extend(FILE_SYSTEM_TOOLS)
TOOL_SET.extend(MATH_TOOLS)
TOOL_SET.extend(SHELL_TOOLS)
