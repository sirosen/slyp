from __future__ import annotations

import dataclasses
import hashlib


@dataclasses.dataclass
class HashableFile:
    filename: str
    _sha: str | None = None
    _binary_content: bytes | None = None

    @property
    def binary_content(self) -> bytes:
        if self._binary_content is None:
            with open(self.filename, "rb") as fp:
                self._binary_content = fp.read()
        return self._binary_content

    @property
    def sha(self) -> str:
        if self._sha is None:
            self._sha = hashlib.sha256(self.binary_content).hexdigest()
        return self._sha

    def write(self, content: bytes) -> None:
        with open(self.filename, "wb") as fp:
            fp.write(content)

        self._sha = None
        self._binary_content = content
