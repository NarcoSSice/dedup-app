import { useState } from 'react'

import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { imageUrl } from '@/store/api'

interface Props {
  imageId: string
  filename: string
}

/** Thumbnail that opens the full-size original on click. */
export function ImageThumb({ imageId, filename }: Props) {
  const [failed, setFailed] = useState(false)

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="block aspect-square w-full overflow-hidden rounded-md border bg-muted transition hover:opacity-90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
          title="Open full size"
        >
          {failed ? (
            <span className="flex size-full items-center justify-center p-2 text-xs text-muted-foreground">
              Preview unavailable
            </span>
          ) : (
            <img
              src={imageUrl(imageId, true)}
              alt={filename}
              loading="lazy"
              onError={() => setFailed(true)}
              className="size-full object-cover"
            />
          )}
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-[min(90vw,1100px)] sm:max-w-[min(90vw,1100px)]">
        <DialogTitle className="truncate pr-8">{filename}</DialogTitle>
        <img
          src={imageUrl(imageId)}
          alt={filename}
          className="max-h-[75vh] w-full rounded-md object-contain"
        />
      </DialogContent>
    </Dialog>
  )
}
