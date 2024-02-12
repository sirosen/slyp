from __future__ import annotations

import typing as t

import libcst
import libcst.matchers

# SimpleWhitespace defines whitespace as seen between tokens in most contexts
# it can contain newlines *if* there is a preceding backslash escape
SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER = libcst.matchers.SimpleWhitespace(
    value=libcst.matchers.MatchIfTrue(lambda x: "\n" not in x)
)

PARENT_NODE_REQUIRES_INNERMOST_PARENS_MATCHER = libcst.matchers.OneOf(
    libcst.matchers.Arg(star=libcst.matchers.DoNotCare()),
    libcst.matchers.UnaryOperation(),
)

ParenFixNodeTypes = t.Union[
    libcst.Name,
    libcst.Attribute,
    libcst.Subscript,
    libcst.Call,
    libcst.Dict,
    libcst.DictComp,
    libcst.List,
    libcst.ListComp,
    libcst.Set,
    libcst.SetComp,
    libcst.Tuple,
    libcst.UnaryOperation,
    libcst.BinaryOperation,
    libcst.Comparison,
    libcst.Ellipsis,
    libcst.Integer,
    libcst.Float,
    libcst.SimpleString,
    libcst.ConcatenatedString,
    libcst.FormattedString,
    libcst.Lambda,
    libcst.Yield,
    libcst.GeneratorExp,
    libcst.IfExp,
    libcst.Await,
]
PFN = t.TypeVar("PFN", bound=ParenFixNodeTypes)


