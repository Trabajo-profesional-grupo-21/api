class UserAlreadyExists(Exception):
    """
    Raised when the provided email is not unique
    """
    def __init__(self, message="Email already in use"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class UserNotFound(Exception):
    """
    Raised when user not found
    """
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'