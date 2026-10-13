import { RECENT_REQUESTS_LIMIT } from '@/lib/constants'

export interface RecentRequest {
  requestId: string
  openedAt: string
  accepted: number
  rejected: number
}

const STORAGE_KEY = 'dedup:recent-requests'

// localStorage can be unavailable (private mode, blocked storage): history is
// a convenience, so failures just mean "no history".
export function loadRecentRequests(): RecentRequest[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as RecentRequest[]) : []
  } catch {
    return []
  }
}

export function saveRecentRequest(request: RecentRequest): void {
  const updated = [
    request,
    ...loadRecentRequests().filter((r) => r.requestId !== request.requestId),
  ].slice(0, RECENT_REQUESTS_LIMIT)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // ignore, see above
  }
}
