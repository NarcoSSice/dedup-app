import enum


class ImageStatus(enum.StrEnum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


class RequestStatus(enum.StrEnum):
    processing = "processing"
    done = "done"


class RejectReason(enum.StrEnum):
    file_too_large = "file_too_large"
    unsupported_format = "unsupported_format"
    invalid_image = "invalid_image"
    empty_file = "empty_file"
