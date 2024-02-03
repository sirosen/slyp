from __future__ import annotations

import typing as t

import libcst
import libcst.matchers

NodeTypes = t.Union[
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
N = t.TypeVar("N", bound=NodeTypes)


class UnnecessaryParenthesesFixer(libcst.CSTTransformer):
    METADATA_DEPENDENCIES = (
        libcst.metadata.PositionProvider,
        libcst.metadata.ParentNodeProvider,
    )

    def __init__(self) -> None:
        self.in_star_arg: int = 0

    def visit_Arg(self, node: libcst.Arg) -> None:
        if node.star:
            self.in_star_arg += 1

    def leave_Arg(
        self, original_node: libcst.Arg, updated_node: libcst.Arg
    ) -> libcst.Arg:
        if original_node.star:
            self.in_star_arg -= 1
        return updated_node

    def _how_many_parens_same_line(self, node: N) -> int:
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
        self, original_node: N, updated_node: N, *, preserve_innermost: bool = False
    ) -> N:
        if not preserve_innermost and self.in_star_arg > 0:
            # check if the parent of the node is *-expansion of an arg
            parent = self.get_metadata(
                libcst.metadata.ParentNodeProvider, original_node
            )
            if isinstance(parent, libcst.Arg) and bool(parent.star):
                preserve_innermost = True

        if preserve_innermost and len(original_node.lpar) == 1:
            return updated_node

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
        # parens define precedence:
        #   ~ x * y != (~x) * y
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
        # parens define precedence:
        #   ~ x * y != (~x) * y
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
        # parens define precedence:
        #   (x is y) in truefalsecontainer
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
    ) -> libcst.ConcatenatedString:
        if not original_node.lpar:
            return updated_node
        return self.modify_parenthesized_node(original_node, updated_node)

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
        # expression nesting:
        #   return (yield from inner())
        if len(original_node.lpar) < 2:
            return updated_node
        return self.modify_parenthesized_node(
            original_node,
            updated_node,
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
