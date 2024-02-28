from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Result:
    messages: list[Message]
    success: bool

    @property
    def message_strings(self) -> list[str]:
        return [m.message for m in self.messages]


@dataclasses.dataclass
class Message:
    message: str
    verbosity: int = 0
