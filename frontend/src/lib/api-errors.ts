import { MAX_FILE_BYTES, MAX_FILES } from '@/lib/constants'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, detail: unknown) {
    super(`HTTP ${status}`)
    this.status = status
    this.detail = detail
  }
}

export function errorStatus(error: Error | null): number | undefined {
  return error instanceof ApiError ? error.status : undefined
}

export function errorMessage(error: Error | null): string {
  // fetch rejects with a TypeError when the server cannot be reached at all
  if (error instanceof TypeError) {
    return 'Server is unreachable. Check that the backend is running and try again.'
  }

  const status = errorStatus(error)
  if (status === 404) return 'Request not found. Check the request ID.'
  if (status === 413) {
    return `Upload is too large: at most ${MAX_FILES} files, ${MAX_FILE_BYTES / 1024 / 1024} MB each.`
  }
  if (status === 422) return 'The server rejected the request parameters.'
  if (status === 502 || status === 503 || status === 504) {
    return 'Backend is not available right now. Try again in a moment.'
  }
  if (status && status >= 500) return 'Server error. Try again later.'

  if (error instanceof ApiError && error.detail) return String(error.detail)
  return 'Something went wrong'
}
