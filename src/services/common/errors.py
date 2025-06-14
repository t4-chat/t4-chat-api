class NotFoundError(Exception):
    def __init__(self, resource_name: str, message: str):
        self.message = f"{resource_name} not found. {message}"
        super().__init__(self.message)


class ForbiddenError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BudgetExceededError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class LimitsExceededError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidInputError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
