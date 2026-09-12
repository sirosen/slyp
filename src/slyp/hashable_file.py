from __future__ import annotations

import dataclasses
import hashlib
import sys


@dataclasses.dataclass
class HashableFile:
    filename: str
    _sha: str | None = None
    _binary_content: bytes | None = None

    @property
    def binary_content(self) -> bytes:
        if self._binary_content is None:
            self._binary_content = self._read()
        return self._binary_content

    def _read(self) -> bytes:
        if self.is_stdio:
            return sys.stdin.buffer.read()

        with open(self.filename, "rb") as fp:
            return fp.read()

    @property
    def sha(self) -> str:
        if self._sha is None:
            self._sha = hashlib.sha256(self.binary_content).hexdigest()
        return self._sha

    def write(self, content: bytes) -> None:
        self._write(content)
        self._sha = None
        self._binary_content = content

    def _write(self, content: bytes, /) -> None:
        if self.is_stdio:
            sys.stdout.buffer.write(content)
        else:
            with open(self.filename, "wb") as fp:
                fp.write(content)

    @property
    def is_stdio(self) -> bool:
        return self.filename == "-"
