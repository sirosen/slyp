from __future__ import annotations

import dataclasses
import functools
import hashlib


@dataclasses.dataclass
class HashableFile:
    filename: str
    _sha: str | None = None

    @functools.cached_property
    def binary_content(self) -> bytes:
        with open(self.filename, "rb") as fp:
            return fp.read()

    @property
    def sha(self) -> str:
        if self._sha is None:
            self._sha = hashlib.sha256(self.binary_content).hexdigest()
        return self._sha

    def write(self, content: bytes) -> None:
        with open(self.filename, "wb") as fp:
            fp.write(content)
        self._sha = None
