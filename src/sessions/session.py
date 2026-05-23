import os
import json
import time
from uuid import uuid4
from pathlib import Path

from utils.noslop_dir_utils import get_noslop_path


class Session:
    def __init__(self, id: str | None = None):
        if id is None:
            id = str(uuid4())

        # Sessions directory
        sessions_dir = f"{get_noslop_path()}/sessions"

        if not os.path.exists(sessions_dir):
            os.makedirs(f"{get_noslop_path()}/sessions", exist_ok=True)

        self._sessions_dir = sessions_dir
        self._session_id = id

        self._session_data = {
            "id": self._session_id,
            "summary": "",
            "context": [],
            "created_time_ts": int(time.time() * 1000),
            "updated_time_ts": int(time.time() * 1000),
        }

        if os.path.exists(f"{self._sessions_dir}/{self._session_id}.json"):
            with open(f"{self._sessions_dir}/{self._session_id}.json", "r") as f:
                contents = f.read()

            contents_json = json.loads(contents)

            self._session_data["summary"] = contents_json["summary"]
            self._session_data["context"] = contents_json["context"]
            self._session_data["created_time_ts"] = contents_json["created_time_ts"]
            self._session_data["updated_time_ts"] = contents_json["updated_time_ts"]

    def save(self, context: list):
        self._session_data["context"] = context
        self._session_data["updated_time_ts"] = int(time.time() * 1000)

        if not self._session_data["summary"]:
            # find first user message
            first_user_message = ""
            for m in self._session_data["context"]:
                if m["role"] == "user":
                    first_user_message = m["content"][0]["text"]
                    break

            self._session_data["summary"] = first_user_message[:150]

        with open(f"{self._sessions_dir}/{self._session_id}.json", "w") as f:
            session_dump = json.dumps(self._session_data)

            f.write(session_dump)

    def get_context(self) -> list:
        return self._session_data["context"]
