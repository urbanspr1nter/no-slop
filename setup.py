from setuptools import setup

setup(
    name="mypackage",
    version="0.0.1",
    where="src",
    install_requires=["requests", "openai", "textual", "textual-dev"],
)
