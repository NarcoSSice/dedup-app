export type RejectReason = 'file_too_large' | 'unsupported_format' | 'invalid_image' | 'empty_file'

export interface RejectedFile {
  filename: string
  reason: RejectReason
}

export interface UploadResponse {
  request_id: string
  accepted: number
  rejected: RejectedFile[]
}

export interface Duplicate {
  image_id: string
  filename: string
  score: number
  source_request_id: string
}

export interface DuplicateGroup {
  image_id: string
  filename: string
  duplicates: Duplicate[]
}

export interface FailedImage {
  filename: string
  reason: string | null
}

export type RequestStatus = 'processing' | 'done'

export interface DuplicatesResponse {
  request_id: string
  status: RequestStatus
  accepted: number
  rejected: RejectedFile[]
  groups: DuplicateGroup[]
  failed: FailedImage[]
  message: string | null
}
