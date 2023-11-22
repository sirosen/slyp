import libcst


class ErrorCollectingVisitor(libcst.CSTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.filename: str = "<unset>"
        self.errors: set[tuple[int, str, str]] = set()
