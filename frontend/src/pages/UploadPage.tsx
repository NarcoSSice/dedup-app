import { Loader2Icon, UploadIcon } from 'lucide-react'
import { useNavigate } from 'react-router'
import { toast } from 'sonner'

import { ApiErrorAlert } from '@/components/ApiErrorAlert'
import { FilePreviewGrid } from '@/components/FilePreviewGrid'
import { RecentRequests } from '@/components/RecentRequests'
import { UploadDropzone } from '@/components/UploadDropzone'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useRecentRequests } from '@/hooks/useRecentRequests'
import { useSelectedFiles } from '@/hooks/useSelectedFiles'
import { errorMessage } from '@/lib/api-errors'
import { MAX_FILES } from '@/lib/constants'
import { useUploadImagesMutation } from '@/store/api'

export function UploadPage() {
  const { selected, valid, tooMany, addFiles, removeFile, clear } = useSelectedFiles()
  const [uploadImages, { isLoading, error, reset }] = useUploadImagesMutation()
  const { recent } = useRecentRequests()
  const navigate = useNavigate()

  const invalidCount = selected.length - valid.length
  const canUpload = valid.length > 0 && !tooMany && !isLoading

  const upload = async () => {
    try {
      const result = await uploadImages(valid.map((s) => s.file)).unwrap()
      toast.success(`Uploaded: ${result.accepted} accepted, ${result.rejected.length} rejected`)
      clear()
      navigate(`/requests/${result.request_id}`)
    } catch (e) {
      toast.error(errorMessage(e as Parameters<typeof errorMessage>[0]))
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Find duplicate images</CardTitle>
          <CardDescription>
            Uploaded images are compared with each other and with everything uploaded before.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <UploadDropzone
            onFiles={(files) => {
              reset()
              addFiles(files)
            }}
            disabled={isLoading}
          />

          {selected.length > 0 && (
            <>
              <p className="text-sm text-muted-foreground">
                {valid.length} ready to upload
                {invalidCount > 0 && `, ${invalidCount} will be skipped`}
              </p>
              <FilePreviewGrid files={selected} onRemove={removeFile} disabled={isLoading} />
            </>
          )}

          {tooMany && (
            <ApiErrorAlert
              title="Too many files"
              message={`Select at most ${MAX_FILES} images per upload (now ${valid.length}).`}
            />
          )}
          {error && <ApiErrorAlert title="Upload failed" message={errorMessage(error)} />}
        </CardContent>

        {selected.length > 0 && (
          <CardFooter className="justify-end gap-2">
            <Button variant="outline" onClick={clear} disabled={isLoading}>
              Clear
            </Button>
            <Button onClick={upload} disabled={!canUpload}>
              {isLoading ? <Loader2Icon className="animate-spin" /> : <UploadIcon />}
              {isLoading
                ? 'Uploading…'
                : `Upload ${valid.length} image${valid.length === 1 ? '' : 's'}`}
            </Button>
          </CardFooter>
        )}
      </Card>

      <RecentRequests requests={recent} />
    </div>
  )
}
