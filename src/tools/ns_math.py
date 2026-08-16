import math

from tools.base_tool import BaseTool
from tools.helpers import err, ok

_BINARY_SCHEMA = {
    "type": "object",
    "properties": {
        "x": {"type": "number", "description": "The first operand."},
        "y": {"type": "number", "description": "The second operand."},
    },
    "required": ["x", "y"],
}


class MathTool(BaseTool):
    """Shared implementation for the small math tools.

    Subclasses supply ``name``, ``description``, ``parameters`` and a
    ``func``. Errors (e.g. taking a square root of a negative number or a
    division by zero) are converted into error envelopes instead of raising.
    """

    func = staticmethod(lambda *args: args[0])
    arity = 1

    def invoke(self, **kwargs) -> dict:
        if self.arity == 1:
            args = [kwargs.get("x", 0)]
        else:
            args = [kwargs.get("x", 0), kwargs.get("y", 0)]

        try:
            result = self.func(*args)
        except (ValueError, ZeroDivisionError, OverflowError) as e:
            return err(f"Could not compute result: {e}.")

        return ok(result)


class SqrtTool(MathTool):
    name = "sqrt"
    description = "Computes the square root of a given number."
    parameters = {
        "type": "object",
        "properties": {
            "x": {
                "type": "number",
                "description": "The number you want to square root.",
            }
        },
        "required": ["x"],
    }
    arity = 1
    func = staticmethod(math.sqrt)


class SumTool(MathTool):
    name = "sum"
    description = "Computes the sum of 2 numbers."
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x + y)


class SubTool(MathTool):
    name = "sub"
    description = "Computes the difference between 2 numbers."
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x - y)


class MultTool(MathTool):
    name = "mult"
    description = "Computes the product between 2 numbers."
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x * y)


class DivTool(MathTool):
    name = "div"
    description = (
        "Computes the quotient between 2 numbers. Raises a ZeroDivisionError if "
        "attempting to divide by 0."
    )
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x / y)


class PowTool(MathTool):
    name = "pow"
    description = "Computes x raised to y power."
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x**y)


class ModTool(MathTool):
    name = "mod"
    description = "Computes the modulo between 2 numbers."
    parameters = _BINARY_SCHEMA
    arity = 2
    func = staticmethod(lambda x, y: x % y)
