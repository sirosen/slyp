import ast


class ErrorRecordingVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.errors: set[tuple[int, str]] = set()
