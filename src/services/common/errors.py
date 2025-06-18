class NotFoundError(Exception):
    def __init__(self, resource_name: str, message: str):
        self.status_code = 404
        self.message = f"{resource_name} not found. {message}"
        super().__init__(self.message)


class ForbiddenError(Exception):
    def __init__(self, message: str):
        self.status_code = 403
        self.message = message
        super().__init__(self.message)


class BudgetExceededError(Exception):
    def __init__(self, message: str):
        self.status_code = 402
        self.message = message
        super().__init__(self.message)


class LimitsExceededError(Exception):
    def __init__(self, message: str):
        self.status_code = 402
        self.message = message
        super().__init__(self.message)


class InvalidInputError(Exception):
    def __init__(self, message: str):
        self.status_code = 400
        self.message = message
        super().__init__(self.message)

class BadRequestError(Exception):
    def __init__(self, message: str):
        self.status_code = 400
        self.message = message
        super().__init__(self.message)

class NoAvailableHostError(Exception):
    def __init__(self, message: str):
        self.status_code = 400
        self.message = message
        super().__init__(self.message)

class ModelApiError(Exception):
    def __init__(self, message: str):
        self.message = message
        self.status_code = 424
        super().__init__(self.message)


class BYOKError(Exception):
    def __init__(self, message: str = "This model is only available with BYOK"):
        self.status_code = 402
        self.message = message
        super().__init__(self.message)
