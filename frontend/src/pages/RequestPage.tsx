import { Loader2Icon, SearchXIcon } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router'

import { ApiErrorAlert } from '@/components/ApiErrorAlert'
import { DuplicateGroupCard } from '@/components/DuplicateGroupCard'
import { RequestSummary } from '@/components/RequestSummary'
import { ThresholdSlider } from '@/components/ThresholdSlider'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useDebounce } from '@/hooks/useDebounce'
import { useGetDuplicatesQuery } from '@/lib/api'
import { errorMessage, errorStatus } from '@/lib/api-errors'
import { DEFAULT_THRESHOLD } from '@/lib/constants'
import { saveRecentRequest } from '@/lib/history'

export function RequestPage() {
  const { requestId = '' } = useParams()
  const [threshold, setThreshold] = useState(DEFAULT_THRESHOLD)

  const debouncedThreshold = useDebounce(threshold, 300)
  const { data, error, isLoading, isFetching, refetch } = useGetDuplicatesQuery(
    requestId,
    debouncedThreshold
  )

  useEffect(() => {
    if (!data) return
    saveRecentRequest({
      requestId: data.request_id,
      openedAt: new Date().toISOString(),
      accepted: data.accepted,
      rejected: data.rejected.length + data.failed.length,
    })
  }, [data?.request_id])

  if (isLoading) return <PageSkeleton />

  if (!data) {
    const notFound = errorStatus(error) === 404
    return (
      <ApiErrorAlert
        title={notFound ? 'Request not found' : 'Could not load results'}
        message={errorMessage(error)}
        onRetry={notFound ? undefined : refetch}
      />
    )
  }

  const processing = data.status === 'processing'

  return (
    <div className="space-y-6">
      <RequestSummary result={data} />

      <Card>
        <CardContent>
          <ThresholdSlider value={threshold} onChange={setThreshold} />
        </CardContent>
      </Card>

      {error && <ApiErrorAlert message={errorMessage(error)} onRetry={refetch} />}

      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">Duplicates</h2>
          {isFetching && !processing && (
            <Loader2Icon className="size-4 animate-spin text-muted-foreground" />
          )}
        </div>

        {processing ? (
          <div className="space-y-3">
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2Icon className="size-4 animate-spin" />
              Processing images, results will appear automatically…
            </p>
            <Skeleton className="h-48 w-full" />
          </div>
        ) : data.groups.length ? (
          data.groups.map((group) => (
            <DuplicateGroupCard key={group.image_id} group={group} requestId={data.request_id} />
          ))
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
              <SearchXIcon className="size-8 text-muted-foreground" />
              <p className="font-medium">{data.message ?? 'No duplicates found'}</p>
              <p className="text-sm text-muted-foreground">
                Try lowering the similarity threshold to see looser matches.
              </p>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  )
}

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-48 w-full" />
    </div>
  )
}
