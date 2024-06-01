class InvalidCredentials(Exception):
    """
    Raised when the provided email or password are not valid
    """
    def __init__(self, message="Incorrect email or password"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class InvalidToken(Exception):
    """
    Raised when the provided token is not valid
    """
    def __init__(self, message="Could not validate token"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class NotEnoughPrivileges(Exception):
    """
    Raised when user has not enough privileges
    """
    def __init__(self, message="Unauthorized: not enough privileges"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'