class SlypTransformer(libcst.CSTTransformer):
    METADATA_DEPENDENCIES = (
        libcst.metadata.PositionProvider,
        libcst.metadata.ParentNodeProvider,
    )

    def _singular_parens_are_same_line(
        self, node: libcst.With | libcst.ImportFrom
    ) -> bool:
        if node.lpar is not None and libcst.matchers.matches(
            node.lpar, libcst.matchers.LeftParen()
        ):
            lpar_line = self.get_metadata(
                libcst.metadata.PositionProvider, node.lpar  # type: ignore[arg-type]
            ).start.line
            rpar_line = self.get_metadata(
                libcst.metadata.PositionProvider, node.rpar  # type: ignore[arg-type]
            ).start.line
            return lpar_line == rpar_line

        return False

    def _how_many_parens_same_line(self, node: PFN) -> int:
        """
        Determine how many parens are on the same line for a node.

        Start by finding the "max offset" into the paren lists where the lpar and rpar
        are on the same line. The range is [-1 , len(paren_list)] ; then add one.
        """
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

    def modify_parenthesized_node(
        self, original_node: PFN, updated_node: PFN, *, preserve_innermost: bool = False
    ) -> PFN:
        num_parens_to_unwrap: int | None = None
        if not preserve_innermost:
            # **optimization**
            #
            # if there is a parent node to check, pick up on the number of parens to
            # unwrap first -- this saves the work of accessing the parent node when it's
            # avoidable and we can short-circuit
            #
            # based on timings, accessing parent nodes seems slower than finding paren
            # linenos
            num_parens_to_unwrap = self._how_many_parens_same_line(original_node)
            if num_parens_to_unwrap <= 0:
                return updated_node

            parent = self.get_metadata(
                libcst.metadata.ParentNodeProvider, original_node
            )
            # check if the parent of the node is *-expansion of an arg
            if libcst.matchers.matches(
                parent, PARENT_NODE_REQUIRES_INNERMOST_PARENS_MATCHER
            ):
                preserve_innermost = True

        if preserve_innermost and len(original_node.lpar) == 1:
            return updated_node

        if num_parens_to_unwrap is None:
            num_parens_to_unwrap = self._how_many_parens_same_line(original_node)
        if preserve_innermost:
            num_parens_to_unwrap -= 1
        if num_parens_to_unwrap <= 0:
            return updated_node
        return updated_node.with_changes(  # type: ignore[return-value]
            lpar=updated_node.lpar[:-num_parens_to_unwrap],
            rpar=updated_node.rpar[num_parens_to_unwrap:],
        )

    # identifiers, attributes, lookups, and calls

    def leave_Name(
        self, original_node: libcst.Name, updated_node: libcst.Name
    ) -> libcst.Name:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Attribute(
        self, original_node: libcst.Attribute, updated_node: libcst.Attribute
    ) -> libcst.Attribute:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Subscript(
        self, original_node: libcst.Subscript, updated_node: libcst.Subscript
    ) -> libcst.Subscript:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Call(
        self, original_node: libcst.Call, updated_node: libcst.Call
    ) -> libcst.Call:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    # collections

    def leave_Dict(
        self, original_node: libcst.Dict, updated_node: libcst.Dict
    ) -> libcst.Dict:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_DictComp(
        self, original_node: libcst.DictComp, updated_node: libcst.DictComp
    ) -> libcst.DictComp:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_List(
        self, original_node: libcst.List, updated_node: libcst.List
    ) -> libcst.List:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_ListComp(
        self, original_node: libcst.ListComp, updated_node: libcst.ListComp
    ) -> libcst.ListComp:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Set(
        self, original_node: libcst.Set, updated_node: libcst.Set
    ) -> libcst.Set:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_SetComp(
        self, original_node: libcst.SetComp, updated_node: libcst.SetComp
    ) -> libcst.SetComp:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Tuple(
        self, original_node: libcst.Tuple, updated_node: libcst.Tuple
    ) -> libcst.Tuple:
        # list of tuples:
        #   [(1, 2), (3, 4)] != [1, 2, 3, 4]
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    # operators

    def leave_UnaryOperation(
        self, original_node: libcst.UnaryOperation, updated_node: libcst.UnaryOperation
    ) -> libcst.UnaryOperation:
        # parens define precedence
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_BinaryOperation(
        self,
        original_node: libcst.BinaryOperation,
        updated_node: libcst.BinaryOperation,
    ) -> libcst.BinaryOperation:
        # parens define precedence
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_Comparison(
        self, original_node: libcst.Comparison, updated_node: libcst.Comparison
    ) -> libcst.Comparison:
        # parens define precedence
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    # literals, constants, and strings

    def leave_Ellipsis(
        self, original_node: libcst.Ellipsis, updated_node: libcst.Ellipsis
    ) -> libcst.Ellipsis:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_Integer(
        self,
        original_node: libcst.Integer,
        updated_node: libcst.Integer,
    ) -> libcst.Integer:
        # direct access to attributes of integers and floats requires parens:
        #   (1).bit_length()
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_Float(
        self,
        original_node: libcst.Float,
        updated_node: libcst.Float,
    ) -> libcst.Float:
        # direct access to attributes of integers and floats requires parens:
        #   (1).bit_length()
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_SimpleString(
        self, original_node: libcst.SimpleString, updated_node: libcst.SimpleString
    ) -> libcst.SimpleString:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    def leave_ConcatenatedString(
        self,
        original_node: libcst.ConcatenatedString,
        updated_node: libcst.ConcatenatedString,
    ) -> libcst.ConcatenatedString | libcst.SimpleString:
        new_node = updated_node
        # if the node is parenthesized, potentially strip parens
        if original_node.lpar:
            new_node = self.modify_parenthesized_node(original_node, updated_node)

        # if the node is a pair of simple strings with no newline between them,
        # this may be a chance to join them into a single string node
        if libcst.matchers.matches(
            new_node,
            libcst.matchers.ConcatenatedString(
                whitespace_between=SIMPLE_WHITESPACE_NO_NEWLINE_MATCHER,
                left=libcst.matchers.SimpleString(),
                right=libcst.matchers.SimpleString(),
            ),
        ):
            # check that the left and right match in their prefix and quote characters,
            # and forbid this change (for now) when one of the two is a multiline string
            # (TODO: consider when it might be safe to join multiline strings)
            #
            # the restriction against differing quote characters allows us to avoid any
            # attempt to manipulate unescaped quotes in the string values
            # having done this verification, join the strings into a single node,
            # preserving the prefix and quote style
            left: libcst.SimpleString = new_node.left  # type: ignore[assignment]
            right: libcst.SimpleString = new_node.right  # type: ignore[assignment]
            if (
                (
                    left.prefix == right.prefix
                    or {left.prefix, right.prefix}.issubset({"br", "rb"})
                )
                and left.quote == right.quote
                and left.quote in {"'", '"'}
            ):
                return libcst.SimpleString(
                    lpar=new_node.lpar,
                    rpar=new_node.rpar,
                    value=left.prefix
                    + left.quote
                    + left.raw_value
                    + right.raw_value
                    + left.quote,
                )

        return new_node

    def leave_FormattedString(
        self,
        original_node: libcst.FormattedString,
        updated_node: libcst.FormattedString,
    ) -> libcst.FormattedString:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

    # expressions

    def leave_Lambda(
        self, original_node: libcst.Lambda, updated_node: libcst.Lambda
    ) -> libcst.Lambda:
        # lambdas can have attributes:
        #   (lambda x: x + 1).__code__
        # and can be called (although it's sort of pointless):
        #   (lambda x: x + 1)(2)
        # and also may parse (for a human) less ambiguously with parens:
        #   (lambda x: x + 1), 2
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_Yield(
        self, original_node: libcst.Yield, updated_node: libcst.Yield
    ) -> libcst.Yield:
        new_node = updated_node
        # inject whitespace if a yield is used without trailing space
        # e.g. `yield('foo')` -> `yield ('foo')`
        if new_node.value is not None and (
            new_node.whitespace_after_yield.empty  # type: ignore[union-attr]
        ):
            new_node = new_node.with_changes(
                whitespace_after_yield=libcst.SimpleWhitespace(" ")
            )
        # expression nesting:
        #   return (yield from inner())
        if len(new_node.lpar) < 2:
            return new_node
        return self.modify_parenthesized_node(
            original_node,
            new_node,
            preserve_innermost=True,
        )

    def leave_GeneratorExp(
        self, original_node: libcst.GeneratorExp, updated_node: libcst.GeneratorExp
    ) -> libcst.GeneratorExp:
        # generator expression passed to a function call:
        #   foo((x % 2 for x in range(10)), bar)
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_IfExp(
        self, original_node: libcst.IfExp, updated_node: libcst.IfExp
    ) -> libcst.IfExp:
        # parens are required for usage of the results:
        #   (foo() if x else bar())["baz"]
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_Await(
        self, original_node: libcst.Await, updated_node: libcst.Await
    ) -> libcst.Await:
        # parens are required for usage of the results:
        #   (await foo())["bar"]
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
            preserve_innermost=True,
        )

    def leave_Match(
        self, original_node: libcst.Match, updated_node: libcst.Match
    ) -> libcst.Match:
        # inject whitespace if missing
        # ensures that `match(x): ...` converts to `match x: ...`
        if not original_node.whitespace_after_match.empty:
            return updated_node
        return updated_node.with_changes(
            whitespace_after_match=libcst.SimpleWhitespace(" ")
        )

    def leave_With(
        self, original_node: libcst.With, updated_node: libcst.With
    ) -> libcst.With:
        # remove parens from `with (foo): ...` as long as they are on the same line
        changes: dict[str, t.Any] = {}
        if original_node.whitespace_after_with.empty:
            changes["whitespace_after_with"] = libcst.SimpleWhitespace(" ")
        if self._singular_parens_are_same_line(original_node):
            changes["lpar"] = libcst.MaybeSentinel.DEFAULT
            changes["rpar"] = libcst.MaybeSentinel.DEFAULT
        if changes:
            return updated_node.with_changes(**changes)
        return updated_node

    def leave_If(self, original_node: libcst.If, updated_node: libcst.If) -> libcst.If:
        # inject whitespace if missing
        # ensures that `if(x): ...` converts to `if x: ...`
        if not original_node.whitespace_before_test.empty:
            return updated_node
        return updated_node.with_changes(
            whitespace_before_test=libcst.SimpleWhitespace(" ")
        )

    def leave_ImportFrom(
        self, original_node: libcst.ImportFrom, updated_node: libcst.ImportFrom
    ) -> libcst.ImportFrom:
        changes: dict[str, t.Any] = {}
        if original_node.whitespace_after_import.empty:
            changes["whitespace_after_import"] = libcst.SimpleWhitespace(" ")
        if self._singular_parens_are_same_line(original_node):
            changes["lpar"] = None
            changes["rpar"] = None
        if changes:
            return updated_node.with_changes(**changes)
        return updated_node
