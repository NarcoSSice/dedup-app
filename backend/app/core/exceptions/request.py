from fastapi import HTTPException


class RequestNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Request not found")
