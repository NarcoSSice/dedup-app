import { AlertCircleIcon, XIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { SelectedFile } from '@/hooks/useSelectedFiles'
import { useObjectUrl } from '@/hooks/useObjectUrl'
import { formatSize } from '@/lib/files'
import { cn } from '@/lib/utils'

interface Props {
  files: SelectedFile[]
  onRemove: (key: string) => void
  disabled?: boolean
}

export function FilePreviewGrid({ files, onRemove, disabled }: Props) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
      {files.map((item) => (
        <FilePreview key={item.key} item={item} onRemove={onRemove} disabled={disabled} />
      ))}
    </ul>
  )
}

function FilePreview({
  item,
  onRemove,
  disabled,
}: {
  item: SelectedFile
  onRemove: (key: string) => void
  disabled?: boolean
}) {
  const previewUrl = useObjectUrl(item.file)

  return (
    <li
      className={cn(
        'relative overflow-hidden rounded-lg border bg-background',
        item.error && 'border-destructive/60'
      )}
    >
      <div className="flex aspect-square items-center justify-center bg-muted">
        {item.error ? (
          <AlertCircleIcon className="size-8 text-destructive" />
        ) : (
          previewUrl && (
            <img src={previewUrl} alt={item.file.name} className="size-full object-cover" />
          )
        )}
      </div>
      <div className="space-y-0.5 p-2">
        <p className="truncate text-xs font-medium" title={item.file.name}>
          {item.file.name}
        </p>
        <p className={cn('text-xs', item.error ? 'text-destructive' : 'text-muted-foreground')}>
          {item.error ?? formatSize(item.file.size)}
        </p>
      </div>
      <Button
        size="icon-xs"
        variant="secondary"
        className="absolute top-1.5 right-1.5"
        onClick={() => onRemove(item.key)}
        disabled={disabled}
        aria-label={`Remove ${item.file.name}`}
      >
        <XIcon />
      </Button>
    </li>
  )
}
