import { useCallback, useMemo, useState } from 'react'

import { MAX_FILES } from '@/lib/constants'
import { fileKey, validateFile } from '@/lib/files'

export interface SelectedFile {
  key: string
  file: File
  error: string | null
}

export function useSelectedFiles() {
  const [selected, setSelected] = useState<SelectedFile[]>([])

  const addFiles = useCallback((files: File[]) => {
    setSelected((current) => {
      const known = new Set(current.map((s) => s.key))
      const added = files
        .filter((file) => !known.has(fileKey(file)))
        .map((file) => ({ key: fileKey(file), file, error: validateFile(file) }))
      return [...current, ...added]
    })
  }, [])

  const removeFile = useCallback((key: string) => {
    setSelected((current) => current.filter((s) => s.key !== key))
  }, [])

  const clear = useCallback(() => setSelected([]), [])

  const valid = useMemo(() => selected.filter((s) => !s.error), [selected])
  const tooMany = valid.length > MAX_FILES

  return { selected, valid, tooMany, addFiles, removeFile, clear }
}
