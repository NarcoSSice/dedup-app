import { CheckIcon, CopyIcon, Loader2Icon } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { REJECT_REASON_LABELS } from '@/lib/files'
import type { DuplicatesResponse } from '@/types/api'

/** Request ID, processing state and what happened to every uploaded file. */
export function RequestSummary({ result }: { result: DuplicatesResponse }) {
  const processing = result.status === 'processing'
  const notProcessed = [
    ...result.rejected.map((r) => ({
      filename: r.filename,
      reason: REJECT_REASON_LABELS[r.reason],
    })),
    ...result.failed.map((f) => ({ filename: f.filename, reason: 'Could not be processed' })),
  ]

  return (
    <Card>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Request</span>
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm break-all">
            {result.request_id}
          </code>
          <CopyButton text={result.request_id} />
        </div>

        <div className="flex flex-wrap gap-2">
          {processing ? (
            <Badge variant="outline">
              <Loader2Icon className="animate-spin" />
              Processing
            </Badge>
          ) : (
            <Badge variant="outline">
              <CheckIcon />
              Done
            </Badge>
          )}
          <Badge variant="secondary">{result.accepted} accepted</Badge>
          <Badge variant={notProcessed.length ? 'destructive' : 'secondary'}>
            {notProcessed.length} rejected
          </Badge>
        </div>

        {notProcessed.length > 0 && (
          <ul className="space-y-1 text-sm">
            {notProcessed.map((f, i) => (
              <li key={`${f.filename}-${i}`} className="flex gap-2">
                <span className="truncate font-medium">{f.filename}</span>
                <span className="shrink-0 text-destructive">{f.reason}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard blocked: the ID is still selectable by hand
    }
  }

  return (
    <Button variant="ghost" size="icon-xs" onClick={copy} aria-label="Copy request ID">
      {copied ? <CheckIcon /> : <CopyIcon />}
    </Button>
  )
}
