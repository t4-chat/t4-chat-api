class NotFoundError(Exception):
    """Exception raised when a resource is not found"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
