import type { SerializedError } from '@reduxjs/toolkit'
import type { FetchBaseQueryError } from '@reduxjs/toolkit/query'

import { MAX_FILE_BYTES, MAX_FILES } from '@/lib/constants'

type ApiError = FetchBaseQueryError | SerializedError | undefined

export function errorStatus(error: ApiError): number | undefined {
  if (!error || !('status' in error)) return undefined
  if (typeof error.status === 'number') return error.status
  if (error.status === 'PARSING_ERROR') return error.originalStatus
  return undefined
}

export function errorMessage(error: ApiError): string {
  if (!error) return 'Something went wrong'
  if ('status' in error && error.status === 'FETCH_ERROR') {
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

  if ('data' in error && typeof error.data === 'object' && error.data && 'detail' in error.data) {
    return String(error.data.detail)
  }
  return 'Something went wrong'
}
