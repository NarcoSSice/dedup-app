import { ACCEPTED_TYPES, MAX_FILE_BYTES } from '@/lib/constants'
import type { RejectReason } from '@/types/api'

export const REJECT_REASON_LABELS: Record<RejectReason, string> = {
  file_too_large: 'Larger than 10 MB',
  unsupported_format: 'Not a JPEG or PNG',
  invalid_image: 'Corrupted image',
  empty_file: 'Empty file',
}

export function validateFile(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) return REJECT_REASON_LABELS.unsupported_format
  if (file.size > MAX_FILE_BYTES) return REJECT_REASON_LABELS.file_too_large
  if (file.size === 0) return REJECT_REASON_LABELS.empty_file
  return null
}

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export const fileKey = (file: File) => `${file.name}:${file.size}:${file.lastModified}`
