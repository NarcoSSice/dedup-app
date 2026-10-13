import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'

import { ApiError } from '@/lib/api-errors'
import { API_URL, POLL_INTERVAL_MS } from '@/lib/constants'
import type { DuplicatesResponse, UploadResponse } from '@/types/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init)
  const body = await response.json().catch(() => undefined)
  if (!response.ok) throw new ApiError(response.status, body?.detail)
  return body as T
}

export function useUploadImagesMutation() {
  return useMutation({
    mutationFn: (files: File[]) => {
      const body = new FormData()
      files.forEach((file) => body.append('files', file))
      return request<UploadResponse>('/images', { method: 'POST', body })
    },
  })
}

export function useGetDuplicatesQuery(requestId: string, threshold: number) {
  return useQuery({
    queryKey: ['duplicates', requestId, threshold],
    queryFn: ({ signal }) =>
      request<DuplicatesResponse>(
        `/duplicates/${encodeURIComponent(requestId)}?threshold=${threshold}`,
        { signal }
      ),

    placeholderData: keepPreviousData,
    refetchInterval: ({ state }) =>
      state.data?.status === 'processing' && !state.error ? POLL_INTERVAL_MS : false,
  })
}

export const imageUrl = (imageId: string, thumbnail = false) =>
  `${API_URL}/images/${imageId}${thumbnail ? '?thumb=true' : ''}`
