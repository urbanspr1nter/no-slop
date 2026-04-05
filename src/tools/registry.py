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
