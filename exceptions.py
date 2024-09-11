class CategoryNotFoundException(Exception):
    """Raised when a category is not found"""
    pass

class SavingGoalAlreadyExistsException(Exception):
    """Raised when trying to create a saving goal that already exists"""
    pass

class SavingGoalNotFoundException(Exception):
    """Raised when a saving goal is not found"""
    pass

class UnauthorizedAccessException(Exception):
    """Raised when a user tries to access or modify a resource they're not authorized for"""
    pass