from abc import ABC, abstractmethod

from tools.helpers import err, ok


class BaseTool(ABC):
    """The one interface every tool implements.

    A tool is defined by three pieces of metadata (``name``, ``description``,
    ``parameters``) that are turned into the OpenAI function schema the model
    sees (see :meth:`to_schema`), plus :meth:`invoke` which performs the work.

    The registry derives the model-facing schema from these attributes, so the
    schema and the implementation can never drift apart.
    """

    #: Name the model uses to invoke this tool. Must be unique across tools.
    name: str = ""

    #: Human-readable description shown to the model.
    description: str = ""

    #: JSON schema (OpenAI function ``parameters``) describing the arguments.
    parameters: dict = {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    def invoke(self, **kwargs) -> dict:
        """Execute the tool and return a normalized result envelope.

        Always returns a dict with a ``status`` key: ``"ok"`` on success and
        ``"error"`` on failure. Prefer the :func:`tools.helpers.ok` and
        :func:`tools.helpers.err` helpers. Implementations must never raise
        for model-visible failures; :meth:`run` is the last line of defense.
        """

    def to_schema(self) -> dict:
        """Return the OpenAI function schema for this tool."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def run(self, tool_call_id: str = "", **kwargs) -> dict:
        """Invoke the tool safely, converting any exception into an error envelope.

        This is what the dispatch layer calls. It guarantees a tool bug or a
        bad argument can never crash the agent loop.
        """
        try:
            result = self.invoke(tool_call_id=tool_call_id, **kwargs)
        except Exception as e:
            return err(f"{self.name} failed: {type(e).__name__}: {e}")

        if isinstance(result, dict) and result.get("status") in ("ok", "error"):
            return result

        # Defensive: a tool that forgot the envelope still gets normalized.
        return ok(result)
