class NotFoundError(Exception):
    """Exception raised when a resource is not found"""
    def __init__(self, resource_name: str, resource_id: int):
        self.message = f"{resource_name} with ID {resource_id} not found"
        super().__init__(self.message)
        
