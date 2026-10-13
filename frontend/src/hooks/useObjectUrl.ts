import { useEffect, useState } from 'react'

/** Local preview URL for a picked file, revoked when the file goes away. */
export function useObjectUrl(file: File): string | undefined {
  const [url, setUrl] = useState<string>()

  useEffect(() => {
    const objectUrl = URL.createObjectURL(file)
    // syncing with an external resource; a useMemo URL would be revoked by
    // StrictMode's effect re-run and break the preview
    // eslint-disable-next-line react/set-state-in-effect
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [file])

  return url
}
