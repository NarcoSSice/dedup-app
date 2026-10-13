from fastapi import HTTPException


class ImageNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Image not found")


class TooManyFilesException(HTTPException):
    def __init__(self, max_files: int):
        super().__init__(
            status_code=413, detail=f"Too many files, max {max_files} per request"
        )


class InvalidImageError(ValueError):
    """A single uploaded file is rejected; carries the reason for the response."""

    def __init__(self, reason):
        super().__init__(reason.value)
        self.reason = reason
