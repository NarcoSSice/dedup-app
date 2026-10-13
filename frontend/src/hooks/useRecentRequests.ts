import { useCallback, useState } from 'react'

import { loadRecentRequests, saveRecentRequest, type RecentRequest } from '@/lib/history'

export function useRecentRequests() {
  const [recent, setRecent] = useState<RecentRequest[]>(loadRecentRequests)

  const addRecent = useCallback((request: RecentRequest) => {
    setRecent(saveRecentRequest(request))
  }, [])

  return { recent, addRecent }
}
