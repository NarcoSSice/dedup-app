// Same limits as the backend, checked on the client before upload.
export const MAX_FILE_BYTES = 10 * 1024 * 1024
export const MAX_FILES = 50
export const ACCEPTED_TYPES = ['image/jpeg', 'image/png']

// Backend default (DUPLICATE_THRESHOLD); the slider starts here.
export const DEFAULT_THRESHOLD = 0.8
export const MIN_THRESHOLD = 0.5

export const POLL_INTERVAL_MS = 1000
export const RECENT_REQUESTS_LIMIT = 10

export const API_URL = '/api'
