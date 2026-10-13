import { UploadIcon } from 'lucide-react'
import { useState, type DragEvent } from 'react'

import { cn } from '@/lib/utils'
import { MAX_FILES } from '@/lib/constants'

interface Props {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

export function UploadDropzone({ onFiles, disabled }: Props) {
  const [dragging, setDragging] = useState(false)

  const onDrop = (event: DragEvent) => {
    event.preventDefault()
    setDragging(false)
    if (!disabled) onFiles(Array.from(event.dataTransfer.files))
  }

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
        dragging ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/60',
        disabled && 'pointer-events-none opacity-50'
      )}
    >
      <UploadIcon className="size-8 text-muted-foreground" />
      <span className="font-medium">Drop images here or click to choose</span>
      <span className="text-sm text-muted-foreground">
        JPEG or PNG, up to 10 MB each, up to {MAX_FILES} files per upload
      </span>
      <input
        type="file"
        multiple
        accept="image/jpeg,image/png"
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          onFiles(Array.from(e.target.files ?? []))
          e.target.value = '' // allow picking the same file again
        }}
      />
    </label>
  )
}
