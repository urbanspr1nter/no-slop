import math


def sqrt(x: float) -> float:
    """Returns the square root of a given number.

    Output:
        - float: square root of the number
    """

    return math.sqrt(x)


def sum(x: float, y: float) -> float:
    """Returns the sum of 2 numbers.

    Output:
        - float: sum of 2 numbers
    """

    return x + y


def sub(x: float, y: float) -> float:
    """Returns the difference between 2 numbers.

    Output:
        - float: difference between 2 numbers
    """

    return x - y


def mult(x: float, y: float) -> float:
    """Returns the product of 2 numbers.

    Output:
        - float: product of 2 numbers.
    """

    return x * y


def div(x: float, y: float) -> float:
    """Returns the quotient of 2 numbers.

    Output:
        - float: quotient of 2 numbers.
    """

    try:
        return x / y
    except ZeroDivisionError as z:
        print(f"Division by 0 error. Attempted to divide by: {y}")
        raise z


def pow(x: float, y: float) -> float:
    """Raises a number x to the power of y.

    Output:
        - float: x to the power of y
    """

    return x**y


def mod(x: float, y: float) -> float:
    """Computes modulo of x and y.

    Output:
        - float: result of x mod y
    """

    return x % y
