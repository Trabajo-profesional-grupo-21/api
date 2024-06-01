class InvalidParameter(Exception):
    """
    Raised when the provided parameter is not valid
    """
    def __init__(self, message="Incorrect parameter"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class DbError(Exception):
    """
    Raised when DB operations fail
    """
    def __init__(self, message="Error DB Operation"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'