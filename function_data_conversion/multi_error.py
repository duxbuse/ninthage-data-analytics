class Multi_Error(Exception):
    def __init__(self, errors: list[Exception]) -> None:
        self.errors = errors
        super().__init__(self.errors)

    def __str__(self) -> str:

        return "\n".join([str(x) for x in self.errors])
