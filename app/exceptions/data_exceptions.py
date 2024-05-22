class BlobAlreadyExists(Exception):
    """
    Raised when the provided video_name is not unique
    """
    def __init__(self, message="Video or image already exists"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class VideoDataNotReady(Exception):
    """
    Raised when asked batch is not ready
    """
    def __init__(self, message="Batch data not ready"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class ImageDataError(Exception):
    """
    Raised when there's an error processing image
    """
    def __init__(self, message="Image processing error"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

class BlobNotFound(Exception):
    """
    Raised when asked batch is not ready
    """
    def __init__(self, message="Video or image not found"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'