import functools
import typing as t

import libcst
import libcst.metadata


class LazyCSTNodePositions:
    """
    A layer over libcst's MetadataWrapper which only initializes it on access, thereby
    saving on the cost of building this metadata until it's strictly necessary.

    Only provides the PositionProvider metadata.
    """

    def __init__(self, module: libcst.Module, unsafe_skip_copy: bool = True) -> None:
        self._module = module
        self._unsafe_skip_copy = unsafe_skip_copy

    @functools.cached_property
    def _map(self) -> t.Mapping[libcst.CSTNode, libcst.metadata.CodeRange]:
        return libcst.MetadataWrapper(
            self._module, unsafe_skip_copy=self._unsafe_skip_copy
        ).resolve(libcst.metadata.PositionProvider)

    def lookup(self, node: libcst.CSTNode) -> libcst.metadata.CodeRange:
        return self._map[node]
