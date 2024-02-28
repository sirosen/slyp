from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Result:
    messages: list[Message]
    success: bool

    @property
    def message_strings(self) -> list[str]:
        return [m.message for m in self.messages]

    def join(self, other: Result) -> Result:
        return Result(
            messages=self.messages + other.messages,
            success=self.success and other.success,
        )


@dataclasses.dataclass
class Message:
    message: str
    verbosity: int = 0
    priority: int = 1

    def __lt__(self, other: Message) -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.message < other.message
