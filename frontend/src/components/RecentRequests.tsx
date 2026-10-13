import { HistoryIcon } from 'lucide-react'
import { Link } from 'react-router'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { RecentRequest } from '@/lib/history'

export function RecentRequests({ requests }: { requests: RecentRequest[] }) {
  if (!requests.length) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <HistoryIcon className="size-4" />
          Recent requests
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y">
          {requests.map((r) => (
            <li key={r.requestId}>
              <Link
                to={`/requests/${r.requestId}`}
                className="flex flex-col gap-1 py-2 hover:text-primary sm:flex-row sm:items-center sm:justify-between"
              >
                <span className="truncate font-mono text-sm">{r.requestId}</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {r.accepted} accepted · {r.rejected} rejected ·{' '}
                  {new Date(r.openedAt).toLocaleString()}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
