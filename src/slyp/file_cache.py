from __future__ import annotations

import dataclasses
import hashlib
import os
import shutil

_CACHEDIR = ".slyp_cache"


@dataclasses.dataclass
class HashedFile:
    filename: str
    sha: str = ""

    def __post_init__(self) -> None:
        if not self.sha:
            self.sha = self._compute_sha()

    def _compute_sha(self) -> str:
        with open(self.filename, "rb") as fp:
            return hashlib.sha256(fp.read()).hexdigest()


def _ensure_cachedir(base_cache_dir: str, subdir: str) -> None:
    os.makedirs(base_cache_dir, exist_ok=True)
    os.makedirs(subdir, exist_ok=True)
    gitignore_path = os.path.join(base_cache_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "wb") as fp:
            fp.write(b"*\n")


class PassingFileCache:
    def __init__(
        self,
        *,
        contract_version: str,
        config_id: str,
        base_cache_dir: str = _CACHEDIR,
        cache_dir: str = "passing_files",
    ) -> None:
        self._cache_dir = os.path.join(
            base_cache_dir, f"{cache_dir}_{contract_version}"
        )
        self._config_id = config_id
        _ensure_cachedir(base_cache_dir, self._cache_dir)

    def clear(self) -> None:
        shutil.rmtree(self._cache_dir, ignore_errors=True)

    def _find(self, item: HashedFile) -> str:
        return os.path.join(self._cache_dir, item.sha)

    def __contains__(self, item: HashedFile) -> bool:
        cache_file = self._find(item)
        if not os.path.exists(cache_file):
            return False
        with open(cache_file) as fp:
            data = fp.read()
        return self._config_id in data

    def add(self, item: HashedFile) -> None:
        cache_file = self._find(item)
        if not os.path.exists(cache_file):
            data = self._config_id + "\n"
        else:
            with open(cache_file) as fp:
                data = fp.read().strip()

            if self._config_id in data:  # short-circuit (already recorded)
                return
            else:
                data += f"\n{self._config_id}\n"

        with open(cache_file, "w") as fp:
            fp.write(data)
