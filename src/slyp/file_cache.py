from __future__ import annotations

import dataclasses
import hashlib
import os
import shutil

_CACHEDIR = ".slyp_cache"


@dataclasses.dataclass
class HashedFile:
    filename: str
    sha: bytes = b""

    def __post_init__(self) -> None:
        if not self.sha:
            self.sha = self._compute_sha()

    def _compute_sha(self) -> bytes:
        with open(self.filename, "rb") as fp:
            return hashlib.sha256(fp.read()).digest()


def _ensure_cachedir(base_cache_dir: str, cache_subdirs: list[str]) -> None:
    os.makedirs(base_cache_dir, exist_ok=True)
    for subdir in cache_subdirs:
        os.makedirs(os.path.join(base_cache_dir, subdir), exist_ok=True)
    gitignore_path = os.path.join(base_cache_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "wb") as fp:
            fp.write(b"*\n")


class PassingFileCache:
    def __init__(
        self,
        *,
        config_id: str,
        base_cache_dir: str = _CACHEDIR,
        cache_dir: str = "passing_files",
    ):
        self._cache_dir = os.path.join(base_cache_dir, cache_dir, config_id)
        _ensure_cachedir(base_cache_dir, [cache_dir])

    def clear(self) -> None:
        shutil.rmtree(_CACHEDIR, ignore_errors=True)

    def __contains__(self, item: HashedFile) -> bool:
        cached_hashfile = os.path.join(self._cache_dir, item.filename)
        if not os.path.exists(cached_hashfile):
            return False
        with open(cached_hashfile, "rb") as fp:
            return fp.read() == item.sha

    def add(self, item: HashedFile) -> None:
        target_file = os.path.join(self._cache_dir, item.filename)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "wb") as fp:
            fp.write(item.sha)

    def __delitem__(self, item: HashedFile) -> None:
        cached_hashfile = os.path.join(self._cache_dir, item.filename)
        if os.path.exists(cached_hashfile):
            os.remove(cached_hashfile)
