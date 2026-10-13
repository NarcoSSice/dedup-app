import { Link } from 'react-router'

import { ImageThumb } from '@/components/ImageThumb'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { DuplicateGroup } from '@/types/api'

interface Props {
  group: DuplicateGroup
  requestId: string
}

/** The uploaded image on the left, its duplicates with similarity scores on the right. */
export function DuplicateGroupCard({ group, requestId }: Props) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 md:flex-row">
        <div className="w-full shrink-0 space-y-2 md:w-48">
          <Badge>Uploaded</Badge>
          <ImageThumb imageId={group.image_id} filename={group.filename} />
          <p className="truncate text-sm font-medium" title={group.filename}>
            {group.filename}
          </p>
        </div>

        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-sm text-muted-foreground">
            {group.duplicates.length} duplicate{group.duplicates.length > 1 && 's'}
          </p>
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {group.duplicates.map((dup) => (
              <li key={dup.image_id} className="space-y-1.5">
                <ImageThumb imageId={dup.image_id} filename={dup.filename} />
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-xs font-medium" title={dup.filename}>
                    {dup.filename}
                  </p>
                  <Badge variant="secondary" title="Similarity score">
                    {dup.score.toFixed(3)}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {dup.source_request_id === requestId ? (
                    'From this upload'
                  ) : (
                    <Link
                      to={`/requests/${dup.source_request_id}`}
                      className="underline-offset-2 hover:underline"
                    >
                      From an earlier upload
                    </Link>
                  )}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
