from __future__ import annotations

import typing as t

import libcst
import libcst.matchers

# alphabetical order
NODE_TYPES = t.Union[
    libcst.Attribute,
    libcst.Await,
    libcst.BinaryOperation,
    libcst.Call,
    libcst.Comparison,
    libcst.ConcatenatedString,
    libcst.Dict,
    libcst.DictComp,
    libcst.Ellipsis,
    libcst.Float,
    libcst.FormattedString,
    libcst.GeneratorExp,
    libcst.IfExp,
    libcst.Imaginary,
    libcst.Integer,
    libcst.Lambda,
    libcst.List,
    libcst.ListComp,
    libcst.Name,
    libcst.Set,
    libcst.SetComp,
    libcst.SimpleString,
    libcst.StarredElement,
    libcst.Subscript,
    libcst.Tuple,
    libcst.UnaryOperation,
    libcst.Yield,
]
MATCH_ON = (
    getattr(libcst.matchers, type_.__name__)() for type_ in t.get_args(NODE_TYPES)
)

# The innermost parens should not be removed in some cases, as they are
# required in some contexts.
PRESERVE_INNERMOST_PAREN_TYPES: tuple[type[libcst.CSTNode], ...] = (
    # list of tuples:
    #   [(1, 2), (3, 4)] != [1, 2, 3, 4]
    libcst.Tuple,
    # generator expression passed to a function call:
    #   foo((x % 2 for x in range(10)), bar)
    libcst.GeneratorExp,
    # parens define precedence:
    #   (1 + 2) * 3 != 1 + 2 * 3
    libcst.BinaryOperation,
    libcst.UnaryOperation,
    # parens are required for usage of the results:
    #   (foo() if x else bar())["baz"]
    #   (await foo())["bar"]
    libcst.IfExp,
    libcst.Await,
    # direct access to attributes of integers and floats requires parens:
    #   (1).bit_length()
    libcst.Integer,
    libcst.Float,
)


class UnnecessaryParenthesesFixer(libcst.matchers.MatcherDecoratableTransformer):
    METADATA_DEPENDENCIES = (libcst.metadata.PositionProvider,)

    def _how_many_parens_same_line(self, node: libcst.CSTNode) -> int:
        if not node.lpar:
            return 0

        max_offset = -1
        for offset in range(len(node.lpar)):
            lpar_line = self.get_metadata(
                libcst.metadata.PositionProvider, node.lpar[-(offset + 1)]
            ).start.line
            rpar_line = self.get_metadata(
                libcst.metadata.PositionProvider, node.rpar[offset]
            ).start.line

            if lpar_line != rpar_line:
                break
            max_offset = offset
        return max_offset + 1

    @libcst.matchers.leave(libcst.matchers.OneOf(*MATCH_ON))
    def modify_parenthesized_node(
        self, original_node: NODE_TYPES, updated_node: NODE_TYPES
    ) -> NODE_TYPES:
        num_parens_to_unwrap = self._how_many_parens_same_line(original_node)
        if isinstance(original_node, PRESERVE_INNERMOST_PAREN_TYPES):
            num_parens_to_unwrap -= 1
        if num_parens_to_unwrap <= 0:
            return updated_node
        return updated_node.with_changes(
            lpar=updated_node.lpar[:-num_parens_to_unwrap],
            rpar=updated_node.rpar[num_parens_to_unwrap:],
        )
