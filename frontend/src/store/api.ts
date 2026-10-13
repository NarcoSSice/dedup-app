import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

import { API_URL } from '@/lib/constants'
import type { DuplicatesResponse, UploadResponse } from '@/types/api'

interface DuplicatesParams {
  requestId: string
  threshold: number
}

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: API_URL }),
  endpoints: (builder) => ({
    uploadImages: builder.mutation<UploadResponse, File[]>({
      query: (files) => {
        const body = new FormData()
        files.forEach((file) => body.append('files', file))
        return { url: '/images', method: 'POST', body }
      },
    }),

    getDuplicates: builder.query<DuplicatesResponse, DuplicatesParams>({
      query: ({ requestId, threshold }) => ({
        url: `/duplicates/${encodeURIComponent(requestId)}`,
        params: { threshold },
      }),
    }),
  }),
})

export const { useUploadImagesMutation, useGetDuplicatesQuery } = api

export const imageUrl = (imageId: string, thumbnail = false) =>
  `${API_URL}/images/${imageId}${thumbnail ? '?thumb=true' : ''}`
